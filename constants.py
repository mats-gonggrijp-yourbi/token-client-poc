from typing import Any

EXPIRES_IN = 5
CONFIG: dict[str, dict[str, Any]] = {}
TIME_WHEEL_SIZE = 32
TIME_MARGIN = 3
NUM_WORKERS = 2
# Seconds per tick
TICK_INTERVAL = 1.0
TICKS_TO_DEADLINE = int(EXPIRES_IN // TICK_INTERVAL)

MAX_DELAY_TIME = 6.0
DELAY_CHANCE = 0.1

KV_MOCK = {
    "Hagelslag Paradijs" : {
        "YbiClientId" : "client123",
        "YbiClientSecret" : "secret123",
        "RefreshToken" : ""
    },
    "Smikkelbeertjes" : {
        "YbiClientId" : "client123",
        "YbiClientSecret" : "secret123",
        "RefreshToken" : ""
    }
}
