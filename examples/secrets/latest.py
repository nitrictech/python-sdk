# [START import]
from nitric.api import Secrets
# [END import]
async def secret_latest():
# [START snippet]
    # Construct a new secret client
    secrets = Secrets()

    # Get latest secret version
    latest_version = secrets.secret("database.password").latest()

    # Access the latest secret version
    value = await latest_version.access()
# [END snippet]
