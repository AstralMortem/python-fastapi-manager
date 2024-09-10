from dataclasses import field
from functools import wraps
from typing import Callable, ClassVar, Any

from pydantic import BaseModel, field_validator
from fastapi import status, Response

from fastapi_manager.router import BaseRouter
from fastapi_manager.views import generics
from fastapi_manager.views import mixins


MAPPINGS = {
    "retrieve": "GET",
    "list": "GET",
    "update": "PUT",
    "destroy": "DELETE",
    "partial_update": "PATCH",
    "create": "POST",
}


class Metadata(BaseModel):
    methods: list[str]
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


def endpoint(
    methods: list[str],
    *,
    name: str | None = None,
    path: str | None = None,
    status_code: int | None = None,
    response_model: type[BaseModel] | None = None,
    response_class: type[Response] | None = None,
):

    assert all(
        issubclass(_type, expected_type)
        for _type, expected_type in (
            (response_model, BaseModel),
            (response_class, Response),
        )
        if _type is not None
    ), "Response model and response class must be subclasses of BaseModel and Response respectively."
    assert (
        isinstance(methods, list) or methods is None
    ), "Methods must be an string, iterable of strings or Method enums."

    def _decorator(function: Callable):
        """
        Decorate the function.
        """

        @wraps(function)
        async def _wrapper(*args, **kwargs):
            """
            Wrapper for the function.
            """
            return await function(*args, **kwargs)

        _wrapper.__endpoint_metadata = Metadata(  # type: ignore
            methods=methods,
            name=name,
            path=path if not path.startswith("/") else path[1:],
            status_code=status_code,
            response_class=response_class,
            response_model=response_model,
        )
        return _wrapper

    return _decorator


class ViewSetMixin(BaseRouter):
    path: str = "/"
    default_status_code: int = status.HTTP_200_OK

    @classmethod
    def as_view(cls, actions=None, **initkwargs):

        if actions is None:
            raise ValueError("actions cannot be None")

        for i in initkwargs:
            if not hasattr(BaseRouter, i):
                raise AttributeError(f"{i} has no attribute {i}")

        def view():
            self = cls(**initkwargs)
            for action in actions.values():
                if action not in self.allowed_methods:
                    raise ValueError(f"action {action} is not allowed for that class")

            for _callable_name in dir(self):
                handler = getattr(self, _callable_name)
                if _callable_name in actions.keys() or hasattr(
                    handler, "__endpoint_metadata"
                ):
                    method = actions.get(_callable_name, "")
                    print(method)
                    metadata: Metadata = getattr(
                        handler,
                        "__endpoint_metadata",
                        Metadata(methods=[method], path=self.get_paths(handler)),
                    )

                    _path = self.path
                    if metadata and metadata.path:
                        _path = self.path + metadata.path

                    self.add_api_route(
                        _path,
                        handler,
                        methods=metadata.methods,
                        name=cls.name_parser(cls, method),
                        tags=[cls.name_parser(cls)],
                        response_model=self.get_response_model_class(method),
                        # response_class=self.get_response_class(method),
                        status_code=self.default_status_code,
                    )
            return self

        return view()


class GenericViewSet(ViewSetMixin, generics.GenericAPIView):

    def __init_subclass__(cls, **kwargs):
        allowed_methods = []
        for i in cls.mro():
            if i.__name__.endswith("Mixin"):
                allowed_methods.extend(
                    list(getattr(i, "allowed_methods", allowed_methods))
                )

        cls.allowed_methods = tuple(set(allowed_methods))


class ReadOnlyModelViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    pass


class ModelViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    pass
