# [START import]
from nitric.api import Documents
# [END import]
async def documents_sub_doc_query():
# [START snippet]
    docs = Documents()

    query = docs.collection("Customers").doc("apple").collection("Orders").query()

    results = query.fetch()
# [END snippet]
