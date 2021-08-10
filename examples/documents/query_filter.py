# [START import]
from nitric.api import Documents
# [END import]
async def documents_query_filter():
# [START snippet]
    docs = Documents()

    query = docs.collection("Customers").query().where("country", "==", "US").where("age", ">=", 21)

    results = query.fetch()
# [END snippet]
