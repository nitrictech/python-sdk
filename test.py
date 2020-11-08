from nitric.sdk.v1 import EventingClient
from nitric.sdk.v1 import StorageClient

event_client = EventingClient()
print(str(event_client.publish('test', {'test': 'ing'})))
print(str(event_client.get_topics()))

storage_client = StorageClient()
print(str(storage_client.put("mr.bucket", "water.txt", b'test content for mr.bucket')))
print(str(storage_client.get("mr.bucket", "water.txt")))
