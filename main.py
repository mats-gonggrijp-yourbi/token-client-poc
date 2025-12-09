import asyncio
from scheduled_callback import ScheduledCallback
from load_callback_config import (
    load_callback_configs_from_database,
    load_timewheel_configs_from_database
)
from timewheel import TimeWheel
from init_call import initial_call

async def main():
    timewheels: dict[str, TimeWheel] = {}

    # Create timewheel instances
    for c in load_timewheel_configs_from_database().values():
        wheel = TimeWheel(c)
        timewheels[wheel.scale] = wheel

    print(f"Initialized {len(timewheels)} timewheels.")

    # Schedule initial callbacks
    for c in load_callback_configs_from_database():
        sc = ScheduledCallback(c)
        sc.scheduled_tick = timewheels[sc.config.scale].add(sc, 0)
        await initial_call(sc, c, sc.config.url, sc.config.instance_alias)

    # Run all tick loops concurrently
    tasks = [
        asyncio.create_task(w.tick_loop())
        for w in timewheels.values()
    ]

    # TO DO: double check each timewheel coupled worker only executed 
    # it's own scope-based callbacks 

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())