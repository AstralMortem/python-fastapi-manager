import pytest
from fastapi_manager.apps import apps
from tortoise import Tortoise


@pytest.fixture(autouse=True)
def populate_apps():
    apps.populate([])
