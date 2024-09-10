from fastapi import Request, Body
from pydantic import BaseModel
from typing import Annotated


class CreateModelMixin:
    allowed_methods = ["POST"]

    async def create(self, body: Annotated[BaseModel, Body()], *, request: Request):
        data = body.model_dump()
        return await self.service.insert(data, request=request)


class UpdateModelMixin:
    allowed_methods = ["PUT", "PATCH"]

    async def update(self, pk, body: Annotated[BaseModel, Body()], *, request: Request):
        data = body.model_dump()
        return await self.service.update(pk, data, request=request)

    async def partial_update(
        self, pk, body: Annotated[BaseModel, Body()], *, request: Request
    ):
        data = body.model_dump(exclude_unset=True)
        return await self.service.update(pk, data, request=request)


class DestroyModelMixin:
    allowed_methods = ["DELETE"]

    async def destroy(self, pk, *, request: Request):
        return await self.service.delete(pk, request=request)


class RetrieveModelMixin:
    allowed_methods = ["GET"]

    async def retrieve(self, pk, *, request: Request):
        return await self.service.get(pk, request=request)


class ListModelMixin:
    allowed_methods = ["LIST"]

    async def list(self, request: Request):
        return await self.service.select(request)
