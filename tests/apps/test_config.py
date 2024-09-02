from pathlib import Path
from types import ModuleType

import pytest
from unittest.mock import patch, MagicMock
from fastapi_manager.apps.config import AppConfig, AppCreator


def test_app_config_initialization():
    app_name = "test_app"
    app_module = MagicMock(__name__=app_name, __path__=["/path/to/test_app"])

    config = AppConfig(app_name, app_module)

    assert config.name == app_name
    assert config.label == "test_app"
    assert config.module == app_module
    assert config.app_registry is None


def test_app_config_invalid_label():
    app_name = "test_app.invalid-label"
    app_module = MagicMock(__name__=app_name, __path__=["/path/to/test_app"])

    with pytest.raises(Exception):
        AppConfig(app_name, app_module)


def test_app_config_path_resolution():
    app_name = "test_app"
    app_module = MagicMock(__name__=app_name, __path__=["/path/to/test_app"])

    config = AppConfig(app_name, app_module)

    assert config.path == "/path/to/test_app"


# def test_app_config_import_models():
#     app_name = "test_app"
#     app_module = MagicMock(
#         __name__=app_name, __path__=[str(Path("test_app").absolute())], models = MagicMock(__name__="models")
#     )
#
#
#     config = AppConfig(app_name, app_module)
#     config.app_registry = MagicMock(models_dict={config.label: {}})
#
#     with patch("fastapi_manager.apps.config.import_module") as mock_import_module:
#         config.import_models()
#         mock_import_module.assert_called_once_with(f"{app_name}.models")
#         assert config.models == config.app_registry.models_list[config.label]


def test_app_config_create():
    entry = "test_app"

    with patch("fastapi_manager.apps.config.import_module") as mock_import_module:
        mock_module = MagicMock(__name__=entry, __path__=["/path/to/test_app"])
        mock_import_module.return_value = mock_module

        app_config = AppConfig.create(entry)

        assert app_config.name == entry
        assert app_config.module == mock_module





# Mock modules
class MockModule(ModuleType):
    pass


class MockAppConfig(AppConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@pytest.fixture
def mock_module():
    return MockModule("mock_module")


@pytest.fixture
def mock_app_config(mock_module):
    return MockAppConfig("mock_app", mock_module)


@pytest.fixture
def app_creator():
    return AppCreator()


def test_try_get_module(app_creator):
    with patch('fastapi_manager.apps.config.import_module') as mock_import_module:  # Replace with the actual module path
        mock_import_module.return_value = MagicMock()
        app_creator.app_entry = "test_entry"
        app_creator.try_get_module()
        mock_import_module.assert_called_once_with("test_entry")
        assert app_creator.app_module is not None


def test_try_get_config_or_init_new(app_creator, mock_module):
    with patch('fastapi_manager.apps.config.import_module') as mock_import_module, \
            patch('fastapi_manager.apps.config.inspect.getmembers') as mock_getmembers, \
            patch('fastapi_manager.apps.config.module_has_submodule') as mock_module_has_submodule:

        mock_module_has_submodule.return_value = True
        mock_import_module.return_value = mock_module
        mock_getmembers.return_value = [("MockAppConfig", MockAppConfig)]
        app_creator.app_entry = "test_entry"
        app_creator.app_module = mock_module
        app_creator.try_get_config_or_init_new()

        mock_import_module.assert_called_once_with(f"test_entry.config")
        assert app_creator.app_config == MockAppConfig


def test_try_import_as_string(app_creator):
    with patch('fastapi_manager.apps.config.import_string') as mock_import_string:
        mock_import_string.return_value = MockAppConfig
        app_creator.app_entry = "mock_app_entry"
        app_creator.try_import_as_string()
        mock_import_string.assert_called_once_with("mock_app_entry")
        assert app_creator.app_config == MockAppConfig


def test_try_set_appconfig_name(app_creator):
    app_creator.app_config = MagicMock()
    app_creator.app_config.name = "test_name"
    app_creator.try_set_appconfig_name()
    assert app_creator.app_name == "test_name"


def test_try_import_module_by_config_name(app_creator):
    app_creator.app_name = "mock_app"
    with patch('fastapi_manager.apps.config.import_module') as mock_import_module:
        app_creator.try_import_module_by_config_name()
        mock_import_module.assert_called_once_with("mock_app")



def test_get_unique_module_path(app_creator, mock_module):
    mock_module.__path__ = ["mock/path"]
    path = app_creator.get_unique_module_path(mock_module)
    assert not isinstance(path, Path)
    assert Path(path) == Path("mock/path")

    mock_module.__path__ = []
    mock_module.__file__ = "mock/path/__init__.py"
    path = app_creator.get_unique_module_path(mock_module)
    assert Path(path) == Path("mock/path")
