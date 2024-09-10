from uuid import UUID

from pydantic import BaseModel
from .base import GenericView
from .mixins import (
    CreateModelMixin,
    ListModelMixin,
    DestroyModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from typing import Generic, TypeVar, Annotated, Union, override, Any
from fastapi import Request, Path
from fastapi_manager.db.models import PK

_INPUT_MODEL = TypeVar("_INPUT_MODEL", bound=BaseModel)


class APIView(GenericView):
    pass


class CreateAPIView(Generic[_INPUT_MODEL], CreateModelMixin, APIView):
    async def post(self, request: Request, data: _INPUT_MODEL):
        return await self.create(data, request)


class ListAPIView(ListModelMixin, APIView):
    async def list(self, request: Request):
        return await self.list_all(request)


class RetrieveAPIView(RetrieveModelMixin, APIView):
    async def get(self, request: Request, pk: Annotated[PK, Path()]):
        return await self.retrieve(pk, request)


class DestroyAPIView(DestroyModelMixin, APIView):
    async def delete(self, request: Request, pk: Annotated[PK, Path()]):
        return await self.destroy(pk, request)


class UpdateAPIView(Generic[_INPUT_MODEL], UpdateModelMixin, APIView):
    async def put(
        self, request: Request, pk: Annotated[PK, Path()], data: _INPUT_MODEL
    ):
        return await self.update(pk, data, request)

    async def patch(
        self, request: Request, pk: Annotated[PK, Path()], data: _INPUT_MODEL
    ):
        return await self.partial_update(pk, data, request)


class RetrieveUpdateAPIView(
    Generic[_INPUT_MODEL], RetrieveModelMixin, UpdateModelMixin, APIView
):
    async def get(self, request: Request, pk: Annotated[PK, Path()]):
        return await self.retrieve(pk, request)

    async def put(
        self, request: Request, pk: Annotated[PK, Path()], data: _INPUT_MODEL
    ):
        return await self.update(pk, data, request)

    async def patch(
        self, request: Request, pk: Annotated[PK, Path()], data: _INPUT_MODEL
    ):
        return await self.partial_update(pk, data, request)


class RetrieveDestroyAPIView(RetrieveModelMixin, DestroyModelMixin, APIView):
    async def get(self, request: Request, pk: Annotated[PK, Path()]):
        return await self.retrieve(pk, request)

    async def delete(self, request: Request, pk: Annotated[PK, Path()]):
        return await self.destroy(pk, request)


class RetrieveUpdateDestroyAPIView(
    Generic[_INPUT_MODEL],
    RetrieveModelMixin,
    DestroyModelMixin,
    UpdateModelMixin,
    APIView,
):

    async def get(self, request: Request, pk: Annotated[PK, Path()]):
        return await self.retrieve(pk, request)

    async def delete(self, request: Request, pk: Annotated[PK, Path()]):
        return await self.destroy(pk, request)

    async def put(
        self, request: Request, pk: Annotated[PK, Path()], data: _INPUT_MODEL
    ):
        return await self.update(pk, data, request)

    async def patch(
        self, request: Request, pk: Annotated[PK, Path()], data: _INPUT_MODEL
    ):
        return await self.partial_update(pk, data, request)


class ModelView(
    Generic[_INPUT_MODEL],
    RetrieveModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    CreateModelMixin,
    APIView,
):

    async def list(self, request: Request):
        return await self.list_all(request)

    async def get(self, request: Request, pk: Annotated[PK, Path()]):
        return await self.retrieve(pk, request)

    async def delete(self, request: Request, pk: Annotated[PK, Path()]):
        return await self.destroy(pk, request)

    async def post(self, request: Request, data: _INPUT_MODEL):
        return await self.create(data, request)

    async def put(
        self, request: Request, pk: Annotated[PK, Path()], data: _INPUT_MODEL
    ):
        return await self.update(pk, data, request)

    async def patch(
        self, request: Request, pk: Annotated[PK, Path()], data: _INPUT_MODEL
    ):
        return await self.partial_update(pk, data, request)
