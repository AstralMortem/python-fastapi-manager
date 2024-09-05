from contextlib import asynccontextmanager
from fastapi import FastAPI

from fastapi_manager import setup


@asynccontextmanager
async def global_lifespan(app: "Application"):
    # run global startup event
    print("Setup server")
    await setup()

    # check if user set custom lifespan
    # else just yield
    if app.user_lifespan is not None:
        async with app.user_lifespan(app) as custom:
            yield custom
    else:
        yield

    # run global end event
    print("GOODBYE")


class Application(FastAPI):

    def __init__(self, lifespan=None, *args, **kwargs) -> None:
        from fastapi_manager.conf import settings

        self.user_lifespan = lifespan
        super().__init__(
            lifespan=global_lifespan,
            title=settings.PROJECT_TITLE,
            version=settings.PROJECT_VERSION,
            root_path=settings.PROJECT_ROOT_PATH,
            *args,
            **kwargs
        )
