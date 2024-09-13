import asyncio

from .base import BaseCommand
from fastapi_manager.db.migrations import Command
from fastapi_manager.db.connection import generate_config
from fastapi_manager.conf import settings
from tortoise import run_async


class MakeMigrations(BaseCommand):
    name = "makemigrations"

    def execute(self, message: str = "Update", app: str = None):
        command = Command(generate_config(settings))
        asyncio.run(command.makemigrations(message, app))


#
# class BaseMigrationCommand(BaseCommand):
#     MIGRATIONS_PATH = (
#         Path(settings.BASE_DIR).joinpath("migrations").absolute().resolve()
#     )
#
#     async def _check_is_init(self, command):
#         path = self.MIGRATIONS_PATH.joinpath(command.app)
#         if not path.exists() or len(list(path.iterdir())) == 0:
#             await command.init_db(True)
#             return True
#         return False
#
#
# class MakeMigrations(BaseMigrationCommand):
#     name = "makemigrations"
#
#     async def _app_make_migrations(self, config, message, app):
#         command = Command(config, app, str(self.MIGRATIONS_PATH))
#
#         is_init = await self._check_is_init(command)
#         if is_init:
#             message = f"initial"
#         await command.init()
#         await command.migrate(message)
#
#     async def _async_execute(self, message, app):
#         config = generate_config(settings)
#         if app is not None:
#             await self._app_make_migrations(config, message, app)
#         else:
#             apps = config["apps"]
#             for app in apps.keys():
#                 await self._app_make_migrations(config, message, app)
#
#         print(config)
#
#     def execute(self, message: str = "update", app: str = None):
#         run_async(self._async_execute(message, app))
#
#
# class Migrate(BaseMigrationCommand):
#     name = "migrate"
#
#     async def _app_migrate(self, config, app):
#         command = Command(config, app, str(self.MIGRATIONS_PATH))
#         await self._check_is_init(command, app)
#         await command.upgrade(True)
#
#     async def _async_execute(self, app):
#         config = generate_config(settings)
#         if app is not None:
#             await self._app_migrate(config, app)
#         else:
#             apps = config["apps"]
#             for app in apps.keys():
#                 await self._app_migrate(config, app)
#
#     def execute(self, app: str = None):
#         asyncio.run(self._async_execute(app))
