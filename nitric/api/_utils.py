import re
from nitric.config import settings
from urllib.parse import urlparse
from grpclib.client import Channel


def format_url(url: str):
    """Add the default http scheme prefix to urls without one."""
    if not re.match("^((?:http|ftp|https):)?//", url.lower()):
        return "http://{}".format(url)
    return url


def new_default_channel():
    """Create new gRPC channel from settings."""
    channel_url = urlparse(format_url(settings.SERVICE_BIND))
    return Channel(host=channel_url.hostname, port=channel_url.port)
