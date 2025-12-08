from typing import Any

MIN_WAIT_TIME = 1 # to do: per system from config 
 
class TimeWheel:
    def __init__(self, size: int) -> None:
        self.slots: list[list[Any]] = [[] for _ in range(size)]
        self.size = size

    def add(
        self, item: Any, current_tick: int, deadline: int, safety_margin: int
    ):
        """Add a new item to the first available slot with least occupancy."""
        assert current_tick in range(0, self.size)
        assert deadline < self.size
        assert safety_margin >= 0
        assert safety_margin < deadline
        assert deadline - safety_margin > 0
        
        max_offset  = deadline - safety_margin
        allowed = [(current_tick + i) % self.size for i in range(MIN_WAIT_TIME, max_offset + 1)]
        optimal = min(allowed, key=lambda t: (len(self.slots[t]), t))
        self.slots[optimal].append(item)

        return optimal

def test():
    from random import randint
    margin = 1
    MIN_SIZE = 4
    MAX_SIZE = 10

    for _ in range(10):
        size = randint(MIN_SIZE, MAX_SIZE)
        wheel = TimeWheel(size)

        for _ in range(10):
            deadline = randint(margin + 1, size - 1)
            wheel.add(deadline, 0, deadline, margin)

        print(wheel.slots, '\n\n')

        for t, slot in enumerate(wheel.slots):
            assert t not in slot # type: ignore


if __name__ == "__main__":
    test()
