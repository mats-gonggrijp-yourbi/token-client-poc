import asyncio
from scheduled_callback import ScheduledCallback
from load_callback_config import load_config_from_database
from timewheel import TimeWheel
from init_call import initial_call

# Constants
TIME_WHEEL_SIZE = 30
TICK_MARGIN = 1
NUM_WORKERS = 100
SECONDS_PER_TICK = 1

async def main():
    timewheel = TimeWheel(TIME_WHEEL_SIZE, SECONDS_PER_TICK, TICK_MARGIN, NUM_WORKERS) 
    configs = load_config_from_database()
    for c in configs:
        print("Loading config..")
        sc = ScheduledCallback(c)
        sc.scheduled_tick = timewheel.add(sc, 0)
        await initial_call(sc, c, sc.config.url, sc.config.instance_alias)
    print(f"Loaded {len(configs)} configs")
    await timewheel.tick_loop()

if __name__ == "__main__":
    asyncio.run(main())