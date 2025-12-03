from typing import Callable, Coroutine, Any
from httpx import Response
from dataclasses import dataclass
import httpx

@dataclass
class ScheduledCallback:
    callback: Callable[
        [str, dict[str, str], dict[str, Any]], # args
        Coroutine[Any, Any, Response] # output
    ]
    args: dict[str, Any]
    deadline_tick: int
    ticks_to_deadline: int

async def callback(
    url: str,
    headers: dict[str, str],
    body: dict[str, Any]
) -> Response:
    async with httpx.AsyncClient() as client:
        if headers["Content-Type"] == 'application/json':
            return await client.post(url, headers=headers, json=body)
    
        elif headers["Content-Type"] == 'application/x-www-form-urlencoded':
            return await client.post(url, headers=headers, data=body)

        raise RuntimeError