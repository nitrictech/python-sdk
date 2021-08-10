# [START import]
from nitric.api import Storage
# [END import]
async def storage_read():
# [START snippet]
    # Construct a new storage client with default settings
    storage = Storage()

    file_ref = storage.bucket("my-bucket").file("path/to/item")

    # Read bytes from the file
    file = await file_ref.read()
# [END snippet]
