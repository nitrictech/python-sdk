# [START import]
from nitric.api import Documents

# [END import]
async def documents_streamed():
    # [START snippet]
    docs = Documents()

    query = docs.collection("Customers").query()

    async for doc in query.stream():
        # Process doc stream...
        print(doc.content)


# [END snippet]
