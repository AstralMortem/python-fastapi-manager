from typing import Union, Callable, Any, List, Optional, Dict
from .base import BaseRouter
from fastapi_manager.apps import apps

ENDPOINTS_VAR = "ENDPOINTS"


def path(
    path: str,
    view: Union[BaseRouter, List[BaseRouter]],
    router_conf: Optional[Dict] = None,
) -> BaseRouter:
    root_router = BaseRouter(
        prefix=path, **router_conf if router_conf is not None else {}
    )
    if isinstance(view, list):
        for route in view:
            root_router.include_router(route)
    elif isinstance(view, BaseRouter):
        root_router.include_router(view)

    return root_router


def include(path: str):
    app_name, module_name = path.rsplit(".", 1)
    app_config = apps.get_app_config(app_name)
    return app_config.get_router(ENDPOINTS_VAR)
