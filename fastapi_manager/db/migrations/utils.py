async def get_table_list(connection):
    dialect = connection._db_type
    query = ""

    if dialect == "postgres":
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
    elif dialect == "mysql":
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE();"
    elif dialect == "sqlite":
        query = "SELECT name FROM sqlite_master WHERE type = 'table';"
    tables = await connection.execute_query(query)
    return list(map(lambda x: x[0], tables))
