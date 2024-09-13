import pytest
from unittest.mock import AsyncMock, patch
from tortoise.connection import connections


@pytest.fixture
def mock_connection():
    """Fixture for mocking the database connection."""
    return AsyncMock()


@pytest.fixture
def recorder(mock_connection):
    from fastapi_manager.db.migrations.recorder import MigrationRecorder

    """Fixture for initializing MigrationRecorder with mock connection."""
    with patch.object(connections, "get", return_value=mock_connection):
        return MigrationRecorder("test_connection")


@pytest.mark.asyncio
async def test_has_table_true(recorder, mock_connection):
    from fastapi_manager.db.migrations.models import MigrationModel

    """Test that has_table returns True when the table exists."""
    mock_connection.execute_query = AsyncMock()
    get_table_list_mock = AsyncMock(return_value=[MigrationModel._meta.db_table])

    with patch(
        "fastapi_manager.db.migrations.utils.get_table_list", get_table_list_mock
    ):
        result = await recorder.has_table()
        print(recorder)

    assert result is True


@pytest.mark.asyncio
async def test_has_table_false(recorder, mock_connection):
    """Test that has_table returns False when the table does not exist."""
    mock_connection.execute_query = AsyncMock()
    get_table_list_mock = AsyncMock(return_value=[])

    with patch(
        "fastapi_manager.db.migrations.utils.get_table_list", get_table_list_mock
    ):
        result = await recorder.has_table()

    assert result is False


@pytest.mark.asyncio
async def test_ensure_table_create_table(recorder, mock_connection):
    """Test that ensure_table creates the table when it does not exist."""
    recorder.has_table = AsyncMock(return_value=False)
    mock_connection.schema_generator()._get_table_sql.return_value = {
        "table_creation_string": "CREATE TABLE ..."
    }

    with patch("fastapi_manager.db.migrations.utils.get_table_list", AsyncMock()):
        await recorder.ensure_table()

    mock_connection.execute_script.assert_called_once()


@pytest.mark.asyncio
async def test_ensure_table_already_exists(recorder):
    """Test that ensure_table does nothing if the table already exists."""
    recorder.has_table = AsyncMock(return_value=True)

    await recorder.ensure_table()

    recorder.connection.execute_script.assert_not_called()


@pytest.mark.asyncio
async def test_apply_migration(recorder, mock_connection):
    from fastapi_manager.db.migrations.models import MigrationModel

    """Test that apply_migration ensures table and creates migration."""
    recorder.ensure_table = AsyncMock()
    MigrationModel.create = AsyncMock()

    await recorder.apply_migration("v1.0", "my_app")

    recorder.ensure_table.assert_called_once()
    MigrationModel.create.assert_called_once_with(app="my_app", version="v1.0")


@pytest.mark.asyncio
async def test_remove_migration(recorder, mock_connection):
    from fastapi_manager.db.migrations.models import MigrationModel

    """Test that remove_migration ensures table and deletes migration."""
    recorder.ensure_table = AsyncMock()
    MigrationModel.filter().delete = AsyncMock()

    await recorder.remove_migration("v1.0", "my_app")

    recorder.ensure_table.assert_called_once()
    MigrationModel.filter.assert_called_once_with(version="v1.0", app="my_app")
    MigrationModel.filter().delete.assert_awaited_once()
