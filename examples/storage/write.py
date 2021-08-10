# [START import]
from nitric.api import Storage
# [END import]
async def storage_write():
# [START snippet]
    # Construct a new storage client with default settings
    storage = Storage()

    file_ref = storage.bucket("my-bucket").file("path/to/item")

    # Write bytes to the file
    await file_ref.write(b"example content")
# [END snippet]
