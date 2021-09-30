# [START import]
from nitric.api import Documents

# [END import]
async def documents_delete():
    # [START snippet]
    docs = Documents()

    document = docs.collection("products").doc("nitric")

    await document.delete()


# [END snippet]
