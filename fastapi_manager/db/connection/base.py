from contextlib import asynccontextmanager
from fastapi import FastAPI
from tortoise import Tortoise, ConfigurationError, expand_db_url
from tortoise.contrib.fastapi import RegisterTortoise
from tortoise.log import logger
from tortoise.connection import connections
from fastapi_manager.apps import apps
from fastapi_manager.conf import settings


class DBConnector(Tortoise):

    @classmethod
    async def init(
        cls,
        _create_db: bool = False,
        **kwargs,
    ) -> None:

        if cls._inited:
            await connections.close_all(discard=True)

        connections_config = {}
        for conf_key, conf_val in settings.DATABASES.items():
            if isinstance(conf_val, str):
                connections_config[conf_key] = expand_db_url(conf_val)
            elif isinstance(conf_val, dict):
                connections_config[conf_key] = conf_val
            else:
                raise ConfigurationError("Config must be str or dict")

        timezone = settings.TIMEZONE
        use_tz = bool(timezone)

        # Mask passwords in logs output
        passwords = []
        for name, info in connections_config.items():
            if isinstance(info, str):
                info = expand_db_url(info)
            password = info.get("credentials", {}).get("password")
            if password:
                passwords.append(password)

        str_connection_config = str(connections_config)
        for password in passwords:
            str_connection_config = str_connection_config.replace(
                password,
                # Show one third of the password at beginning (may be better for debugging purposes)
                f"{password[0:len(password) // 3]}***",
            )

        logger.debug(
            "Tortoise-ORM startup\n    connections: %s\n    apps: %s",
            str_connection_config,
            str(cls.apps.values()),
        )

        cls._init_timezone(use_tz, timezone)
        await connections._init(connections_config, _create_db)
        cls._init_apps()
        cls._inited = True

    @classmethod
    def _init_apps(cls, *args) -> None:
        for app_config in apps.get_app_configs():
            cls.apps[app_config.label] = app_config.models

            for model in app_config.get_models():
                model._meta.default_connection = "default"

        cls._init_relations()
        cls._build_initial_querysets()


class RegisterORM(RegisterTortoise):

    async def init_orm(self) -> None:  # pylint: disable=W0612
        await DBConnector.init(
            _create_db=self._create_db,
        )
        logger.info(
            "Tortoise-ORM started, %s, %s", connections._get_storage(), DBConnector.apps
        )
        if self.generate_schemas:
            logger.info("Tortoise-ORM generating schema")
            await DBConnector.generate_schemas()

    @staticmethod
    async def close_orm() -> None:  # pylint: disable=W0612
        await connections.close_all()
        logger.info("Tortoise-ORM shutdown")


@asynccontextmanager
async def register_orm(app: FastAPI):

    orm = RegisterORM(app, generate_schemas=False)
    await orm.init_orm()
    yield
    await orm.close_orm()
