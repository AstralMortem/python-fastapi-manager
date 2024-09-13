from enum import Enum
from tortoise.backends.base.schema_generator import BaseSchemaGenerator
from fastapi_manager.apps import apps


class OPType(Enum):
    ADD = "+"
    REMOVE = "-"
    ALTER = "~"
    RENAME = "^"


class Operation:
    op_type: str
    schema_generator: BaseSchemaGenerator
    model_name: str
    app_label: str

    def __init__(self, app_label, model_name):
        self.app_label = app_label
        self.model_name = model_name

    def _get_app(self):
        return apps.get_app_config(self.app_label)

    def _get_models(self):
        return self._get_app().get_models()

    def _get_model(self):
        return self._get_app().get_model(self.model_name)

    def to_sql(self):
        return ""
