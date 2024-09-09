from fastapi import HTTPException, Request
from fastapi_manager.db.models import Model


class BaseService:
    _model: type[Model] = None

    async def create(self, data: dict, request: Request):
        return await self._model.create(**data)

    async def get(self, pk, request: Request):
        return await self._model.get(pk=pk)

    async def delete(self, pk, request: Request):
        return await self._model.filter(pk=pk).delete()

    async def update(self, pk, data, request: Request):
        obj = await self.get(pk, request)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{self._model} Not found")
        await obj.update_from_dict(data)
        await obj.save()
        return obj

    async def list(self, request: Request):
        return await self._model.filter().all()

    async def get_all(self, request: Request):
        return await self.list(request)

    @property
    def model(self):
        return self._model
