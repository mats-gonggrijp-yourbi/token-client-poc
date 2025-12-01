from typing import Any

CONFIG: dict[str, dict[str, Any]] = {}
TIME_WHEEL_SIZE = 32
TIME_MARGIN = 3
NUM_WORKERS = 2
TICK_INTERVAL = 1.0

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
