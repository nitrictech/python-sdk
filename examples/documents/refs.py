# [START import]
from nitric.api import Documents
# [END import]
def documents_refs():
# [START snippet]
  docs = Documents()

  # create a reference to a collection named 'products'
  products = docs.collection("products")

  # create a reference to a document with the id 'nitric'
  nitric = products.doc("nitric")
# [END snippet]
