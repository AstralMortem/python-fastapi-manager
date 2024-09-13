# from tortoise import Tortoise, generate_schema_for_client
# from aerich.utils import get_app_connection
# from .migrate import Migration
#
#
# class Command:
#
#     def __init__(self, config):
#         self.config = config
#
#     async def makemigrations(self, message: str = "update", app=None):
#         if app is not None:
#             await Migrate.init(self.config, app)
#             await Migrate.migrate(message)
#         else:
#             apps = self.config.get("apps")
#             for app in apps.keys():
#                 await Migrate.init(self.config, app)
#                 await Migrate.migrate(message)
#
#     async def migrate(self):
#         pass
#
#     async def downgrade(self):
#         pass
