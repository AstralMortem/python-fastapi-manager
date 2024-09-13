from tortoise import connections, Tortoise
from fastapi_manager.db.connection import generate_config
from fastapi_manager.conf import settings
import pytest
from fastapi_manager.db import fields
from fastapi_manager.db.migrations.migrate import Migration
from fastapi_manager.db.migrations.operations import CreateModel


@pytest.fixture()
def get_app():
    from fastapi_manager.apps import apps

    apps.populate([])


@pytest.mark.asyncio
@pytest.fixture
async def tortoise_conf(get_app):
    config = generate_config(settings)
    await Tortoise.init(config=config)
    return Tortoise.get_connection("default")


@pytest.mark.asyncio
async def test_operation(tortoise_conf):
    from fastapi_manager.db.migrations.operations import CreateModel
    from fastapi_manager.db.migrations.operations import Operation

    conn = await tortoise_conf
    Operation.schema_generator = conn.schema_generator(conn)

    model = CreateModel("TestModel", {"name": fields.CharField(max_length=100)})

    print(model.to_sql())


@pytest.mark.asyncio
async def test_migrate(tortoise_conf):

    cls = Migration("initial")
    cls.to_upgrade = [
        CreateModel("fastapi", "TestModel", {"name": fields.CharField(max_length=100)})
    ]
    conn = await tortoise_conf
    print(await cls.apply(conn, False))
