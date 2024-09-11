from importlib import import_module

from .base import BaseCommand
from fastapi_manager.core.asgi import Application
import uvicorn
import inspect
from fastapi_manager.utils.module_loading import module_has_submodule


class RunServerCommand(BaseCommand):
    name = "runserver"

    def get_asgi(self, settings):
        project_name = settings.BASE_DIR.name
        try:
            module_path = f"{project_name}.asgi"
            mod = import_module(module_path)
            for name, obj in inspect.getmembers(mod):
                if (
                    name == "app"
                    or name == "application"
                    or isinstance(obj, Application)
                ):
                    return f"{module_path}:{name}"
        except:
            raise Exception(
                "You must set asgi.py file, and create instance application = Application() from fastapi_manager.core.asgi import Application"
            )

    def execute(
        self,
        host: str = None,
        port: int = None,
        settings: str = None,
        reloads: bool = True,
    ):
        local_host = host or "127.0.0.1"
        local_port = port or 8000
        if ":" in local_host:
            local_host, local_port = host.split(":")

        app = Application()

        from fastapi_manager.conf import settings

        uvicorn.run(
            self.get_asgi(settings),
            host=local_host,
            port=local_port,
            reload=reloads,
            reload_dirs=[settings.BASE_DIR],
        )
