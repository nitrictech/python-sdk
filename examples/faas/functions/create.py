# [START snippet]
from nitric.faas import start, HttpContext
from nitric.api import Documents
import json

from common.example import generate_id


async def handler(ctx: HttpContext) -> HttpContext:
    example = json.loads(ctx.req.body)

    doc_id = generate_id()

    await Documents().collection("examples").doc(doc_id).set(example)

    ctx.res.body = f'Created example with ID: {doc_id}'
    return ctx


if __name__ == "__main__":
    start(handler)

# [END snippet]