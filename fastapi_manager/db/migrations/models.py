from fastapi_manager.db import models, fields

MAX_VERSION_LENGTH = 255
MAX_APP_LENGTH = 100


class MigrationModel(models.Model):
    app = fields.CharField(max_length=MAX_APP_LENGTH)
    version = fields.CharField(max_length=MAX_VERSION_LENGTH)
    applied = fields.DatetimeField(auto_now_add=True)

    class Meta:
        db_table = "migrations"
        app = "fastapi"
