# [START import]
from nitric.api import Documents

# [END import]
async def documents_get():
    # [START snippet]
    docs = Documents()

    document = docs.collection("products").doc("nitric")

    product = await document.get()


# [END snippet]
