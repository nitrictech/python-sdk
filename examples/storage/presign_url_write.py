# [START import]
from nitric.api import Storage
from nitric.api.storage import FileMode

# [END import]
async def storage_presign_url_write():
    # [START snippet]
    # Construct a new storage client with default settings
    storage = Storage()

    # Create a writable presigned url for the file valid for the next 3600 seconds
    await storage.bucket("my-bucket").file("path/to/item").presign_url(mode=FileMode.WRITE, expiry=3600)


# [END snippet]
