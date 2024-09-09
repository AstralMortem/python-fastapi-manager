from .mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    UpdateModelMixin,
)


class CreateAPIView(CreateModelMixin):
    async def post(self, data, *args, **kwargs):
        return await self.create(data, *args, **kwargs)


class ListAPIView(ListModelMixin):
    async def get(self, *args, **kwargs):
        return await self.list(*args, **kwargs)


class RetrieveAPIView(RetrieveModelMixin):
    async def get(self, *args, **kwargs):
        return await self.retrieve(*args, **kwargs)


class DestroyAPIView(DestroyModelMixin):
    async def delete(self, *args, **kwargs):
        return await self.destroy(*args, **kwargs)


class UpdateAPIView(UpdateModelMixin):
    async def put(self, *args, **kwargs):
        return await self.update(*args, **kwargs)

    async def patch(self, *args, **kwargs):
        return await self.partial_update(*args, **kwargs)


class RetrieveUpdateAPIView(RetrieveModelMixin, UpdateModelMixin):
    async def get(self, *args, **kwargs):
        return await self.retrieve(*args, **kwargs)

    async def put(self, *args, **kwargs):
        return await self.update(*args, **kwargs)

    async def patch(self, *args, **kwargs):
        return await self.partial_update(*args, **kwargs)


class RetrieveDestroyAPIView(RetrieveModelMixin, DestroyModelMixin):
    async def get(self, *args, **kwargs):
        return await self.retrieve(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        return await self.destroy(*args, **kwargs)


class RetrieveUpdateDestroyAPIView(
    RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
):

    async def get(self, *args, **kwargs):
        return await self.retrieve(*args, **kwargs)

    async def put(self, *args, **kwargs):
        return await self.update(*args, **kwargs)

    async def patch(self, *args, **kwargs):
        return await self.partial_update(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        return await self.destroy(*args, **kwargs)
