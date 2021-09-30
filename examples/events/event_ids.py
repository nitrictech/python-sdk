# [START import]
from nitric.api import Events, Event

# [END import]
async def events_event_ids():
    # [START snippet]
    # Create a new Event Client with default settings
    topic = Events().topic("my-topic")

    payload = {"content": "of event"}

    # Publish an event to the topic 'my-topic'
    event = await topic.publish(Event(payload=payload))


# [END snippet]
