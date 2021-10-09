# [START import]
from nitric.api import Secrets

# [END import]
async def secret_put():
    # [START snippet]
    # Construct a new secret client
    secrets = Secrets()

    # Store the new password value, making it the latest version
    new_password = "qxGJp9rWMbYvPEsNFXzukQa!"
    new_version = await secrets.secret("database.password").put(new_password)

    # Access the exact version of the put secret, for future reference
    password = await new_version.access()


# [END snippet]
