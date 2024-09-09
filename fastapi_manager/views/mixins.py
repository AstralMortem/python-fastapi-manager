class CreateModelMixin:
    async def create(self, data, *args, **kwargs):
        pass


class ListModelMixin:
    def list(self, *args, **kwargs):
        pass


class RetrieveModelMixin:
    def retrieve(self, *args, **kwargs):
        pass


class UpdateModelMixin:
    async def update(self, *args, **kwargs):
        pass

    async def partial_update(self, *args, **kwargs):
        pass


class DestroyModelMixin:
    async def destroy(self, *args, **kwargs):
        pass
