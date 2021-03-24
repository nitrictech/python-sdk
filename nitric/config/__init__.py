"""Nitric SDK Configuration Settings."""
import os

from nitric.config import default_settings


class Settings:
    """Nitric default and env settings helper class."""

    def __init__(self):
        """Construct a new Nitric settings helper object."""
        for setting in dir(default_settings):
            default_value = getattr(default_settings, setting)
            env_variable = os.environ.get(setting)
            setattr(self, setting, env_variable or default_value)

    def __getattr__(self, name):
        return getattr(self, name)


settings = Settings()
