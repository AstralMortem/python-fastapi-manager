from typing import TypeVar, Generic, Any

from fastapi import HTTPException, Request
from fastapi_manager.db.models import Model
from abc import ABC, abstractmethod
from fastapi_manager.db.models import PK


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
    model: type[_ORM_MODEL]

    async def insert(self, data: dict[str, Any], request: Request):
        return await self.model.create(**data)

    async def get(self, pk: PK, request: Request):
        return await self.model.get(pk=pk)

    async def delete(self, pk: PK, request: Request):
        obj = await self.model.get(pk=pk)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{self.model} Not found")
        await obj.delete()
        return obj

    async def update(self, pk: PK, data: dict[str, Any], request: Request):
        obj = await self.get(pk, request)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{self.model} Not found")
        await obj.update_from_dict(data)
        await obj.save()
        return obj

    async def select(self, request: Request):
        return await self.model.filter().all()

    @property
    def orm_model(self):
        return self.model
