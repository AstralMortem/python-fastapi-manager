from collections.abc import Callable
from typing import Optional, Union, List
from fastapi import FastAPI
from fastapi_manager.conf import settings
from .lifespan import global_lifespan


class Application(FastAPI):
    """
    Main application class, just wrapper on FastAPI class, but
    with defaults set from global_settings and global_lifespan.
    """

    def __init__(
        self,
        lifespan: Optional[Union[List[Callable], Callable]] = None,
        *args,
        **kwargs
    ) -> None:
        self.user_lifespan = lifespan

        super().__init__(
            lifespan=global_lifespan(self.user_lifespan),
            title=settings.PROJECT_TITLE,
            version=settings.PROJECT_VERSION,
            root_path=settings.PROJECT_ROOT_PATH,
            debug=settings.DEBUG,
            *args,
            **kwargs
        )
