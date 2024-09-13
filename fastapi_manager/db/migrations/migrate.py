from tortoise import BaseDBAsyncClient

from .operations import Operation, CreateModel


class Migration:

    to_upgrade: list[Operation] = []
    to_downgrade: list[Operation] = []

    initial = True

    atomic = True

    def __init__(self, name):
        self.name = name

    # Generate SQL script
    def _get_script(self, statements: list[Operation]):
        return ";\n        ".join(list(map(lambda x: x.to_sql(), statements))) + ";"

    # apply SQL script to DB
    async def apply(self, conn: BaseDBAsyncClient, run: bool = True):
        Operation.schema_generator = conn.schema_generator(conn)

        query_script = self._get_script(self.to_upgrade)
        if run:
            await conn.execute_script(query_script)
        return query_script

    # apply SQL script to DB with reverse action
    async def reverse(self, conn: BaseDBAsyncClient, run: bool = True):
        Operation.schema_generator = conn.schema_generator(conn)
        query_script = self._get_script(self.to_downgrade)
        if run:
            await conn.execute_script(query_script)
        return query_script

    def describe(self):
        pass
