from importlib import import_module
from fastapi import APIRouter, FastAPI
from fastapi_manager.conf import settings


class BaseRouter(APIRouter):

    @classmethod
    def as_view(cls, **initkwargs):
        return cls(**initkwargs)


async def resolve_endpoints(app: FastAPI):
    from .conf import ENDPOINTS_VAR

    root_router = import_module(settings.ROOT_ROUTER)
    try:
        endpoints = getattr(root_router, ENDPOINTS_VAR)
    except AttributeError:
        raise AttributeError(
            f"You need set enpoints list in format {ENDPOINTS_VAR} = []"
        )

    for endpoint in endpoints:
        app.include_router(endpoint)
