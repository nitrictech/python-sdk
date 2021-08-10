# [START import]
from nitric.api import Storage
# [END import]
async def storage_delete():
# [START snippet]
    # Construct a new storage client with default settings
    storage = Storage()

    # Delete the file
    await storage.bucket("my-bucket").file("path/to/item").delete()
# [END snippet]
