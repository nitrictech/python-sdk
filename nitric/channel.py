import atexit
import re
from urllib.parse import urlparse
from grpclib.client import Channel

from nitric.application import Nitric
from nitric.config import settings
from nitric.exception import NitricNotRunningException


def format_url(url: str):
    """Add the default http scheme prefix to urls without one."""
    if not re.match("^((?:http|ftp|https):)?//", url.lower()):
        return "http://{0}".format(url)
    return url


class ChannelManager:
    """A singleton class to manage the gRPC channel."""

    channel = None

    @classmethod
    def get_channel(cls) -> Channel:
        """Return the channel instance."""

        if cls.channel is None:
            cls._create_channel()
        return cls.channel  # type: ignore

    @classmethod
    def _create_channel(cls):
        """Create a new channel instance."""

        channel_url = urlparse(format_url(settings.SERVICE_ADDRESS))
        cls.channel = Channel(host=channel_url.hostname, port=channel_url.port)
        atexit.register(cls._close_channel)

    @classmethod
    def _close_channel(cls):
        """Close the channel instance."""

        if cls.channel is not None:
            cls.channel.close()
            cls.channel = None

            # If the program exits without calling Nitric.run(), it may have been a mistake.
            if not Nitric.has_run():
                print(
                    "WARNING: The Nitric application was not started. "
                    "If you intended to start the application, call Nitric.run() before exiting."
                )
