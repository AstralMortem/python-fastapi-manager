from typing import Union, Callable, Any, List, Optional, Dict
from .base import BaseRouter
from fastapi_manager.apps import apps


ENDPOINTS_VAR = "ENDPOINTS"


def path(
    path: str, view: Union[BaseRouter, List[BaseRouter], type[BaseRouter]], **initkwargs
) -> BaseRouter:
    root_router = BaseRouter(prefix=path, **initkwargs)
    if isinstance(view, list):
        for route in view:
            root_router.include_router(route)
    elif isinstance(view, BaseRouter):
        root_router.include_router(view)
    elif issubclass(view, BaseRouter):
        root_router.include_router(register_view_set(view, **initkwargs))
    else:
        raise ValueError(
            f"View must be either a BaseRouter or a subclass of BaseRouter"
        )

    return root_router


def include(path: str):
    app_name, module_name = path.rsplit(".", 1)
    app_config = apps.get_app_config(app_name)
    return app_config.get_router(ENDPOINTS_VAR)


def register_view_set(viewset, **initkwargs):
    from fastapi_manager.viewsets.base import MAPPINGS

    allowed_methods = {
        k: v for k, v in MAPPINGS.items() if v.upper() in viewset.allowed_methods
    }

    res = viewset.as_view(allowed_methods, **initkwargs)

    return res
