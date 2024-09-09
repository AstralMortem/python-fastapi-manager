from typing import Union, Any
from tortoise.contrib.fastapi import register_tortoise
from importlib.util import find_spec


def register_orm(app, settings):
    config = generate_config(settings)
    register_tortoise(app=app, config=config)


def generate_config(settings):
    return {
        "connections": validate_connections(settings.DATABASES),
        "apps": generate_apps_dict(),
    }


def validate_connections(db_connections: dict[str, Any]):
    connections_dict = {}
    for key, value in db_connections.items():
        if key in connections_dict:
            raise Exception("Duplicate connection name in DATABASES settings")
        if isinstance(value, str):
            connections_dict[key] = value
        elif isinstance(value, dict):
            engine = value.get("engine", None)
            credentials = value.get("credentials", None)
            if not engine:
                raise Exception("Missing 'engine' parameter")
            if not credentials:
                raise Exception("Missing 'credentials' parameter")
            if not isinstance(credentials, dict):
                raise Exception("Credentials must be a dict")
            if not find_spec(engine):
                raise Exception("Incorrect database engine")
            connections_dict[key] = {
                "engine": engine,
                "credentials": dict(credentials),
            }
        else:
            raise Exception("Improperly configured DATABASES settings")
    return connections_dict


def generate_apps_dict():
    apps_dict = {}
    from fastapi_manager.apps import apps

    for app_config in apps.get_app_configs():
        apps_dict[app_config.label] = {
            "models": [f"{app_config.name}.models"],
            "default_connection": "default",
        }

    apps_dict["fastapi"] = {
        "models": ["aerich.models"],
        "default_connection": "default",
    }
    return apps_dict
