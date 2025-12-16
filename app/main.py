import asyncio
from src.scheduled_callback import ScheduledCallback, create_secret_strings
from src.load_callback_configs import load_callback_configs
from src.timewheel import TimeWheel
import psycopg
import os

async def main():
    conn = psycopg.connect(database_string)
    callbacks = [ScheduledCallback(c) for c in load_callback_configs(conn)]
    
    # Update every callback with the refresh tokens from the keyvault
    for c in callbacks:
        config = c.config
        print(f"Loading callback: {config.model_dump_json(indent=2)}\n")
        _, refresh_secret = create_secret_strings(config)
        print(f"refresh secret name: {refresh_secret}\n")
        refresh_token = await c.secret_client.get_secret(refresh_secret)
        print(f"received refresh token from keyvault: {refresh_secret}\n")
        if not refresh_token.value:
            raise RuntimeError(f"Missing refresh tokens for: {c.config}")
        
        c.config.body = c.update_fn(
            c.config.body, "refresh_token", refresh_token.value
        )
        print(f"updated request body: {c.config.body}")

    # Initialize a time wheel
    wheel = TimeWheel(base_tick=1.0, wheels=3, slots=10)

    # Schedule all callbacks
    list(map(wheel.schedule, callbacks))
    print(f"Scheduled {len(callbacks)} for timewheel")

    # Start the time wheel loop
    print("Starting wheel loop")
    wheel.start()

    # Loop untill stop is set to true
    await stop.wait()

if __name__ == "__main__":
    # main() keeps running untill stop is set to `True`
    stop = asyncio.Event()

    database_string = (
        f"postgresql://{os.getenv("POSTGRES_USER")}"
        f":{os.getenv("POSTGRES_PASSWORD")}"
        "@localhost:5432/postgres"
    )

    # Run main inside asyncio runner
    asyncio.run(main())