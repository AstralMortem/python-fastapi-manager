import pytest
from fastapi_manager.conf import settings
from tests import local_config

@pytest.fixture(scope='function', autouse=True)
def local_settings():
    settings.configure(settings_module=local_config)