from fastapi import HTTPException, status, Depends, Path
from typing import Iterable, Annotated, Any
from fastapi_class.views import (
    RESPONSE_MODEL_ATTRIBUTE_NAME,
    RESPONSE_CLASS_ATTRIBUTE_NAME,
    EXCEPTIONS_ATTRIBUTE_NAME,
    COMMON_KEYWORD,
    ENDPOINT_METADATA_ATTRIBUTE_NAME,
    _view_class_name_default_parser,
)
from starlette.responses import JSONResponse
from fastapi_manager.router import BaseRouter
from fastapi_class import Method, _exceptions_to_responses
from .metadata import Metadata

from fastapi_manager.services import BaseService
import inspect


def set_path_params(func):
    signature = inspect.signature(func)

    parameters = signature.parameters
    defaults = {
        "{" + name + "}": param.annotation
        for name, param in parameters.items()
        if param.name == "id" or param.name == "pk"
    }
    return "/".join(defaults.keys())


class GenericView:
    router = BaseRouter()
    path = "/"
    name_parser = _view_class_name_default_parser
    default_status_code: int = status.HTTP_200_OK
    service: type[BaseService]
    dependencies: dict[str, Depends] = None

    @classmethod
    def as_view(cls):
        return cls._view()

    @classmethod
    def _view(cls):
        obj = cls()
        cls_based_response_model = getattr(obj, RESPONSE_MODEL_ATTRIBUTE_NAME, {})
        cls_based_response_class = getattr(obj, RESPONSE_CLASS_ATTRIBUTE_NAME, {})
        common_exceptions = getattr(obj, EXCEPTIONS_ATTRIBUTE_NAME, {}).get(
            COMMON_KEYWORD, ()
        )
        for _callable_name in dir(obj):
            _callable = getattr(obj, _callable_name)
            if _callable_name in set(Method) or hasattr(
                _callable, ENDPOINT_METADATA_ATTRIBUTE_NAME
            ):
                metadata: Metadata = getattr(
                    _callable,
                    ENDPOINT_METADATA_ATTRIBUTE_NAME,
                    Metadata([_callable_name], path=set_path_params(_callable)),
                )
                exceptions: Iterable[HTTPException] = getattr(
                    obj, ENDPOINT_METADATA_ATTRIBUTE_NAME, {}
                ).get(_callable_name, [])
                exceptions += common_exceptions
                _path = cls.path
                if metadata and metadata.path:
                    _path = cls.path + metadata.path
                obj.router.add_api_route(
                    _path,
                    _callable,
                    methods=list(metadata.methods),
                    response_class=metadata.response_class_or_default(
                        cls_based_response_class.get(_callable_name, JSONResponse)
                    ),
                    response_model=metadata.response_model_or_default(
                        cls_based_response_model.get(_callable_name)
                    ),
                    responses=_exceptions_to_responses(exceptions),
                    name=metadata.name_or_default(cls.name_parser(cls, _callable_name)),
                    status_code=metadata.status_code_or_default(
                        obj.default_status_code
                    ),
                )
        return obj.router
