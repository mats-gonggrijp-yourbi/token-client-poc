from typing import Any
from time import monotonic
from asyncio import Queue, sleep, create_task, Task
from scheduled_callback import ScheduledCallback

MIN_WAIT_TIME = 1 # to do: per system from config 
 
class TimeWheel:
    async def worker(self):
        """ Execute sheduled callbacks from queue and reschedule new ones in wheel. """
        while True:
            sc = await self.queue.get()
            try:
                await sc.callback()
                sc.scheduled_tick = self.add(sc, sc.scheduled_tick)
                print((
                    f"Scheduled for tick {sc.scheduled_tick}"
                    f"with deadline: {sc.config.expires_in_ticks}"
                ))
            finally:
                self.queue.task_done()


    def __init__(
            self, size: int, seconds_per_tick: int, tick_margin: int, num_workers: int
        ):
        assert tick_margin >= 0

        self.slots: list[list[Any]] = [[] for _ in range(size)]
        self.size = size
        self.seconds_per_tick = seconds_per_tick
        self.queue: Queue[ScheduledCallback] = Queue()
        self.tick_margin = tick_margin
        self.tasks: list[Task[Any]] = []
        for _ in range(num_workers):
            self.tasks.append(create_task(self.worker()))


    def add(self, sc: ScheduledCallback, current_tick: int):
        """Add a new item to the first available slot with least occupancy."""
        assert current_tick < self.size
        assert sc.config.expires_in_ticks < self.size
        assert sc.config.expires_in_ticks - self.tick_margin > 0

        max_offset  = sc.config.expires_in_ticks - self.tick_margin
        allowed = [
            (current_tick + i) % self.size 
            for i in range(MIN_WAIT_TIME, max_offset + 1)
        ]
        optimal = min(allowed, key=lambda t: (len(self.slots[t]), t))
        self.slots[optimal].append(sc)

        return optimal


    async def _queue_slot(self, t: int):
        for sc in self.slots[t]:
            sc.scheduled_tick = t
            await self.queue.put(sc)
        self.slots[t].clear()


    async def _increment_tick(self, next_tick_time: float):
        diff = next_tick_time - monotonic()
        if diff > 0:
            await sleep(diff)
        return next_tick_time + self.seconds_per_tick

    
    async def tick_loop(self):
        """ Move scheduled callbacks from wheel onto queue. """
        t = 0
        next_tick_time = monotonic() + self.seconds_per_tick
        while True:
            print(f'\n----- tick {t} ({t * self.seconds_per_tick} seconds)-----')
            await self._queue_slot(t)
            next_tick_time = await self._increment_tick(next_tick_time)
            t = (t + 1) %  self.size

