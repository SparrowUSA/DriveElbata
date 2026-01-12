import asyncio


class UploadQueue:
    def __init__(self, concurrency=3):
        self.queue = asyncio.Queue()
        self.concurrency = concurrency
        self.paused = False
        self.total_uploaded = 0
        self.total_failed = 0

    async def worker(self, handler):
        while True:
            item = await self.queue.get()

            # pause handling
            while self.paused:
                await asyncio.sleep(1)

            try:
                await handler(item)
                self.total_uploaded += 1
            except Exception:
                self.total_failed += 1
            finally:
                self.queue.task_done()

    async def start(self, handler):
        for _ in range(self.concurrency):
            asyncio.create_task(self.worker(handler))

    async def push(self, item):
        await self.queue.put(item)

    async def clear(self):
        while not self.queue.empty():
            self.queue.get_nowait()
            self.queue.task_done()

    def pending(self):
        return self.queue.qsize()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
