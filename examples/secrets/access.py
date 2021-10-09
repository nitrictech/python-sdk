# [START import]
from nitric.api import Secrets

# [END import]
async def secret_access():
    # [START snippet]
    # Construct a new secret client
    secrets = Secrets()

    # Access secret with specific version id
    version = "7F5F86D0-D97F-487F-A5A0-11BAAD00F777"
    value = await secrets.secret("database.password").version(version).access()

    password = value.as_string()


# [END snippet]
