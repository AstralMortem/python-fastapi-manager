from typing import Optional, List, TYPE_CHECKING, Tuple, Type

from fastapi_manager.apps import apps
from tortoise.models import (
    ModelMeta as TortoiseMetaModel,
    MetaInfo as TortoiseMetaInfo,
)

from fastapi_manager.utils.string import convert_to_snake_case


if TYPE_CHECKING:
    from .model import Model


class MetaInfo(TortoiseMetaInfo):
    __slots__ = (
        "abstract",
        "db_table",
        "schema",
        "app",
        "apps",
        "app_label",
        "model_name",
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
        super().__init__(meta)
        self.apps: Optional[object] = getattr(meta, "apps", None)
        self.app_label: Optional[str] = getattr(meta, "app_label", self.app)
        self.model_name: Optional[str] = getattr(meta, "model_name", None)


class ModelMeta(TortoiseMetaModel):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        new_class = super().__new__(mcs, name, bases, attrs)

        parents = [b for b in bases if isinstance(b, ModelMeta)]
        if not parents:
            return new_class

        if hasattr(new_class, "_meta"):
            new_class._meta = MetaInfo(getattr(new_class, "Meta", None))

        module = attrs.get("__module__", None)
        app_config = apps.get_containing_app_config(module)
        app_label = None
        if new_class._meta.app_label is None or new_class._meta.app is None:
            if app_config is None:
                raise RuntimeError(
                    "Model class %s.%s doesn't declare an explicit "
                    "app_label and isn't in an application in "
                    "INSTALLED_APPS." % (module, name)
                )
            else:
                app_label = app_config.label

        new_class._meta.app = app_label
        new_class._meta.app_label = app_label
        new_class._meta.apps = apps
        if new_class._meta.model_name is None:
            new_class._meta.model_name = convert_to_snake_case(name)

        new_class._meta.apps.register_model(app_label, new_class)
        return new_class


# class ModelMeta(TortoiseMetaModel):
#     def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
#         super_new = super().__new__
#         parents = [b for b in bases if isinstance(b, ModelMeta)]
#         attrs["_meta"] = MetaInfo(attrs.get("meta_class"))
#         if not parents:
#             return super_new(mcs, name, bases, attrs)
#         new_class = super_new(mcs, name, bases, attrs)
#         module = attrs.get("__module__")
#
#         app_label = None
#         app_config = apps.get_containing_app_config(module)
#
#         meta = getattr(new_class, "_meta", None)
#
#         if (
#             getattr(meta, "app_label", None) is None
#             or getattr(meta, "app", None) is None
#         ):
#             if app_config is None:
#                 if not getattr(meta, "abstract", None):
#                     raise RuntimeError(
#                         "Model class %s.%s doesn't declare an explicit "
#                         "app_label and isn't in an application in "
#                         "INSTALLED_APPS." % (module, name)
#                     )
#             else:
#                 app_label = app_config.label
#
#         new_class._meta.app = app_label
#         new_class._meta.app_label = app_label
#
#         if not hasattr(meta, "model_name"):
#             new_class._meta.model_name = convert_to_snake_case(name)
#         if not hasattr(meta, "apps"):
#             new_class._meta.apps = apps
#         new_class._meta.apps.register_model(
#             new_class._meta.app_label or new_class._meta.app, new_class
#         )
#         return new_class
