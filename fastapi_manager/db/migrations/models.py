from fastapi_manager.db import fields, models


class FastapiMigrations(models.Model):

    app = fields.CharField(max_length=50)
    name = fields.TextField()
    applied = fields.DatetimeField(auto_now_add=True)

    class Meta:
        db_table = "fastapi_migrations"
