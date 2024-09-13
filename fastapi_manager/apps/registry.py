import asyncio
import warnings
from collections import defaultdict

from .config import AppConfig


class AppRegistry:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppRegistry, cls).__new__(cls)
        return cls._instance

    def __init__(self, installed_apps=None):
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
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # loop.run_until_complete(self.async_populate(installed_apps))
        # loop.close()
        asyncio.run(self.async_populate(installed_apps))

    async def async_populate(self, installed_apps):
        if self.ready:
            return

        async with self._lock:
            if self.ready:
                return

            # phase 1. Create app configs
            for entry in installed_apps:
                if isinstance(entry, AppConfig):
                    app = entry
                else:
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

    def to_dict(self):
        return {app.label: app.models for app in self.get_app_configs()}

    def register_model(self, app_label, model):
        # Since this method is called when models are imported, it cannot
        # perform imports because of the risk of import loops. It mustn't
        # call get_app_config().
        model_name = model._meta.model_name
        app_models = self.models_dict[app_label]
        if model_name in app_models:
            if (
                model.__name__ == app_models[model_name].__name__
                and model.__module__ == app_models[model_name].__module__
            ):
                warnings.warn(
                    "Model '%s.%s' was already registered. Reloading models is not "
                    "advised as it can lead to inconsistencies, most notably with "
                    "related models." % (app_label, model_name),
                    RuntimeWarning,
                    stacklevel=2,
                )
            else:
                raise RuntimeError(
                    "Conflicting '%s' models in application '%s': %s and %s."
                    % (model_name, app_label, app_models[model_name], model)
                )
        app_models[model_name] = model

    def get_containing_app_config(self, object_name):
        """
        Look for an app config containing a given object.

        object_name is the dotted Python path to the object.

        Return the app config for the inner application in case of nesting.
        Return None if the object isn't in any registered app config.
        """
        self.check_apps_ready()
        candidates = []
        for app_config in self.apps.values():
            if object_name.startswith(app_config.name):
                subpath = object_name.removeprefix(app_config.name)
                if subpath == "" or subpath[0] == ".":
                    candidates.append(app_config)
        if candidates:
            return sorted(candidates, key=lambda ac: -len(ac.name))[0]


apps = AppRegistry(None)
