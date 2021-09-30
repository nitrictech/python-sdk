# [START import]
from nitric.api import Documents

# [END import]
async def documents_query():
    # [START snippet]
    docs = Documents()

    query = docs.collection("Customers").query()

    # Execute query
    results = await query.fetch()


# [END snippet]
