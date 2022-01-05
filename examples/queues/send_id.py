# [START import]
from nitric.api import Queues, Task

# [END import]
async def queues_send():
    # [START snippet]
    # Construct a new queue client with default settings
    queues = Queues()

    payload = {"content": "of task"}

    # Publish a task to a queue
    await queues.queue("my-queue").send(Task(id="unique-task-id", payload=payload))


# [END snippet]
