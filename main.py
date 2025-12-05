import asyncio
import time
from scheduled_callback import ScheduledCallback
from database_connection import load_config_from_database
from timewheel import TimeWheel
from init_call import initial_call

# Constants
TIME_WHEEL_SIZE = 30
TIME_MARGIN = 1
NUM_WORKERS = 1
SECONDS_PER_TICK = 5.0

# Global variables
timewheel = TimeWheel(TIME_WHEEL_SIZE) 
callback_queue: asyncio.Queue[ScheduledCallback] = asyncio.Queue()

async def worker():
    """ Execute sheduled callbacks from queue and reschedule new ones in wheel. """
    while True:
        sc = await callback_queue.get()
        try:
            # Update the fresh and access tokens 
            data = await sc.callback()
            if data:
                await sc.secret_client.set_secret("RefreshToken", data["refresh_token"])
                await sc.secret_client.set_secret("AccessToken", data["access_token"])

            # Add the scheduled callback to the wheel again
            sc.scheduled_tick = timewheel.add(
                sc, sc.scheduled_tick, sc.config.expires_in, TIME_MARGIN
            )
            print(f"Scheduled for tick {sc.scheduled_tick} with deadline: {sc.config.expires_in}")

        finally:
            callback_queue.task_done()


async def queue_slot(t: int):
    for sc in timewheel.slots[t]:
        sc.scheduled_tick = t
        print("Queueing for tick: ", t)
        await callback_queue.put(sc)
    timewheel.slots[t].clear()

async def increment_tick(t: int, next_tick_time: float):
    now = time.monotonic()
    diff = next_tick_time - now
    if diff > 0:
        await asyncio.sleep(diff)
    t = (t + 1) %  TIME_WHEEL_SIZE
    next_tick_time += SECONDS_PER_TICK


async def tick_loop():
    """ Move scheduled callbacks from wheel onto queue. """
    t = 0
    next_tick_time = time.monotonic() + SECONDS_PER_TICK

    while True:
        print(f'\n----- tick {t} ({t * SECONDS_PER_TICK} seconds)-----')

        # Queue the values in wheel slot t
        await queue_slot(t)

        # Increment tick by sleeping untill next time interval
        await increment_tick(t, next_tick_time)


async def main():
    for _ in range(NUM_WORKERS):
        asyncio.create_task(worker())

    # Configs per callback are stored in the database
    configs = load_config_from_database()

    # Create a scheduled callback for each config
    for c in configs:
        sc = ScheduledCallback(c)
        sc.scheduled_tick = timewheel.add(
            sc, 0, sc.config.expires_in, TIME_MARGIN
        )
        # Get initial refresh token from auth server (this would be manual)
        await initial_call(sc, c, sc.config.url, sc.config.instance_alias)

    print(f"Loaded {len(configs)} configs")

    await tick_loop()

if __name__ == "__main__":
    asyncio.run(main())