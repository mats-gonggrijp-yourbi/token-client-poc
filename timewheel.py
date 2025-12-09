from typing import Any
from time import monotonic
from asyncio import Queue, sleep, create_task, Task
from scheduled_callback import ScheduledCallback
from timewheel_config import TimeWheelConfig

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


    def __init__(self, config: TimeWheelConfig):
        assert config.tick_safety_margin >= 0
        assert config.tick_safety_margin >= 0
        assert config.num_workers > 0

        # Config
        self.size = config.size
        self.seconds_per_tick = config.seconds_per_tick
        self.scale = config.scale
        self.tick_safety_margin = config.tick_safety_margin
        self.num_workers = config.num_workers

        # Data
        self.slots: list[set[ScheduledCallback]] = [set() for _ in range(config.size)]
        self.queue: Queue[ScheduledCallback] = Queue()
        self.tasks: list[Task[Any]] = []

        for _ in range(config.num_workers):
            self.tasks.append(create_task(self.worker()))


    def add(self, sc: ScheduledCallback, current_tick: int):
        """Add a new item to the first available slot with least occupancy."""
        assert current_tick < self.size
        assert sc.config.expires_in_ticks < self.size
        assert sc.config.expires_in_ticks > self.tick_safety_margin

        # Compute the upper boundary for the slot range
        max_offset  = sc.config.expires_in_ticks - self.tick_safety_margin
        assert max_offset > sc.config.wait_time_in_ticks 

        # Compute the slot range withing the upper and lower boundaries
        allowed = [
            (current_tick + i) % self.size 
            for i in range(sc.config.wait_time_in_ticks, max_offset + 1)
        ]

        # Find the left-most minimally occupied slot within that range
        optimal = min(allowed, key=lambda t: (len(self.slots[t]), t))
        self.slots[optimal].add(sc)

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
        t = 0
        # Initial compute of the clock time for the next integer tick value
        next_tick_time = monotonic() + self.seconds_per_tick

        while True:
            print(f'\n--[TIMEWHEEL {self.scale}] tick {t} ({t * self.seconds_per_tick} seconds)-----')

            # Queue all tasks in the current slot
            await self._queue_slot(t)

            # Compute the clock time for the next integer tick value
            next_tick_time = await self._increment_tick(next_tick_time)

            # Increment ticks; wrap around when t > size
            t = (t + 1) %  self.size

