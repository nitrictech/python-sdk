from nitric.resources import schedule
from nitric.application import Nitric


# Run every 5 minutes
@schedule("process-transactions").every("5 minutes")
async def process_transactions(ctx):
    pass


Nitric.run()
