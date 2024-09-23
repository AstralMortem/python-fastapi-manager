from importlib import import_module
from fastapi_manager.core.asgi import Application
import uvicorn
import inspect
from fastapi_manager.core.cli.typer import AsyncTyper

cli = AsyncTyper()


def get_asgi(settings):
    """
    find asgi module, and Application instance inside, return string for uvicorn
    """
    project_name = settings.BASE_DIR.name
    try:
        module_path = f"{project_name}.asgi"
        mod = import_module(module_path)
        for name, obj in inspect.getmembers(mod):
            if name == "app" or name == "application" or isinstance(obj, Application):
                return f"{module_path}:{name}"
    except:
        raise Exception(
            "You must set asgi.py file, and create instance application = Application() from fastapi_manager.core.asgi import Application"
        )


@cli.command()
def runserver(
    host: str = None,
    port: int = None,
    settings: str = None,
    reloads: bool = True,
):
    local_host = host or "127.0.0.1"
    local_port = port or 8000
    if ":" in local_host:
        local_host, local_port = host.split(":")

    from fastapi_manager.conf import settings

    uvicorn.run(
        get_asgi(settings),
        host=local_host,
        port=local_port,
        reload=reloads,
        reload_dirs=[settings.BASE_DIR],
    )
