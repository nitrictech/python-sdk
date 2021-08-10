# [START import]
from nitric.api import Queues, Task
# [END import]
async def queues_receive():
# [START snippet]
    # Construct a new queue client with default settings
    queue = Queues().queue("my-queue")

    # Receive tasks from the queue
    tasks = await queue.receive()
    for task in tasks:
        # Work on a task...

        # Complete the task if it was processed successfully
        task.complete()
# [END snippet]
