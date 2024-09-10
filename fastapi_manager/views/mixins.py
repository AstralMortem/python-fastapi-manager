from pydantic import BaseModel
from fastapi import Request
from typing import Any

from fastapi_manager.services.base import AbstractService


class CreateModelMixin:
    service: type[AbstractService]

    async def create(self, data: BaseModel, request: Request):
        data_to_dict = data.model_dump()
        obj = await self.service.insert(data_to_dict, request)
        return obj


class ListModelMixin:
    service: type[AbstractService]

    async def list_all(self, request: Request):
        obj = await self.service.select(request)
        return obj


class RetrieveModelMixin:
    service: type[AbstractService]

    async def retrieve(self, pk: Any, request: Request):
        return await self.service.get(pk, request)


class UpdateModelMixin:
    service: type[AbstractService]

    async def update(self, pk: Any, data: BaseModel, request: Request):
        data_to_dict = data.model_dump()
        return await self.service.update(pk, data_to_dict, request)

    async def partial_update(self, pk: Any, data: BaseModel, request: Request):
        data_to_dict = data.model_dump()
        return await self.service.update(pk, data_to_dict, request)


class DestroyModelMixin:
    service: type[AbstractService]

    async def destroy(self, pk: Any, request: Request):
        return await self.service.delete(pk, request)
