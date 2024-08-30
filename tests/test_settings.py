from fastapi_manager.conf import settings


def test_local_settings():
    print(settings.DEBUG)