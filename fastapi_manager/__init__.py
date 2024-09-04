async def setup():

    from fastapi_manager.conf import settings
    from fastapi_manager.apps import apps

    await apps.async_populate(settings.INSTALLED_APPS)
