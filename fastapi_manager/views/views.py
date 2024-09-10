from typing import Tuple

from pydantic import BaseModel
from fastapi.responses import JSONResponse

from fastapi_manager.router import BaseRouter
from fastapi_manager.services import BaseService
from tortoise.contrib.pydantic import pydantic_model_creator
from fastapi import Response


class APIView(BaseRouter):
    service: BaseService

    response_model: dict[str, BaseModel] = {}
    response_class: dict[str, Response] = {}
    allowed_methods: Tuple[str] = tuple()

    def get_model(self):
        return self.service.model

    def get_response_model_class(self, method):
        if method in self.allowed_methods:
            return self.response_model.get(
                method, pydantic_model_creator(self.get_model())
            )

    def get_response_class(self, method):
        if method in self.allowed_methods:
            return self.response_class.get(method, JSONResponse)
