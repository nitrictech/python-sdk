from nitric.resources import api, kv
from nitric.application import Nitric
from nitric.context import HttpContext


users = kv("test").allow("get", "set")

public = api("test")

print("this should print")


# Run every 5 minutes
@public.get("/test/:thing")
async def process_transactions(ctx: HttpContext):
    """Process transactions."""
    ctx.res.body = b"Hello, world!"
    thing = ctx.req.params["thing"]
    await users.set(thing, {"thing": ctx.req.params["thing"]})
    out = await users.get(thing)
    print(out)


Nitric.run()
