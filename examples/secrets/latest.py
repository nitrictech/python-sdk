# [START import]
from nitric.api import Secrets
# [END import]
async def secret_latest():
# [START snippet]
    # Construct a new secret client
    secrets = Secrets()

    # Get latest secret version
    value = secrets.secret("my-secret").latest()
# [END snippet]
