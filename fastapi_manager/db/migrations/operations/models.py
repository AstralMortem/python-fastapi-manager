from .base import Operation, OPType
from fastapi_manager.db.models import Model


class CreateModel(Operation):
    op_type = OPType.ADD

    def __init__(self, app_label, name, fields, options=None):
        super().__init__(app_label, name)

        self.fields = fields
        self.options = options or {}
        self.new_model = None

        self._validate_fields()
        self._validate_options()

        self.create_model()

    def _validate_options(self):
        if "app" not in self.options:
            self.options["app"] = self.app_label
        if "model_name" not in self.options:
            self.options["model_name"] = self.model_name

    def _validate_fields(self):
        if len(list(set(self.fields.keys()))) != len(self.fields.keys()):
            raise ValueError("Fields must have unique names")

    def create_model(self):
        attrs = {}

        for key, val in self.fields.items():
            attrs[key] = val

        meta_class = type("Meta", (), self.options)
        attrs["Meta"] = meta_class

        self.new_model = type(self.model_name, (Model,), attrs)

    def to_sql(self):
        return self.schema_generator._get_table_sql(self.new_model, True)[
            "table_creation_string"
        ].rstrip(";")
