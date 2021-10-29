# [START import]
from nitric.api import Documents

# [END import]
async def documents_sub_col_query():
    # [START snippet]
    docs = Documents()

    query = docs.collection("Customers").collection("Orders").query()

    results = await query.fetch()


# [END snippet]
