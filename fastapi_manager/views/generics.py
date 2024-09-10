from typing import Callable
from .views import APIView
import inspect
import re


def _view_class_name_default_parser(cls: object, method: str = None):

    names = cls.__name__
    names = names.replace("ViewSet", "")
    names = names.replace("View", "")

    class_name = " ".join(re.findall(r"[A-Z][^A-Z]*", names))  # type: ignore
    if method:
        return f"{method.capitalize()} {class_name}"
    return class_name


class GenericAPIView(APIView):
    lookup_field: str = "pk"
    name_parser: Callable[[object, str], str] = _view_class_name_default_parser

    def get_paths(self, func):
        fields = []
        sig = inspect.signature(func)
        for name, param in sig.parameters.items():
            if name == self.lookup_field:
                fields.append(name)

        return "/".join(["{" + i + "}" for i in fields])
