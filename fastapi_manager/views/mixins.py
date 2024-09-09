from typing import Any

from pydantic import BaseModel
from fastapi import Request


class CreateModelMixin:
    async def create(self, data: BaseModel, request: Request):
        data_to_dict = data.model_dump()
        obj = await self.service.create(data_to_dict, request)
        return obj


class ListModelMixin:
    async def list(self, request: Request):
        obj = await self.service.filter(request)
        return obj


class RetrieveModelMixin:
    async def retrieve(self, pk: Any, request: Request):
        return await self.service.get(pk, request)


class UpdateModelMixin:
    async def update(self, pk: Any, data: BaseModel, request: Request):
        data_to_dict = data.model_dump()
        return await self.service.update(pk, data_to_dict, request)

    async def partial_update(self, pk: Any, data: BaseModel, request: Request):
        data_to_dict = data.model_dump()
        return await self.service.update(pk, data_to_dict, request)


class DestroyModelMixin:
    async def destroy(self, pk: Any, request: Request):
        return await self.service.delete(pk, request)
