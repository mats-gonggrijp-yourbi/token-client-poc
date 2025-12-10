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
                t = sc.scheduled_tick
                await sc.callback()
                sc.scheduled_tick = self.add(sc, sc.scheduled_tick)
                print((
                    f"ID: {sc.config.id} "
                    f"\nat current: {t}"
                    f"\n scheduled for: {sc.scheduled_tick}"
                    f"\nwith expiry: {sc.config.expires_in_ticks}"
                    f"\nand scale: {sc.config.scale}"
                ))
            finally:
                self.queue.task_done()

    def __init__(
            self,
            config: TimeWheelConfig,
            expected_callbacks: set[int]
        ):
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

        self.expected_callbacks = expected_callbacks
        self.received_callbacks: set[int] = set()


    def add(self, sc: ScheduledCallback, current_tick: int):
        """Add a new item to the first available slot with least occupancy."""
        assert current_tick < self.size
        assert sc.config.expires_in_ticks - self.tick_safety_margin <= self.size
        assert sc.config.expires_in_ticks > self.tick_safety_margin

        # Compute the upper boundary for the slot range
        max_offset  = sc.config.expires_in_ticks - self.tick_safety_margin

        # Keep track of the callback ID's that have been processed by this wheel
        self.received_callbacks.add(sc.config.id)

        # Always wait atleast 1 tick to execute the next callback
        wait_ticks = (
            sc.config.wait_time_in_ticks if sc.config.wait_time_in_ticks > 0 else 1
        )

        # Compute the slot range withing the upper and lower boundaries
        allowed = [
            (current_tick + i) % self.size for i in range(wait_ticks, max_offset + 1)
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

            # At every rotation check if we've completed all callbacks
            if t == (self.size - 1):
                print("current t", t, "final t", self.size -1)
                print("expected callback", self.expected_callbacks)
                print("received callbacks", self.received_callbacks)
                assert self.expected_callbacks == self.received_callbacks
                self.received_callbacks.clear()

