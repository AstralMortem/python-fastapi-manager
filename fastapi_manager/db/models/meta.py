import inspect
from copy import copy, deepcopy
from functools import partial
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    TYPE_CHECKING,
)

from pypika import Order, Query, Table
from tortoise.models import (
    prepare_default_ordering,
    get_together,
    _fk_getter,
    _fk_setter,
    _rfk_getter,
    _ro2o_getter,
    _m2m_getter,
    _get_comments,
)


from tortoise import connections
from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.exceptions import (
    ConfigurationError,
)
from tortoise.fields.base import Field
from tortoise.fields.data import IntField
from tortoise.fields.relational import (
    BackwardFKRelation,
    BackwardOneToOneRelation,
    ForeignKeyFieldInstance,
    ManyToManyFieldInstance,
    OneToOneFieldInstance,
)
from tortoise.filters import FilterInfoDict, get_filters_for_field

from tortoise.manager import Manager
from tortoise.queryset import (
    QuerySetSingle,
)


from fastapi_manager.apps import apps
from fastapi_manager.utils.string import convert_to_snake_case


if TYPE_CHECKING:
    from .model import Model


MODEL = TypeVar("MODEL", bound="Model")
EMPTY = object()


class MetaInfo:
    __slots__ = (
        "abstract",
        "db_table",
        "schema",
        "app",
        "model_name",
        "apps",
        "fields",
        "db_fields",
        "m2m_fields",
        "o2o_fields",
        "backward_o2o_fields",
        "fk_fields",
        "backward_fk_fields",
        "fetch_fields",
        "fields_db_projection",
        "_inited",
        "fields_db_projection_reverse",
        "filters",
        "fields_map",
        "default_connection",
        "basequery",
        "basequery_all_fields",
        "basetable",
        "_filters",
        "unique_together",
        "manager",
        "indexes",
        "pk_attr",
        "generated_db_fields",
        "_model",
        "table_description",
        "pk",
        "db_pk_column",
        "db_native_fields",
        "db_default_fields",
        "db_complex_fields",
        "_default_ordering",
        "_ordering_validated",
    )

    def __init__(self, meta: "Model.Meta") -> None:
        self.abstract: bool = getattr(meta, "abstract", False)
        self.manager: Manager = getattr(meta, "manager", Manager())
        self.db_table: str = getattr(meta, "table", "")
        self.schema: Optional[str] = getattr(meta, "schema", None)
        self.app: Optional[str] = getattr(meta, "app", None)
        self.model_name: Optional[str] = getattr(meta, "model_name", None)
        self.apps: Optional[object] = getattr(meta, "apps", None)
        self.unique_together: Tuple[Tuple[str, ...], ...] = get_together(
            meta, "unique_together"
        )
        self.indexes: Tuple[Tuple[str, ...], ...] = get_together(meta, "indexes")
        self._default_ordering: Tuple[Tuple[str, Order], ...] = (
            prepare_default_ordering(meta)
        )
        self._ordering_validated: bool = False
        self.fields: Set[str] = set()
        self.db_fields: Set[str] = set()
        self.m2m_fields: Set[str] = set()
        self.fk_fields: Set[str] = set()
        self.o2o_fields: Set[str] = set()
        self.backward_fk_fields: Set[str] = set()
        self.backward_o2o_fields: Set[str] = set()
        self.fetch_fields: Set[str] = set()
        self.fields_db_projection: Dict[str, str] = {}
        self.fields_db_projection_reverse: Dict[str, str] = {}
        self._filters: Dict[str, FilterInfoDict] = {}
        self.filters: Dict[str, FilterInfoDict] = {}
        self.fields_map: Dict[str, Field] = {}
        self._inited: bool = False
        self.default_connection: Optional[str] = None
        self.basequery: Query = Query()
        self.basequery_all_fields: Query = Query()
        self.basetable: Table = Table("")
        self.pk_attr: str = getattr(meta, "pk_attr", "")
        self.generated_db_fields: Tuple[str, ...] = None  # type: ignore
        self._model: Type["Model"] = None  # type: ignore
        self.table_description: str = getattr(meta, "table_description", "")
        self.pk: Field = None  # type: ignore
        self.db_pk_column: str = ""
        self.db_native_fields: List[Tuple[str, str, Field]] = []
        self.db_default_fields: List[Tuple[str, str, Field]] = []
        self.db_complex_fields: List[Tuple[str, str, Field]] = []

    @property
    def full_name(self) -> str:
        return f"{self.app}.{self._model.__name__}"

    def add_field(self, name: str, value: Field) -> None:
        if name in self.fields_map:
            raise ConfigurationError(f"Field {name} already present in meta")
        value.model = self._model
        self.fields_map[name] = value
        value.model_field_name = name

        if value.has_db_field:
            self.fields_db_projection[name] = value.source_field or name

        if isinstance(value, ManyToManyFieldInstance):
            self.m2m_fields.add(name)
        elif isinstance(value, BackwardOneToOneRelation):
            self.backward_o2o_fields.add(name)
        elif isinstance(value, BackwardFKRelation):
            self.backward_fk_fields.add(name)

        field_filters = get_filters_for_field(
            field_name=name, field=value, source_field=value.source_field or name
        )
        self._filters.update(field_filters)
        self.finalise_fields()

    @property
    def db(self) -> BaseDBAsyncClient:
        if self.default_connection is None:
            raise ConfigurationError(
                f"default_connection for the model {self._model} cannot be None"
            )
        return connections.get(self.default_connection)

    @property
    def ordering(self) -> Tuple[Tuple[str, Order], ...]:
        if not self._ordering_validated:
            unknown_fields = {f for f, _ in self._default_ordering} - self.fields
            raise ConfigurationError(
                f"Unknown fields {','.join(unknown_fields)} in "
                f"default ordering for model {self._model.__name__}"
            )
        return self._default_ordering

    def get_filter(self, key: str) -> FilterInfoDict:
        return self.filters[key]

    def finalise_model(self) -> None:
        """
        Finalise the model after it had been fully loaded.
        """
        self.finalise_fields()
        self._generate_filters()
        self._generate_lazy_fk_m2m_fields()
        self._generate_db_fields()

    def finalise_fields(self) -> None:
        self.db_fields = set(self.fields_db_projection.values())
        self.fields = set(self.fields_map.keys())
        self.fields_db_projection_reverse = {
            value: key for key, value in self.fields_db_projection.items()
        }
        self.fetch_fields = (
            self.m2m_fields
            | self.backward_fk_fields
            | self.fk_fields
            | self.backward_o2o_fields
            | self.o2o_fields
        )

        generated_fields = [
            (field.source_field or field.model_field_name)
            for field in self.fields_map.values()
            if field.generated
        ]
        self.generated_db_fields = tuple(generated_fields)

        self._ordering_validated = True
        for field_name, _ in self._default_ordering:
            if field_name.split("__")[0] not in self.fields:
                self._ordering_validated = False
                break

    def _generate_lazy_fk_m2m_fields(self) -> None:
        # Create lazy FK fields on model.
        for key in self.fk_fields:
            _key = f"_{key}"
            fk_field_object: ForeignKeyFieldInstance = self.fields_map[key]  # type: ignore
            relation_field = fk_field_object.source_field
            to_field = fk_field_object.to_field_instance.model_field_name
            property_kwargs = dict(
                _key=_key,
                relation_field=relation_field,
                to_field=to_field,
            )
            setattr(
                self._model,
                key,
                property(
                    partial(
                        _fk_getter,
                        ftype=fk_field_object.related_model,
                        **property_kwargs,
                    ),
                    partial(
                        _fk_setter,
                        **property_kwargs,
                    ),
                    partial(
                        _fk_setter,
                        value=None,
                        **property_kwargs,
                    ),
                ),
            )

        # Create lazy reverse FK fields on model.
        for key in self.backward_fk_fields:
            _key = f"_{key}"
            backward_fk_field_object: BackwardFKRelation = self.fields_map[key]  # type: ignore
            setattr(
                self._model,
                key,
                property(
                    partial(
                        _rfk_getter,
                        _key=_key,
                        ftype=backward_fk_field_object.related_model,
                        frelfield=backward_fk_field_object.relation_field,
                        from_field=backward_fk_field_object.to_field_instance.model_field_name,
                    )
                ),
            )

        # Create lazy one to one fields on model.
        for key in self.o2o_fields:
            _key = f"_{key}"
            o2o_field_object: OneToOneFieldInstance = self.fields_map[key]  # type: ignore
            relation_field = o2o_field_object.source_field
            to_field = o2o_field_object.to_field_instance.model_field_name
            property_kwargs = dict(
                _key=_key,
                relation_field=relation_field,
                to_field=to_field,
            )
            setattr(
                self._model,
                key,
                property(
                    partial(
                        _fk_getter,
                        ftype=o2o_field_object.related_model,
                        **property_kwargs,
                    ),
                    partial(
                        _fk_setter,
                        **property_kwargs,
                    ),
                    partial(
                        _fk_setter,
                        value=None,
                        **property_kwargs,
                    ),
                ),
            )

        # Create lazy reverse one to one fields on model.
        for key in self.backward_o2o_fields:
            _key = f"_{key}"
            backward_o2o_field_object: BackwardOneToOneRelation = self.fields_map[  # type: ignore
                key
            ]
            setattr(
                self._model,
                key,
                property(
                    partial(
                        _ro2o_getter,
                        _key=_key,
                        ftype=backward_o2o_field_object.related_model,
                        frelfield=backward_o2o_field_object.relation_field,
                        from_field=backward_o2o_field_object.to_field_instance.model_field_name,
                    ),
                ),
            )

        # Create lazy M2M fields on model.
        for key in self.m2m_fields:
            _key = f"_{key}"
            setattr(
                self._model,
                key,
                property(
                    partial(_m2m_getter, _key=_key, field_object=self.fields_map[key])
                ),
            )

    def _generate_db_fields(self) -> None:
        self.db_default_fields.clear()
        self.db_complex_fields.clear()
        self.db_native_fields.clear()

        for key in self.db_fields:
            model_field = self.fields_db_projection_reverse[key]
            field = self.fields_map[model_field]

            is_native_field_type = field.field_type in self.db.executor_class.DB_NATIVE
            default_converter = field.__class__.to_python_value is Field.to_python_value

            if is_native_field_type and (
                default_converter or field.skip_to_python_if_native
            ):
                self.db_native_fields.append((key, model_field, field))
            elif default_converter:
                self.db_default_fields.append((key, model_field, field))
            else:
                self.db_complex_fields.append((key, model_field, field))

    def _generate_filters(self) -> None:
        get_overridden_filter_func = self.db.executor_class.get_overridden_filter_func
        for key, filter_info in self._filters.items():
            overridden_operator = get_overridden_filter_func(
                filter_func=filter_info["operator"]
            )
            if overridden_operator:
                filter_info = copy(filter_info)
                filter_info["operator"] = overridden_operator
            self.filters[key] = filter_info


