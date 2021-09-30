# [START import]
from nitric.api import Documents

# [END import]
async def documents_set():
    # [START snippet]
    docs = Documents()

    document = docs.collection("products").doc("nitric")

    await (
        document.set(
            {
                "id": "nitric",
                "name": "Nitric Framework",
                "description": "A development framework",
            }
        )
    )


# [END snippet]
