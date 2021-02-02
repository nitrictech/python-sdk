class Topic(object):
    """Represents event topic metadata."""

    def __init__(self, name: str):
        """Construct a new topic instance."""
        self.name = name


class Event(object):
    """Represents a NitricEvent."""

    def __init__(self, request_id: str, payload_type: str, payload: dict):
        """Construct a new Event."""
        self.request_id = request_id
        self.payload_type = payload_type
        self.payload = payload


class FailedEvent(object):
    """Represents a failed queue publish for an event."""

    def __init__(self, event: Event, message: str):
        """Construct a new Failed Event."""
        self.event = event
        self.message = message


class QueueItem(object):
    """Represents a NitricEvents from a Queue that must be acknowledged once complete."""

    def __init__(self, event: Event, lease_id: str):
        """Constructs a new Queue Item, containing an Event."""
        self.event = event
        self.lease_id = lease_id
