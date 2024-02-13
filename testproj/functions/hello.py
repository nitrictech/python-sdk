from nitric.resources import schedule
from nitric.resources import start


# Run every 5 minutes
@schedule("process-transactions", every="5 minutes")
async def process_transactions(ctx):
    pass


Nitric.run()
