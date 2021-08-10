# [START import]
from nitric.api import Documents
# [END import]
async def documents_query_limits():
# [START snippet]
    docs = Documents()

    query = docs.collection("Customers").collection("Orders").query().limit(1000)

    results = query.fetch()
# [END snippet]
