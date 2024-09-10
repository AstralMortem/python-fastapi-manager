import re
from enum import Enum, StrEnum
from typing import Literal, Dict, Any, Callable, Iterable, ClassVar, Annotated
from pydantic import BaseModel, Field, field_validator, root_validator, model_validator
import inspect
from starlette.responses import JSONResponse
from tortoise.contrib.pydantic import pydantic_model_creator
from fastapi import status, HTTPException, Response, Path

from fastapi_manager.db.models import PK
from fastapi_manager.router import BaseRouter
from fastapi_manager.services.base import AbstractService, _ORM_MODEL


COMMON_KEYWORD = "common"
RESPONSE_MODEL_ATTRIBUTE_NAME = "response_model"
RESPONSE_CLASS_ATTRIBUTE_NAME = "response_class"
ENDPOINT_METADATA_ATTRIBUTE_NAME = "__endpoint_metadata"
EXCEPTIONS_ATTRIBUTE_NAME = "EXCEPTIONS"
ACTIONS = Literal["create", "update", "destroy", "list", "retrieve", "partial_update"]


def _view_class_name_default_parser(cls: object, method: str):
    class_name = " ".join(re.findall(r"[A-Z][^A-Z]*", cls.__name__.replace("View", "")))  # type: ignore
    return f"{method.capitalize()} {class_name}"


class Method(str, Enum):
    GET = "get"
    POST = "post"
    PATCH = "patch"
    DELETE = "delete"
    PUT = "put"


ACTIONS_MAP: Dict[str, Method] = {
    "post": Method.POST,
    "update": Method.PUT,
    "delete": Method.DELETE,
    "list": Method.GET,
    "get": Method.GET,
    "patch": Method.PATCH,
}


class Metadata(BaseModel):
    methods: Iterable[str | Method]
    name: str | None = None
    path: str | None = None
    status_code: int | None = None
    response_model: type[BaseModel] | None = None
    response_class: type[Response] | None = None
    __default_method_suffix: ClassVar[str] = "_or_default"

    def __getattr__(self, __name: str) -> Any | Callable[[Any], Any]:
        """
        Dynamically return the value of the attribute.
        """
        if __name.endswith(Metadata.__default_method_suffix):
            prefix = __name.replace(Metadata.__default_method_suffix, "")
            if hasattr(self, prefix):
                return lambda _default: getattr(self, prefix, None) or _default
            return getattr(self, prefix)
        raise AttributeError(f"{self.__class__.__name__} has no attribute {__name}")


class GenericView:
    model: type[_ORM_MODEL]
    service: type[AbstractService]
    dependencies: dict[str, Any] = {}
    name_parser: Callable[[object, str], str] = _view_class_name_default_parser
    default_status_code: int = status.HTTP_200_OK
    path: str = "/"
    router: type[BaseRouter] = BaseRouter

    @staticmethod
    def get_lookup_field(func):
        signature = inspect.signature(func)
        for name, param in signature.parameters.items():
            if (
                name == "pk"
                or name == "id"
                or type(param.annotation) == type(Annotated[PK, Path()])
                or type(param.annotation) == type(Annotated[Any, Path()])
            ):
                return "{" + name + "}"

    @classmethod
    def as_view(cls, **initkwargs):

        self = cls()
        router = self.router(**initkwargs)
        lookup_field = "pk"

        cls_based_response_model = getattr(self, RESPONSE_MODEL_ATTRIBUTE_NAME, {})
        cls_based_response_class = getattr(self, RESPONSE_CLASS_ATTRIBUTE_NAME, {})
        common_exceptions = getattr(self, EXCEPTIONS_ATTRIBUTE_NAME, {}).get(
            COMMON_KEYWORD, ()
        )

        for _callable_name in dir(self):
            _callable_func = getattr(self, _callable_name)
            if _callable_name in set(ACTIONS_MAP.keys()) or hasattr(
                _callable_func, ENDPOINT_METADATA_ATTRIBUTE_NAME
            ):
                metadata: Metadata = getattr(
                    _callable_func,
                    ENDPOINT_METADATA_ATTRIBUTE_NAME,
                    Metadata(
                        methods=[ACTIONS_MAP.get(_callable_name).value],
                        path=cls.get_lookup_field(_callable_func),
                    ),
                )
                exceptions: Iterable[HTTPException] = getattr(
                    self, ENDPOINT_METADATA_ATTRIBUTE_NAME, {}
                ).get(_callable_name, [])
                exceptions += common_exceptions
                _path = self.path
                if metadata and metadata.path:
                    _path = self.path + metadata.path
                router.add_api_route(
                    _path,
                    _callable_func,
                    methods=list(metadata.methods),
                    response_class=metadata.response_class_or_default(
                        cls_based_response_class.get(_callable_name, JSONResponse)
                    ),
                    response_model=metadata.response_model_or_default(
                        cls_based_response_model.get(_callable_name)
                    ),
                    name=metadata.name_or_default(cls.name_parser(cls, _callable_name)),
                    status_code=metadata.status_code_or_default(
                        self.default_status_code
                    ),
                )
        return router
