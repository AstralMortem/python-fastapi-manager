from .meta import ModelMeta
from tortoise.models import Model as TortoiseModel
from fastapi_manager.db import fields


class Model(TortoiseModel, metaclass=ModelMeta):
    id = fields.IntField(pk=True, generated=True)

    class Meta:
        abstract = True
