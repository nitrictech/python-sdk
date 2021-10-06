# [START import]
from typing import List
from nitric.api import Queues, Task
from nitric.api.queues import FailedTask
# [END import]
async def queues_failed():
# [START snippet]
    # Construct a new queue client with default settings 
    queues = Queues()

    payload = {"content": "of task"}

    # Publish tasks to queue
    failed_task = await queues.queue("my-queue").send([Task(payload=payload) for i in range(2)])
    
    # Process the failed task
    for task in failed_task:
      print(task.message)
# [END snippet]