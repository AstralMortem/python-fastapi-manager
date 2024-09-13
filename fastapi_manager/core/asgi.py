from collections.abc import Callable
from contextlib import asynccontextmanager, AsyncExitStack
from typing import Optional, Union, List, Any

from fastapi import FastAPI
from fastapi_manager.conf import settings
from fastapi_manager import setup

from fastapi_manager.db.connection import register_orm
from fastapi_manager.router import resolve_endpoints
from .logger import init_loger


@asynccontextmanager
async def init_app(app: FastAPI):
    await setup()
    yield


def global_lifespan(user_lifespan=None):
    sys_lifespans = [
        init_loger,
        init_app,
        register_orm,
        resolve_endpoints,
    ]
    if user_lifespan:
        if isinstance(user_lifespan, list):
            sys_lifespans.extend(user_lifespan)
        elif isinstance(user_lifespan, Callable):
            sys_lifespans.append(user_lifespan)
        else:
            raise Exception("You should pass @asyncontextmanager func or list of funcs")

    @asynccontextmanager
    async def _lifespan_manager(app: FastAPI):
        exit_stack = AsyncExitStack()
        async with exit_stack:
            for lifespan in sys_lifespans:
                await exit_stack.enter_async_context(lifespan(app))
            yield

    return _lifespan_manager


class Application(FastAPI):

    def __init__(
        self,
        lifespan: Optional[Union[List[Callable], Callable]] = None,
        *args,
        **kwargs
    ) -> None:
        self.user_lifespan = lifespan

        super().__init__(
            lifespan=global_lifespan(self.user_lifespan),
            title=settings.PROJECT_TITLE,
            version=settings.PROJECT_VERSION,
            root_path=settings.PROJECT_ROOT_PATH,
            debug=settings.DEBUG,
            *args,
            **kwargs
        )
