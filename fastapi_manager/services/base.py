from typing import TypeVar, Generic

from fastapi import HTTPException, Request
from fastapi_manager.db.models import Model
from abc import ABC, abstractmethod


_ORM_MODEL = TypeVar("_ORM_MODEL", bound=Model)


class AbstractService(ABC):

    @abstractmethod
    async def insert(self, data, request):
        raise NotImplementedError

    @abstractmethod
    async def select(self, request):
        raise NotImplementedError

    @abstractmethod
    async def update(self, pk, data, request):
        raise NotImplementedError

    @abstractmethod
    async def delete(self, pk, request):
        raise NotImplementedError

    @abstractmethod
    async def get(self, pk, request):
        raise NotImplementedError


class BaseService(Generic[_ORM_MODEL], AbstractService):
    _model: type[_ORM_MODEL]

    async def insert(self, data: dict, request: Request):
        return await self._model.create(**data)

    async def get(self, pk, request: Request):
        return await self._model.get(pk=pk)

    async def delete(self, pk, request: Request):
        obj = await self._model.get(pk=pk)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{self._model} Not found")
        await obj.delete()
        return obj

    async def update(self, pk, data, request: Request):
        obj = await self.get(pk, request)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{self._model} Not found")
        await obj.update_from_dict(data)
        await obj.save()
        return obj

    async def select(self, request: Request):
        return await self._model.filter().all()

    @property
    def model(self):
        return self._model
