from fastapi import APIRouter

from fastapi_manager.router import BaseRouter


class BaseView:

    def __init__(self, prefix, router_conf: dict):
        self.router = APIRouter(prefix=prefix, **router_conf)
