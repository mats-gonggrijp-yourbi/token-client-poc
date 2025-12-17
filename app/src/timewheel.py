import asyncio
import math
from src.scheduled_callback import ScheduledCallback
from time import monotonic
from datetime import datetime 

class TimeWheel:
    """
    A class that implements a hierarchical timewheel datastructure
    
    Holds methods for running the tick loop and scheduling actions based on deadlines

    Holds actions at different levels of time-granularity
    (i.e. seconds, minutes, hours, etc.) and executes them based on their remaining time

    Actions that are far away get put into course slots and gradually cascade down to
    the lowest level where they are executed

    Actions get automatically rescheduled immediately after execution unless cancelled
    """
    def __init__(self, base_tick: float = 0.1, wheels: int = 4, slots: int = 256):
        # The global tick rate in seconds
        self.base_tick = base_tick
        # The number of slots per wheel (level)
        self.slots = slots
        # The number of levels (wheels) in the hierarchy
        self.levels = wheels
        self.current_tick = 0

        # Each wheel is a list of slots, each slot contains multiple actions
        self.wheels: list[list[list[ScheduledCallback]]] = [
            [[] for _ in range(slots)] for _ in range(wheels)
        ]
        self.running = False
        self._task = None
        self.last_executed = 0.0
        self.monotonic = 0.0

    def start(self):
        """Start running the tick loop"""
        if self.running:
            return
        self.running = True
        self._task = asyncio.create_task(self._loop())

    def stop(self):
        """ Stop running the tick loop"""
        self.running = False
        if self._task:
            self._task.cancel()

    async def _loop(self):
        """Increment current tick by one per tick rate and call self._advance()"""
        try:
            while self.running:
                next_tick_time = monotonic() + self.base_tick
                self._advance()
                await asyncio.sleep(max(0, next_tick_time - monotonic()))
                self.current_tick += 1
                if self.current_tick % 15 == 0:
                    print(f"--time: {datetime.now().strftime("%H:%M:%S")} | tick: {self.current_tick}--")

        finally:
            self.running = False

    def schedule(self, action: ScheduledCallback):
        """Compute the due tick based on the deadline and add the action"""
        # Compute how many ticks untill the deadline— never run earlier than deadline
        ticks = max(1, math.ceil(action.config.expires_in_seconds / self.base_tick))

        # Add the action to the wheel with that deadline in ticks
        action.due_tick = self.current_tick + ticks

        print(f"Scheduled new callback for tick {action.due_tick}")

        self._add(action)

    def cancel(self, action: ScheduledCallback):
        """ Cancel the action """
        action.cancelled = True

    def _add(self, action: ScheduledCallback):
        """
        Puts actions into buckets at level and index based on time left untill due

        Actions with less time left get put into lower level buckets

        If the action is scheduled for the current tick or earlier (missed deadline),
        place it in level 0 slot 0 for immediate execution.
        """
        # Compute how much ticks are left until the action is due
        diff = action.due_tick - self.current_tick

        # Execute now
        if diff <= 0:
            self.wheels[0][0].append(action)
            return 

        # Compute the total maximum range in ticks over all levels and slots
        max_range = self.slots ** self.levels

        # If the time left is greater than the wheels range, cap it at size - 1
        if diff >= max_range:
            diff = max_range - 1
            action.due_tick = self.current_tick + diff

        # Go through all levels and check if the ticks left are within the scale
        for level in range(self.levels):
            # If ticks left is within the level's scale boundary we add it to that level
            if diff < self.slots ** (level + 1):
                # span = num(ticks) / slot
                span: int = self.slots ** level
                # int(floor(due/span)) % size
                idx = (action.due_tick // span) % self.slots
                self.wheels[level][idx].append(action)
                break

    def _advance(self):
        """
        Advance the wheel by executing tasks at level 0 or re-adding at higher levels
        
        Actions in higher levels cascade down when ticks pass slot boundaries in levels
        """
        for level in reversed(range(self.levels)):
            span = self.slots ** level
            if self.current_tick % span != 0:
                continue

            idx: int = (self.current_tick // span) % self.slots
            bucket = self.wheels[level][idx]
            if not bucket:
                continue

            self.wheels[level][idx] = []

            if level == 0:
                for action in bucket:
                    if action.cancelled:
                        continue
                    if action.due_tick <= self.current_tick:
                        asyncio.create_task(self._exec(action))
                    else:
                        self._add(action)
            else:
                for action in bucket:
                    if action.cancelled:
                        continue
                    self._add(action)

    async def _exec(self, action: ScheduledCallback):
        """ Execute and reschedule the action """
        try:
            if action.due_tick <= self.current_tick:
                await action.callback()

                current_time = monotonic()
                if current_time > (self.last_executed + action.config.expires_in_seconds + 5.0):
                    print("!! Execution more than 5 seconds past monotonic deadline !!\n")
                self.last_executed = current_time

                print(f"Executed for due tick: {action.due_tick} at current tick: {self.current_tick}")

        finally:
            if not action.cancelled:
                self.schedule(action)
