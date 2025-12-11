from typing import Any
from time import monotonic
from asyncio import Queue, sleep, create_task, Task
from scheduled_callback import ScheduledCallback
from timewheel_config import TimeWheelConfig


class TimeWheel:
    
    def reschedule(self, sc: ScheduledCallback, executed_abs_tick: int) -> int:
        """
        Reschedule SC based on actual execution tick, preserving deadline guarantees.
        """
        current_cyclical_tick = executed_abs_tick % self.size
        return self.add(sc, current_cyclical_tick)


    async def worker(self):
        while True:
            sc = await self.queue.get()
            try:
                cb_id = sc.config.id
                expires = sc.config.expires_in_ticks
                margin = self.tick_safety_margin

                current_abs = self.current_abs_tick
                current_cyc = current_abs % self.size

                # ---- PRE-EXECUTION DEBUG ---------------------------------------
                print(
                    "\n"
                    "========== CALLBACK EXECUTION START ==========\n"
                    f"Callback ID:              {cb_id}\n"
                    f"Current ABS tick:         {current_abs}\n"
                    f"Current cyclical tick:    {current_cyc}\n"
                    f"Last execution ABS tick:  {getattr(sc, 'last_abs_execution_tick', 'N/A')}\n"
                    f"Previous deadline ABS:    {getattr(sc, 'next_abs_deadline_tick', 'N/A')}\n"
                    "------------------------------------------------"
                )

                # ---- DEADLINE CHECK --------------------------------------------
                deadline = sc.next_abs_deadline_tick
                late_threshold = deadline - margin

                if current_abs > late_threshold:
                    print(
                        f"!!! DEADLINE MISS DETECTED !!!\n"
                        f"  Current ABS tick:       {current_abs}\n"
                        f"  Deadline ABS tick:      {deadline}\n"
                        f"  Safety margin:          {margin}\n"
                        f"  Late threshold:         {late_threshold}\n"
                        f"  → Callback executed TOO LATE\n"
                    )
                else:
                    print(
                        "Deadline check:            OK\n"
                        f"  Current ABS tick:       {current_abs}\n"
                        f"  Latest allowed tick:    {late_threshold}\n"
                    )

                # ---- MARK EXECUTION TICK ---------------------------------------
                sc.last_abs_execution_tick = current_abs

                # ---- COMPUTE NEXT DEADLINE -------------------------------------
                sc.next_abs_deadline_tick = current_abs + expires
                print(
                    "Next deadline computed:\n"
                    f"  Expires in ticks:       {expires}\n"
                    f"  Next deadline ABS:      {sc.next_abs_deadline_tick}\n"
                )

                # ---- EXECUTE ---------------------------------------------------
                print("Executing callback...")
                await sc.callback()
                print("Callback execution:        DONE\n")

                # ---- RESCHEDULING ----------------------------------------------
                new_tick = self.reschedule(sc, current_abs)
                sc.scheduled_tick = new_tick

                print(
                    "Rescheduling completed:\n"
                    f"  Rescheduled cyc tick:   {new_tick}\n"
                    f"  Reschedule ABS base:    {current_abs}\n"
                    "========== CALLBACK EXECUTION END ==========\n"
                )

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

        # Async workers
        for _ in range(config.num_workers):
            self.tasks.append(create_task(self.worker()))

        # Callback tracking for checking correctness
        self.expected_callbacks = expected_callbacks
        self.received_callbacks: set[int] = set()

        # Keep track of absolute tick values to prevent time drift on slow workers
        self.current_abs_tick = 0


    def add(self, sc: ScheduledCallback, current_tick: int):
        """Add a new item to the first available slot with least occupancy."""
        assert current_tick < self.size
        assert sc.config.expires_in_ticks - self.tick_safety_margin <= self.size
        assert sc.config.expires_in_ticks > self.tick_safety_margin

        # Compute the upper boundary for the slot range
        max_offset  = sc.config.expires_in_ticks - self.tick_safety_margin
        assert max_offset < self.size

        # Keep track of the callback ID's that have been processed by this wheel
        self.received_callbacks.add(sc.config.id)

        # Always wait atleast 1 tick to execute the next callback
        wait_ticks = (
            sc.config.wait_time_in_ticks if sc.config.wait_time_in_ticks > 0 else 1
        )
        assert wait_ticks < max_offset + 1

        # Compute the slot range within the upper and lower boundaries
        allowed = [
            (current_tick + i) % self.size for i in range(wait_ticks, max_offset + 1)
        ]

        # Find the left-most minimally occupied slot within that range
        optimal = min(allowed, key=lambda t: (len(self.slots[t]), t))
        self.slots[optimal].add(sc)

        return optimal


    async def tick_loop(self):
        t = 0
        # Initial compute of the clock time for the next integer tick value
        next_tick_time = monotonic() + self.seconds_per_tick

        while True:
            print(f'\n--[TIMEWHEEL {self.scale}] tick {t} ({t * self.seconds_per_tick} seconds)-----')

            # Queue all tasks in the current slot
            for sc in self.slots[t]:
                sc.scheduled_tick = t
                await self.queue.put(sc)
            self.slots[t].clear()

            # Compute the clock time for the next integer tick value
            next_tick_time += self.seconds_per_tick
            await sleep(max(0, next_tick_time - monotonic()))

            # Increment ticks; wrap around when t > size
            self.current_abs_tick += 1
            t = self.current_abs_tick % self.size

            # At every rotation check if we've completed all callbacks
            # if t == (self.size - 1):
                # assert self.expected_callbacks == self.received_callbacks
                # self.received_callbacks.clear()

