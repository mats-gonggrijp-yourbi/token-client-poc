from scheduled_callback import ScheduledCallback
from asyncio import Queue
from constants import TIME_WHEEL_SIZE
from typing import Any

wheel: list[list[ScheduledCallback]] = [[] for _ in range(TIME_WHEEL_SIZE)] 
queue: Queue[ScheduledCallback] = Queue()

INITIAL_ARGS: dict[Any, Any] = {
    "url" : "http://127.0.0.1:8000/token",
    "headers" : {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic Y2xpZW50MTIzOnNlY3JldDEyMw=="
    },
    "body" : {
        "grant_type" : "refresh_token",
        "refresh_token" : ""
    }
}