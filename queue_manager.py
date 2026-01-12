import asyncio

class UploadQueue:
    def __init__(self, concurrency=3):
        self.queue = asyncio.Queue()
        self.concurrency = concurrency

    async def worker(self, handler):
        while True:
            item = await self.queue.get()
            try:
                await handler(item)
            finally:
                self.queue.task_done()

    async def start(self, handler):
        for _ in range(self.concurrency):
            asyncio.create_task(self.worker(handler))

    async def push(self, item):
        await self.queue.put(item)
