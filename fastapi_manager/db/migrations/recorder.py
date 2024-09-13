from .models import MigrationModel
from .utils import get_table_list
from tortoise.connection import connections


class MigrationRecorder:

    def __init__(self, connection_name):
        self._has_table = False
        self.connection = connections.get(connection_name)

    async def has_table(self):
        if self._has_table:
            return True
        self._has_table = MigrationModel._meta.db_table in list(
            await get_table_list(self.connection)
        )
        return self._has_table

    async def ensure_table(self):
        if await self.has_table():
            return
        try:
            create_string = self.connection.schema_generator(
                self.connection
            )._get_table_sql(MigrationModel, False)["table_creation_string"]
            await self.connection.execute_script(create_string)

        except Exception as e:
            raise Exception(e)

    async def apply_migration(self, version, app):
        await self.ensure_table()
        await MigrationModel.create(
            app=app,
            version=version,
        )

    async def remove_migration(self, version, app):
        await self.ensure_table()
        await MigrationModel.filter(version=version, app=app).delete()
