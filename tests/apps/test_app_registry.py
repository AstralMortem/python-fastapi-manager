import pytest
import asyncio
from unittest.mock import patch, MagicMock
from collections import defaultdict

from fastapi_manager.apps.registry import AppRegistry
from fastapi_manager.apps.config import AppConfig


@pytest.fixture
def mock_app_config():
    return MagicMock(spec=AppConfig)


@pytest.fixture
def app_registry():
    return AppRegistry()


def test_singleton_behavior():
    reg1 = AppRegistry()
    reg2 = AppRegistry()
    assert reg1 is reg2


def test_initialize(app_registry):
    assert app_registry.apps == {}
    assert isinstance(app_registry.models_dict, defaultdict)
    assert not app_registry.apps_ready
    assert not app_registry.models_ready
    assert not app_registry.ready
    assert isinstance(app_registry._lock, asyncio.Lock)


def test_population(app_registry):
    # Create unique mock AppConfig instances for each app
    mock_app_config1 = MagicMock(spec=AppConfig)
    mock_app_config1.label = "mock_label1"

    mock_app_config2 = MagicMock(spec=AppConfig)
    mock_app_config2.label = "mock_label2"

    with patch('fastapi_manager.apps.config.AppConfig.create') as mock_create, \
            patch('asyncio.Lock', return_value=MagicMock()), \
            patch.object(mock_app_config1, 'import_models') as mock_import_models1, \
            patch.object(mock_app_config2, 'import_models') as mock_import_models2, \
            patch.object(mock_app_config1, 'on_ready', return_value=asyncio.Future()) as mock_on_ready1, \
            patch.object(mock_app_config2, 'on_ready', return_value=asyncio.Future()) as mock_on_ready2:
        mock_create.side_effect = [mock_app_config1, mock_app_config2]
        mock_on_ready1.return_value.set_result(None)
        mock_on_ready2.return_value.set_result(None)

        installed_apps = ["app1", "app2"]
        app_registry.populate(installed_apps)

        # Ensure that AppConfig.create was called for each installed app
        mock_create.assert_any_call("app1")
        mock_create.assert_any_call("app2")
        assert len(app_registry.apps) == 2

        # Ensure the mock config objects are stored in the registry under unique labels
        assert app_registry.get_app_config("mock_label1") == mock_app_config1
        assert app_registry.get_app_config("mock_label2") == mock_app_config2

        # Ensure import_models was called for each app
        mock_import_models1.assert_called_once()
        mock_import_models2.assert_called_once()

        # Ensure on_ready was awaited for each app
        assert mock_on_ready1.call_count == 1
        assert mock_on_ready2.call_count == 1

        # Ensure that the registry flags are set
        assert app_registry.apps_ready
        assert app_registry.models_ready
        assert app_registry.ready



def test_check_apps_ready(app_registry):
    app_registry.apps_ready = False
    with pytest.raises(Exception, match="Apps aren't loaded yet."):
        app_registry.check_apps_ready()

    app_registry.apps_ready = True
    try:
        app_registry.check_apps_ready()  # Should not raise
    except Exception:
        pytest.fail("check_apps_ready raised Exception unexpectedly!")


def test_check_models_ready(app_registry):
    app_registry.models_ready = False
    with pytest.raises(Exception, match="Models aren't loaded yet."):
        app_registry.check_models_ready()

    app_registry.models_ready = True
    try:
        app_registry.check_models_ready()  # Should not raise
    except Exception:
        pytest.fail("check_models_ready raised Exception unexpectedly!")


def test_get_app_configs(app_registry, mock_app_config):
    with patch.object(app_registry, 'check_apps_ready') as mock_check_apps_ready:
        app_registry.apps = {"app1": mock_app_config}
        configs = app_registry.get_app_configs()
        mock_check_apps_ready.assert_called_once()
        assert list(configs) == [mock_app_config]


def test_get_app_config(app_registry, mock_app_config):
    with patch.object(app_registry, 'check_apps_ready') as mock_check_apps_ready:
        app_registry.apps = {"app1": mock_app_config}
        config = app_registry.get_app_config("app1")
        mock_check_apps_ready.assert_called_once()
        assert config == mock_app_config

        with pytest.raises(LookupError, match="No installed app with label 'app2'."):
            app_registry.get_app_config("app2")
