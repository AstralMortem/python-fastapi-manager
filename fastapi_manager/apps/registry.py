import asyncio
from collections import defaultdict

from .config import AppConfig

class AppRegistry:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppRegistry, cls).__new__(cls)
        return cls._instance

    def __init__(self, installed_apps = None):
        if hasattr(self, "initialized"):
            return
        self.initialized = True

        self.apps: dict[str, AppConfig] = {}
        self.models_dict = defaultdict(dict)
        self.apps_ready = self.models_ready = self.ready = False
        self._lock = asyncio.Lock()

        if installed_apps is not None:
            self.populate(installed_apps)

    def populate(self, installed_apps):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.async_populate(installed_apps))
        loop.close()

    async def async_populate(self, installed_apps):
        if self.ready:
            return

        async with self._lock:
            if self.ready:
                return

            # phase 1. Create app configs
            for entry in installed_apps:
                app = AppConfig.create(entry)
                if app.label in self.apps:
                    raise RuntimeError(f"App {app.label} already registered")
                self.apps[app.label] = app
                app.app_registry = self
            self.apps_ready = True

            # phase 2. get models from apps
            for app in self.apps.values():
                app.import_models()
            self.models_ready = True

            # phase 3. run custom startapp
            for app in self.apps.values():
                await app.on_ready()
            self.ready = True

    def check_apps_ready(self):
        if not self.apps_ready:
            raise Exception("Apps aren't loaded yet.")

    def check_models_ready(self):
        if not self.models_ready:
            raise Exception("Models aren't loaded yet.")

    def get_app_configs(self):
        self.check_apps_ready()
        return self.apps.values()

    def get_app_config(self, app_label):
        self.check_apps_ready()
        try:
            return self.apps[app_label]
        except KeyError:
            raise LookupError(f"No installed app with label '{app_label}'.")

apps = AppRegistry(None)