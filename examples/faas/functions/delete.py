# [START snippet]
from nitric.faas import start, HttpContext
from nitric.api import Documents
from nitric.api.exception import NotFoundException, NitricServiceException


async def handler(ctx: HttpContext) -> HttpContext:

    # get id param from HTTP request path
    try:
        doc_id = ctx.path.split("/")[-1]
    except IndexError:
        ctx.res.status = 400
        ctx.res.body = "Invalid request"
        return ctx

    try:
        await Documents().collection("examples").doc(doc_id).delete()
        ctx.res.body = "Removed example " + doc_id
    except NotFoundException:
        ctx.res.status = 404
        ctx.res.body = "Example not found"
    except NitricServiceException:
        ctx.res.status = 500
        ctx.res.body = "An unexpected error occurred"
    return ctx 


if __name__ == "__main__":
    start(handler)

# [END snippet]