from fastapi_manager.db import models, fields


class TestModel(models.Model):

    test = fields.CharField(max_length=250)