class ModelMeta(type):
    __slots__ = ()

    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        fields_db_projection: Dict[str, str] = {}
        fields_map: Dict[str, Field] = {}
        filters: Dict[str, FilterInfoDict] = {}
        fk_fields: Set[str] = set()
        m2m_fields: Set[str] = set()
        o2o_fields: Set[str] = set()
        meta_class: "Model.Meta" = attrs.get("Meta", type("Meta", (), {}))
        pk_attr: str = "id"
        module = attrs.get("__module__", None)

        parents = [b for b in bases if isinstance(b, ModelMeta)]

        # Searching for Field attributes in the class hierarchy
        def __search_for_field_attributes(base: Type, attrs: dict) -> None:
            """
            Searching for class attributes of type fields.Field
            in the given class.

            If an attribute of the class is an instance of fields.Field,
            then it will be added to the fields dict. But only, if the
            key is not already in the dict. So derived classes have a higher
            precedence. Multiple Inheritance is supported from left to right.

            After checking the given class, the function will look into
            the classes according to the MRO (method resolution order).

            The MRO is 'natural' order, in which python traverses methods and
            fields. For more information on the magic behind check out:
            `The Python 2.3 Method Resolution Order
            <https://www.python.org/download/releases/2.3/mro/>`_.
            """
            for parent in base.__mro__[1:]:
                __search_for_field_attributes(parent, attrs)
            meta = getattr(base, "_meta", None)
            if meta:
                # For abstract classes
                for key, value in meta.fields_map.items():
                    attrs[key] = value
                # For abstract classes manager
                for key, value in base.__dict__.items():
                    if isinstance(value, Manager) and key not in attrs:
                        attrs[key] = value.__class__()
            else:
                # For mixin classes
                for key, value in base.__dict__.items():
                    if isinstance(value, Field) and key not in attrs:
                        attrs[key] = value

        # Start searching for fields in the base classes.
        inherited_attrs: dict = {}
        for base in bases:
            __search_for_field_attributes(base, inherited_attrs)
        if inherited_attrs:
            # Ensure that the inherited fields are before the defined ones.
            attrs = {**inherited_attrs, **attrs}

        if name != "Model":
            custom_pk_present = False
            for key, value in attrs.items():
                if isinstance(value, Field):
                    if value.pk:
                        if custom_pk_present:
                            raise ConfigurationError(
                                f"Can't create model {name} with two primary keys,"
                                " only single primary key is supported"
                            )
                        if value.generated and not value.allows_generated:
                            raise ConfigurationError(
                                f"Field '{key}' ({value.__class__.__name__}) can't be DB-generated"
                            )
                        custom_pk_present = True
                        pk_attr = key

            if not custom_pk_present and not getattr(meta_class, "abstract", None):
                if "id" not in attrs:
                    attrs = {"id": IntField(primary_key=True), **attrs}

                if not isinstance(attrs["id"], Field) or not attrs["id"].pk:
                    raise ConfigurationError(
                        f"Can't create model {name} without explicit primary key if field 'id'"
                        " already present"
                    )

        for key, value in attrs.items():
            if isinstance(value, Field):
                if getattr(meta_class, "abstract", None):
                    value = deepcopy(value)

                fields_map[key] = value
                value.model_field_name = key

                if isinstance(value, OneToOneFieldInstance):
                    o2o_fields.add(key)
                elif isinstance(value, ForeignKeyFieldInstance):
                    fk_fields.add(key)
                elif isinstance(value, ManyToManyFieldInstance):
                    m2m_fields.add(key)
                else:
                    fields_db_projection[key] = value.source_field or key
                    field, source_field = fields_map[key], fields_db_projection[key]
                    filters.update(
                        get_filters_for_field(
                            field_name=key, field=field, source_field=source_field
                        )
                    )
                    if value.pk:
                        filters.update(
                            get_filters_for_field(
                                field_name="pk", field=field, source_field=source_field
                            )
                        )

        # Clean the class attributes
        for slot in fields_map:
            attrs.pop(slot, None)
        attrs["_meta"] = meta = MetaInfo(meta_class)
        # fastapi_manager init

        app_label = None
        app_config = apps.get_containing_app_config(module)
        if getattr(meta, "app", None) is None and parents:
            if app_config is None:
                if not getattr(meta, "abstract"):
                    raise RuntimeError(
                        "Model class %s.%s doesn't declare an explicit "
                        "app or app_label and isn't in an application in "
                        "INSTALLED_APPS." % (module, name)
                    )
            else:
                app_label = app_config.label

        meta.apps = apps
        meta.model_name = convert_to_snake_case(name)
        meta.app = app_label

        # tortoise init
        meta.fields_map = fields_map
        meta.fields_db_projection = fields_db_projection
        meta._filters = filters
        meta.fk_fields = fk_fields
        meta.backward_fk_fields = set()
        meta.o2o_fields = o2o_fields
        meta.backward_o2o_fields = set()
        meta.m2m_fields = m2m_fields
        meta.default_connection = None
        meta.pk_attr = pk_attr
        meta.pk = fields_map.get(pk_attr)  # type: ignore
        if meta.pk:
            meta.db_pk_column = meta.pk.source_field or meta.pk_attr
        meta._inited = False
        if not fields_map:
            meta.abstract = True

        new_class = super().__new__(mcs, name, bases, attrs)
        for field in meta.fields_map.values():
            field.model = new_class  # type: ignore

        for fname, comment in _get_comments(new_class).items():  # type: ignore
            if fname in fields_map:
                fields_map[fname].docstring = comment
                if fields_map[fname].description is None:
                    fields_map[fname].description = comment.split("\n")[0]

        if new_class.__doc__ and not meta.table_description:
            meta.table_description = inspect.cleandoc(new_class.__doc__).split("\n")[0]
        for key, value in attrs.items():
            if isinstance(value, Manager):
                value._model = new_class
        meta._model = new_class  # type: ignore
        meta.manager._model = new_class
        meta.finalise_fields()

        # Also ensure initialization is only performed for subclasses of Model
        # (excluding Model class itself).
        if not parents:
            return new_class

        new_class._meta.apps.register_model(app_label, new_class)  # type: ignore
        return new_class

    def __getitem__(cls: Type[MODEL], key: Any) -> QuerySetSingle[MODEL]:  # type: ignore
        return cls._getbypk(key)  # type: ignore
