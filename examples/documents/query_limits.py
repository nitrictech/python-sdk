# [START import]
from nitric.api import Documents
# [END import]
async def documents_query_limits():
# [START snippet]
    docs = Documents()

    query = docs.collection("Customers").query().limit(1000)

    results = await query.fetch()
# [END snippet]
