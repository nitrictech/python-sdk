import os

from nitric.config import default_settings


class Settings:
    def __init__(self):
        for setting in dir(default_settings):
            default_value = getattr(default_settings, setting)
            env_variable = os.environ.get(setting)
            setattr(self, setting, env_variable or default_value)

    def __getattr__(self, name):
        return getattr(self, name)


settings = Settings()