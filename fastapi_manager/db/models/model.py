import asyncio
import inspect
from copy import copy, deepcopy
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)


from pypika.terms import Term
from typing_extensions import Self
from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.exceptions import (
    ConfigurationError,
    DoesNotExist,
    IncompleteInstanceError,
    IntegrityError,
    ObjectDoesNotExistError,
    OperationalError,
    ParamsError,
)
from tortoise.fields.base import Field
from tortoise.fields.relational import ManyToManyFieldInstance
from tortoise.functions import Function
from tortoise.indexes import Index
from tortoise.queryset import (
    BulkCreateQuery,
    BulkUpdateQuery,
    ExistsQuery,
    Q,
    QuerySet,
    QuerySetSingle,
    RawSQLQuery,
)
from tortoise.router import router
from tortoise.signals import Signals
from tortoise.transactions import in_transaction


from .meta import ModelMeta, MetaInfo, MODEL, EMPTY


class Model(metaclass=ModelMeta):
    """
    Base class for all Tortoise ORM Models.
    """

    # I don' like this here, but it makes auto completion and static analysis much happier
    _meta = MetaInfo(None)  # type: ignore
    _listeners: Dict[Signals, Dict[Type[MODEL], List[Callable]]] = {  # type: ignore
        Signals.pre_save: {},
        Signals.post_save: {},
        Signals.pre_delete: {},
        Signals.post_delete: {},
    }

    def __init__(self, **kwargs: Any) -> None:
        # self._meta is a very common attribute lookup, lets cache it.
        meta = self._meta
        self._partial = False
        self._saved_in_db = False
        self._custom_generated_pk = False
        self._await_when_save: Dict[str, Callable[[], Awaitable[Any]]] = {}

        # Assign defaults for missing fields
        for key in meta.fields.difference(self._set_kwargs(kwargs)):
            field_object = meta.fields_map[key]
            field_default = field_object.default
            if inspect.iscoroutinefunction(field_default):
                self._await_when_save[key] = field_default
            elif callable(field_default):
                setattr(self, key, field_default())
            else:
                setattr(self, key, deepcopy(field_object.default))

    def __setattr__(self, key, value):
        # set field value override async default function
        if hasattr(self, "_await_when_save"):
            self._await_when_save.pop(key, None)
        super().__setattr__(key, value)

    def _set_kwargs(self, kwargs: dict) -> Set[str]:
        meta = self._meta

        # Assign values and do type conversions
        passed_fields = {*kwargs.keys()} | meta.fetch_fields

        for key, value in kwargs.items():
            if key in meta.fk_fields or key in meta.o2o_fields:
                if value and not value._saved_in_db:
                    raise OperationalError(
                        f"You should first call .save() on {value} before referring to it"
                    )
                setattr(self, key, value)
                passed_fields.add(meta.fields_map[key].source_field)
            elif key in meta.fields_db_projection:
                field_object = meta.fields_map[key]
                if field_object.pk and field_object.generated:
                    self._custom_generated_pk = True
                if value is None and not field_object.null:
                    raise ValueError(
                        f"{key} is non nullable field, but null was passed"
                    )
                setattr(self, key, field_object.to_python_value(value))
            elif key in meta.backward_fk_fields:
                raise ConfigurationError(
                    "You can't set backward relations through init, change related model instead"
                )
            elif key in meta.backward_o2o_fields:
                raise ConfigurationError(
                    "You can't set backward one to one relations through init,"
                    " change related model instead"
                )
            elif key in meta.m2m_fields:
                raise ConfigurationError(
                    "You can't set m2m relations through init, use m2m_manager instead"
                )

        return passed_fields

    @classmethod
    def _init_from_db(cls: Type[MODEL], **kwargs: Any) -> MODEL:
        self = cls.__new__(cls)
        self._partial = False
        self._saved_in_db = True
        self._custom_generated_pk = (
            self._meta.db_pk_column not in self._meta.generated_db_fields
        )
        self._await_when_save = {}

        meta = self._meta
        inited_keys: Set[str] = set()
        try:
            # This is like so for performance reasons.
            #  We want to avoid conditionals and calling .to_python_value()
            # Native fields are fields that are already converted to/from python to DB type
            #  by the DB driver
            for key, model_field, field in meta.db_native_fields:
                setattr(self, model_field, kwargs[key])
                inited_keys.add(key)
            # Fields that don't override .to_python_value() are converted without a call
            #  as we already know what we will be doing.
            for key, model_field, field in meta.db_default_fields:
                if (value := kwargs[key]) is not None:
                    value = field.field_type(value)
                setattr(self, model_field, value)
                inited_keys.add(key)
            # These fields need manual .to_python_value()
            for key, model_field, field in meta.db_complex_fields:
                setattr(self, model_field, field.to_python_value(kwargs[key]))
                inited_keys.add(key)
        except KeyError:
            self._partial = True
            native_fields: List[Field] = [f for *_, f in meta.db_native_fields]
            default_fields = complex_fields = None
            for key, value in kwargs.items():
                if key in inited_keys or key not in meta.fields_map:
                    continue
                if (field := meta.fields_map[key]) not in native_fields:
                    if default_fields is None:
                        default_fields = [f for *_, f in meta.db_default_fields]
                    if field in default_fields:
                        if value is not None:
                            value = field.field_type(value)
                    else:
                        if complex_fields is None:
                            complex_fields = [f for *_, f in meta.db_complex_fields]
                        value = field.to_python_value(value)
                setattr(self, key, value)

        return self

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}>"

    def __repr__(self) -> str:
        if self.pk:
            return f"<{self.__class__.__name__}: {self.pk}>"
        return f"<{self.__class__.__name__}>"

    def __hash__(self) -> int:
        if not self.pk:
            raise TypeError("Model instances without id are unhashable")
        return hash(self.pk)

    def __iter__(self):
        for field in self._meta.db_fields:
            yield field, getattr(self, field)

    def __eq__(self, other: object) -> bool:
        return type(other) is type(self) and self.pk == other.pk  # type: ignore

    def _get_pk_val(self) -> Any:
        return getattr(self, self._meta.pk_attr)

    def _set_pk_val(self, value: Any) -> None:
        setattr(self, self._meta.pk_attr, value)

    pk = property(_get_pk_val, _set_pk_val)
    """
    Alias to the models Primary Key.
    Can be used as a field name when doing filtering e.g. ``.filter(pk=...)`` etc...
    """

    @classmethod
    async def _getbypk(cls: Type[MODEL], key: Any) -> MODEL:
        try:
            return await cls.get(pk=key)
        except (DoesNotExist, ValueError):
            raise ObjectDoesNotExistError(cls, cls._meta.pk_attr, key)

    def clone(self: MODEL, pk: Any = EMPTY) -> MODEL:
        """
        Create a new clone of the object that when you do a ``.save()`` will create a new record.

        :param pk: An optionally required value if the model doesn't generate its own primary key.
            Any value you specify here will always be used.
        :return: A copy of the current object without primary key information.
        :raises ParamsError: If pk is required but not provided.
        """
        obj = copy(self)
        if pk is EMPTY:
            pk_field: Field = self._meta.pk
            if pk_field.generated is False and pk_field.default is None:
                raise ParamsError(
                    f"{self._meta.full_name} requires explicit primary key. Please use .clone(pk=<value>)"
                )
            else:
                obj.pk = None
        else:
            obj.pk = pk
        obj._saved_in_db = False
        return obj

    def update_from_dict(self: MODEL, data: dict) -> MODEL:
        """
        Updates the current model with the provided dict.
        This can allow mass-updating a model from a dict, also ensuring that datatype conversions happen.

        This will ignore any extra fields, and NOT update the model with them,
        but will raise errors on bad types or updating Many-instance relations.

        :param data: The parameters you want to update in a dict format
        :return: The current model instance

        :raises ConfigurationError: When attempting to update a remote instance
            (e.g. a reverse ForeignKey or ManyToMany relation)
        :raises ValueError: When a passed parameter is not type compatible
        """
        self._set_kwargs(data)
        return self

    @classmethod
    def register_listener(cls, signal: Signals, listener: Callable):
        """
        Register listener to current model class for special Signal.

        :param signal: one of tortoise.signals.Signals
        :param listener: callable listener

        :raises ConfigurationError: When listener is not callable
        """
        if not callable(listener):
            raise ConfigurationError("Signal listener must be callable!")
        cls_listeners = cls._listeners.get(signal).setdefault(cls, [])  # type:ignore
        if listener not in cls_listeners:
            cls_listeners.append(listener)

    async def _set_async_default_field(self) -> None:
        """retrieve value from field's async default value"""
        if hasattr(self, "_await_when_save"):
            for k, v in self._await_when_save.copy().items():
                setattr(self, k, await v())
            self._await_when_save = {}

    async def _wait_for_listeners(self, signal: Signals, *listener_args) -> None:
        cls_listeners = self._listeners.get(signal, {}).get(self.__class__, [])
        listeners = [
            listener(self.__class__, self, *listener_args) for listener in cls_listeners
        ]
        await asyncio.gather(*listeners)

    async def _pre_delete(self, using_db: Optional[BaseDBAsyncClient] = None) -> None:
        await self._wait_for_listeners(Signals.pre_delete, using_db)

    async def _post_delete(self, using_db: Optional[BaseDBAsyncClient] = None) -> None:
        await self._wait_for_listeners(Signals.post_delete, using_db)

    async def _pre_save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        update_fields: Optional[Iterable[str]] = None,
    ) -> None:
        await self._wait_for_listeners(Signals.pre_save, using_db, update_fields)

    async def _post_save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        created: bool = False,
        update_fields: Optional[Iterable[str]] = None,
    ) -> None:
        await self._wait_for_listeners(
            Signals.post_save, created, using_db, update_fields
        )

    async def save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        update_fields: Optional[Iterable[str]] = None,
        force_create: bool = False,
        force_update: bool = False,
    ) -> None:
        """
        Creates/Updates the current model object.

        :param update_fields: If provided, it should be a tuple/list of fields by name.

            This is the subset of fields that should be updated.
            If the object needs to be created ``update_fields`` will be ignored.
        :param using_db: Specific DB connection to use instead of default bound
        :param force_create: Forces creation of the record
        :param force_update: Forces updating of the record

        :raises IncompleteInstanceError: If the model is partial and the fields are not available for persistence.
        :raises IntegrityError: If the model can't be created or updated (specifically if force_create or force_update has been set)
        """
        await self._set_async_default_field()
        db = using_db or self._choose_db(True)
        executor = db.executor_class(model=self.__class__, db=db)
        if self._partial:
            if update_fields:
                for field in update_fields:
                    if not hasattr(self, self._meta.pk_attr):
                        raise IncompleteInstanceError(
                            f"{self.__class__.__name__} is a partial model without primary key fetchd. Partial update not available"
                        )
                    if not hasattr(self, field):
                        raise IncompleteInstanceError(
                            f"{self.__class__.__name__} is a partial model, field '{field}' is not available"
                        )
            else:
                raise IncompleteInstanceError(
                    f"{self.__class__.__name__} is a partial model, can only be saved with the relevant update_field provided"
                )
        await self._pre_save(db, update_fields)

        if force_create:
            await executor.execute_insert(self)
            created = True
        elif force_update:
            rows = await executor.execute_update(self, update_fields)
            if rows == 0:
                raise IntegrityError(
                    f"Can't update object that doesn't exist. PK: {self.pk}"
                )
            created = False
        else:
            if self._saved_in_db or update_fields:
                if self.pk is None:
                    await executor.execute_insert(self)
                    created = True
                else:
                    await executor.execute_update(self, update_fields)
                    created = False
            else:
                # TODO: Do a merge/upsert operation here instead. Let the executor determine an optimal strategy for each DB engine.
                await executor.execute_insert(self)
                created = True

        self._saved_in_db = True
        await self._post_save(db, created, update_fields)

    async def delete(self, using_db: Optional[BaseDBAsyncClient] = None) -> None:
        """
        Deletes the current model object.

        :param using_db: Specific DB connection to use instead of default bound

        :raises OperationalError: If object has never been persisted.
        """
        db = using_db or self._choose_db(True)
        if not self._saved_in_db:
            raise OperationalError("Can't delete unpersisted record")
        await self._pre_delete(db)
        await db.executor_class(model=self.__class__, db=db).execute_delete(self)
        await self._post_delete(db)

    async def fetch_related(
        self, *args: Any, using_db: Optional[BaseDBAsyncClient] = None
    ) -> None:
        """
        Fetch related fields.

        .. code-block:: python3

            User.fetch_related("emails", "manager")

        :param args: The related fields that should be fetched.
        :param using_db: Specific DB connection to use instead of default bound
        """
        db = using_db or self._choose_db()
        await db.executor_class(model=self.__class__, db=db).fetch_for_list(
            [self], *args
        )

    async def refresh_from_db(
        self,
        fields: Optional[Iterable[str]] = None,
        using_db: Optional[BaseDBAsyncClient] = None,
    ) -> None:
        """
        Refresh latest data from db. When this method is called without arguments
        all db fields of the model are updated to the values currently present in the database.

        .. code-block:: python3

            user.refresh_from_db(fields=['name'])

        :param fields: The special fields that to be refreshed.
        :param using_db: Specific DB connection to use instead of default bound.

        :raises OperationalError: If object has never been persisted.
        """
        if not self._saved_in_db:
            raise OperationalError("Can't refresh unpersisted record")
        db = using_db or self._choose_db()
        qs = QuerySet(self.__class__).using_db(db).only(*(fields or []))
        obj = await qs.get(pk=self.pk)

        for field in fields or self._meta.db_fields:
            setattr(self, field, getattr(obj, field, None))

    @classmethod
    def _choose_db(cls, for_write: bool = False):
        """
        Return the connection that will be used if this query is executed now.

        :param for_write: Whether this query for write.
        :return: BaseDBAsyncClient:
        """
        if for_write:
            db = router.db_for_write(cls)
        else:
            db = router.db_for_read(cls)
        return db or cls._meta.db

    @classmethod
    async def get_or_create(
        cls,
        defaults: Optional[dict] = None,
        using_db: Optional[BaseDBAsyncClient] = None,
        **kwargs: Any,
    ) -> Tuple[Self, bool]:
        """
        Fetches the object if exists (filtering on the provided parameters),
        else creates an instance with any unspecified parameters as default values.

        :param defaults: Default values to be added to a created instance if it can't be fetched.
        :param using_db: Specific DB connection to use instead of default bound
        :param kwargs: Query parameters.
        :raises IntegrityError: If create failed
        :raises TransactionManagementError: If transaction error
        :raises ParamsError: If defaults conflict with kwargs
        """
        if not defaults:
            defaults = {}
        db = using_db or cls._choose_db(True)
        try:
            return await cls.filter(**kwargs).using_db(db).get(), False
        except DoesNotExist:
            return await cls._create_or_get(db, defaults, **kwargs)

    @classmethod
    async def _create_or_get(
        cls, db: BaseDBAsyncClient, defaults: dict, **kwargs
    ) -> Tuple[Self, bool]:
        """Try to create, if fails with IntegrityError then try to get"""
        for key in defaults.keys() & kwargs.keys():
            if (default_value := defaults[key]) != (query_value := kwargs[key]):
                raise ParamsError(
                    f"Conflict value with {key=}: {default_value=} vs {query_value=}"
                )
        merged_defaults = {**kwargs, **defaults}
        try:
            async with in_transaction(connection_name=db.connection_name) as connection:
                return await cls.create(using_db=connection, **merged_defaults), True
        except IntegrityError as exc:
            try:
                return await cls.filter(**kwargs).using_db(db).get(), False
            except DoesNotExist:
                pass
            raise exc

    @classmethod
    def _db_queryset(
        cls, using_db: Optional[BaseDBAsyncClient] = None, for_write: bool = False
    ) -> QuerySet[Self]:
        db = using_db or cls._choose_db(for_write)
        return cls._meta.manager.get_queryset().using_db(db)

    @classmethod
    def select_for_update(
        cls,
        nowait: bool = False,
        skip_locked: bool = False,
        of: Tuple[str, ...] = (),
        using_db: Optional[BaseDBAsyncClient] = None,
    ) -> QuerySet[Self]:
        """
        Make QuerySet select for update.

        Returns a queryset that will lock rows until the end of the transaction,
        generating a SELECT ... FOR UPDATE SQL statement on supported databases.
        """
        return cls._db_queryset(using_db, for_write=True).select_for_update(
            nowait, skip_locked, of
        )

    @classmethod
    async def update_or_create(
        cls: Type[MODEL],
        defaults: Optional[dict] = None,
        using_db: Optional[BaseDBAsyncClient] = None,
        **kwargs: Any,
    ) -> Tuple[MODEL, bool]:
        """
        A convenience method for updating an object with the given kwargs, creating a new one if necessary.

        :param defaults: Default values used to update the object.
        :param using_db: Specific DB connection to use instead of default bound
        :param kwargs: Query parameters.
        """
        if not defaults:
            defaults = {}
        db = using_db or cls._choose_db(True)
        async with in_transaction(connection_name=db.connection_name) as connection:
            instance = (
                await cls.select_for_update().using_db(connection).get_or_none(**kwargs)
            )
            if instance:
                await instance.update_from_dict(defaults).save(using_db=connection)
                return instance, False
        return await cls._create_or_get(db, defaults, **kwargs)

    @classmethod
    async def create(
        cls: Type[MODEL], using_db: Optional[BaseDBAsyncClient] = None, **kwargs: Any
    ) -> MODEL:
        """
        Create a record in the DB and returns the object.

        .. code-block:: python3

            user = await User.create(name="...", email="...")

        Equivalent to:

        .. code-block:: python3

            user = User(name="...", email="...")
            await user.save()

        :param using_db: Specific DB connection to use instead of default bound
        :param kwargs: Model parameters.
        """
        instance = cls(**kwargs)
        instance._saved_in_db = False
        db = using_db or cls._choose_db(True)
        await instance.save(using_db=db, force_create=True)
        return instance

    @classmethod
    def bulk_update(
        cls: Type[MODEL],
        objects: Iterable[MODEL],
        fields: Iterable[str],
        batch_size: Optional[int] = None,
        using_db: Optional[BaseDBAsyncClient] = None,
    ) -> "BulkUpdateQuery[MODEL]":
        """
        Update the given fields in each of the given objects in the database.
        This method efficiently updates the given fields on the provided model instances, generally with one query.

        .. code-block:: python3

            users = [
                await User.create(name="...", email="..."),
                await User.create(name="...", email="...")
            ]
            users[0].name = 'name1'
            users[1].name = 'name2'

            await User.bulk_update(users, fields=['name'])

        :param objects: List of objects to bulk create
        :param fields: The fields to update
        :param batch_size: How many objects are created in a single query
        :param using_db: Specific DB connection to use instead of default bound
        """
        return cls._db_queryset(using_db, for_write=True).bulk_update(
            objects, fields, batch_size
        )

    @classmethod
    async def in_bulk(
        cls: Type[MODEL],
        id_list: Iterable[Union[str, int]],
        field_name: str = "pk",
        using_db: Optional[BaseDBAsyncClient] = None,
    ) -> Dict[str, MODEL]:
        """
        Return a dictionary mapping each of the given IDs to the object with
        that ID. If `id_list` isn't provided, evaluate the entire QuerySet.

        :param id_list: A list of field values
        :param field_name: Must be a unique field
        :param using_db: Specific DB connection to use instead of default bound
        """
        return await cls._db_queryset(using_db).in_bulk(id_list, field_name)

    @classmethod
    def bulk_create(
        cls: Type[MODEL],
        objects: Iterable[MODEL],
        batch_size: Optional[int] = None,
        ignore_conflicts: bool = False,
        update_fields: Optional[Iterable[str]] = None,
        on_conflict: Optional[Iterable[str]] = None,
        using_db: Optional[BaseDBAsyncClient] = None,
    ) -> "BulkCreateQuery[MODEL]":
        """
        Bulk insert operation:

        .. note::
            The bulk insert operation will do the minimum to ensure that the object
            created in the DB has all the defaults and generated fields set,
            but may be incomplete reference in Python.

            e.g. ``IntField`` primary keys will not be populated.

        This is recommended only for throw away inserts where you want to ensure optimal
        insert performance.

        .. code-block:: python3

            User.bulk_create([
                User(name="...", email="..."),
                User(name="...", email="...")
            ])

        :param on_conflict: On conflict index name
        :param update_fields: Update fields when conflicts
        :param ignore_conflicts: Ignore conflicts when inserting
        :param objects: List of objects to bulk create
        :param batch_size: How many objects are created in a single query
        :param using_db: Specific DB connection to use instead of default bound
        """
        return cls._db_queryset(using_db, for_write=True).bulk_create(
            objects, batch_size, ignore_conflicts, update_fields, on_conflict
        )

    @classmethod
    def first(
        cls, using_db: Optional[BaseDBAsyncClient] = None
    ) -> QuerySetSingle[Optional[Self]]:
        """
        Generates a QuerySet that returns the first record.
        """
        return cls._db_queryset(using_db).first()

    @classmethod
    def filter(cls, *args: Q, **kwargs: Any) -> QuerySet[Self]:
        """
        Generates a QuerySet with the filter applied.

        :param args: Q functions containing constraints. Will be AND'ed.
        :param kwargs: Simple filter constraints.
        """
        return cls._meta.manager.get_queryset().filter(*args, **kwargs)

    @classmethod
    def exclude(cls, *args: Q, **kwargs: Any) -> QuerySet[Self]:
        """
        Generates a QuerySet with the exclude applied.

        :param args: Q functions containing constraints. Will be AND'ed.
        :param kwargs: Simple filter constraints.
        """
        return cls._meta.manager.get_queryset().exclude(*args, **kwargs)

    @classmethod
    def annotate(cls, **kwargs: Union[Function, Term]) -> QuerySet[Self]:
        """
        Annotates the result set with extra Functions/Aggregations/Expressions.

        :param kwargs: Parameter name and the Function/Aggregation to annotate with.
        """
        return cls._meta.manager.get_queryset().annotate(**kwargs)

    @classmethod
    def all(cls, using_db: Optional[BaseDBAsyncClient] = None) -> QuerySet[Self]:
        """
        Returns the complete QuerySet.
        """
        return cls._db_queryset(using_db)

    @classmethod
    def get(
        cls, *args: Q, using_db: Optional[BaseDBAsyncClient] = None, **kwargs: Any
    ) -> QuerySetSingle[Self]:
        """
        Fetches a single record for a Model type using the provided filter parameters.

        .. code-block:: python3

            user = await User.get(username="foo")

        :param using_db: The DB connection to use
        :param args: Q functions containing constraints. Will be AND'ed.
        :param kwargs: Simple filter constraints.

        :raises MultipleObjectsReturned: If provided search returned more than one object.
        :raises DoesNotExist: If object can not be found.
        """
        return cls._db_queryset(using_db).get(*args, **kwargs)

    @classmethod
    def raw(
        cls, sql: str, using_db: Optional[BaseDBAsyncClient] = None
    ) -> "RawSQLQuery":
        """
        Executes a RAW SQL and returns the result

        .. code-block:: python3

            result = await User.raw("select * from users where name like '%test%'")

        :param using_db: The specific DB connection to use
        :param sql: The raw sql.
        """
        return cls._db_queryset(using_db).raw(sql)

    @classmethod
    def exists(
        cls: Type[MODEL],
        *args: Q,
        using_db: Optional[BaseDBAsyncClient] = None,
        **kwargs: Any,
    ) -> ExistsQuery:
        """
        Return True/False whether record exists with the provided filter parameters.

        .. code-block:: python3

            result = await User.exists(username="foo")

        :param using_db: The specific DB connection to use.
        :param args: Q functions containing constraints. Will be AND'ed.
        :param kwargs: Simple filter constraints.
        """
        return cls._db_queryset(using_db).filter(*args, **kwargs).exists()

    @classmethod
    def get_or_none(
        cls, *args: Q, using_db: Optional[BaseDBAsyncClient] = None, **kwargs: Any
    ) -> QuerySetSingle[Optional[Self]]:
        """
        Fetches a single record for a Model type using the provided filter parameters or None.

        .. code-block:: python3

            user = await User.get_or_none(username="foo")

        :param using_db: The specific DB connection to use.
        :param args: Q functions containing constraints. Will be AND'ed.
        :param kwargs: Simple filter constraints.
        """
        return cls._db_queryset(using_db).get_or_none(*args, **kwargs)

    @classmethod
    async def fetch_for_list(
        cls,
        instance_list: "Iterable[Model]",
        *args: Any,
        using_db: Optional[BaseDBAsyncClient] = None,
    ) -> None:
        """
        Fetches related models for provided list of Model objects.

        :param instance_list: List of Model objects to fetch relations for.
        :param args: Relation names to fetch.
        :param using_db: DO NOT USE
        """
        db = using_db or cls._choose_db()
        await db.executor_class(model=cls, db=db).fetch_for_list(instance_list, *args)

    @classmethod
    def _check(cls) -> None:
        """
        Calls various checks to validate the model.

        :raises ConfigurationError: If the model has not been configured correctly.
        """
        cls._check_together("unique_together")
        cls._check_together("indexes")

    @classmethod
    def _check_together(cls, together: str) -> None:
        """
        Check the value of "unique_together" option.

        :raises ConfigurationError: If the model has not been configured correctly.
        """
        _together = getattr(cls._meta, together)
        if not isinstance(_together, (tuple, list)):
            raise ConfigurationError(
                f"'{cls.__name__}.{together}' must be a list or tuple."
            )

        if any(
            not isinstance(unique_fields, (tuple, list, Index))
            for unique_fields in _together
        ):
            raise ConfigurationError(
                f"All '{cls.__name__}.{together}' elements must be lists or tuples."
            )

        for fields_tuple in _together:
            if isinstance(fields_tuple, Index):
                fields_tuple = fields_tuple.fields
            for field_name in fields_tuple:
                field = cls._meta.fields_map.get(field_name)

                if not field:
                    raise ConfigurationError(
                        f"'{cls.__name__}.{together}' has no '{field_name}' field."
                    )

                if isinstance(field, ManyToManyFieldInstance):
                    raise ConfigurationError(
                        f"'{cls.__name__}.{together}' '{field_name}' field refers"
                        " to ManyToMany field."
                    )

    @classmethod
    def describe(cls, serializable: bool = True) -> dict:
        """
        Describes the given list of models or ALL registered models.

        :param serializable:
            ``False`` if you want raw python objects,
            ``True`` for JSON-serializable data. (Defaults to ``True``)

        :return:
            A dictionary containing the model description.

            The base dict has a fixed set of keys that reference a list of fields
            (or a single field in the case of the primary key):

            .. code-block:: python3

                {
                    "name":                 str     # Qualified model name
                    "app":                  str     # 'App' namespace
                    "table":                str     # DB table name
                    "abstract":             bool    # Is the model Abstract?
                    "description":          str     # Description of table (nullable)
                    "docstring":            str     # Model docstring (nullable)
                    "unique_together":      [...]   # List of List containing field names that
                                                    #  are unique together
                    "pk_field":             {...}   # Primary key field
                    "data_fields":          [...]   # Data fields
                    "fk_fields":            [...]   # Foreign Key fields FROM this model
                    "backward_fk_fields":   [...]   # Foreign Key fields TO this model
                    "o2o_fields":           [...]   # OneToOne fields FROM this model
                    "backward_o2o_fields":  [...]   # OneToOne fields TO this model
                    "m2m_fields":           [...]   # Many-to-Many fields
                }

            Each field is specified as defined in :meth:`tortoise.fields.base.Field.describe`
        """
        return {
            "name": cls._meta.full_name,
            "app": cls._meta.app,
            "table": cls._meta.db_table,
            "abstract": cls._meta.abstract,
            "description": cls._meta.table_description or None,
            "docstring": inspect.cleandoc(cls.__doc__ or "") or None,
            "unique_together": cls._meta.unique_together or [],
            "indexes": cls._meta.indexes or [],
            "pk_field": cls._meta.fields_map[cls._meta.pk_attr].describe(serializable),
            "data_fields": [
                field.describe(serializable)
                for name, field in cls._meta.fields_map.items()
                if name != cls._meta.pk_attr
                and name in (cls._meta.fields - cls._meta.fetch_fields)
            ],
            "fk_fields": [
                field.describe(serializable)
                for name, field in cls._meta.fields_map.items()
                if name in cls._meta.fk_fields
            ],
            "backward_fk_fields": [
                field.describe(serializable)
                for name, field in cls._meta.fields_map.items()
                if name in cls._meta.backward_fk_fields
            ],
            "o2o_fields": [
                field.describe(serializable)
                for name, field in cls._meta.fields_map.items()
                if name in cls._meta.o2o_fields
            ],
            "backward_o2o_fields": [
                field.describe(serializable)
                for name, field in cls._meta.fields_map.items()
                if name in cls._meta.backward_o2o_fields
            ],
            "m2m_fields": [
                field.describe(serializable)
                for name, field in cls._meta.fields_map.items()
                if name in cls._meta.m2m_fields
            ],
        }

    def __await__(self: MODEL) -> Generator[Any, None, MODEL]:
        async def _self() -> MODEL:
            return self

        return _self().__await__()

    class Meta:
        """
        The ``Meta`` class is used to configure metadata for the Model.

        Usage:

        .. code-block:: python3

            class Foo(Model):
                ...

                class Meta:
                    table="custom_table"
                    unique_together=(("field_a", "field_b"), )
        """
