import httpx
# from  httpx import Response
from callback_config import CallbackConfig
# from secret_client_wrapper import SecretClientWrapper
from urllib.parse import parse_qsl, urlencode
from typing import Any
import json
from mock_secret_client import MockSecretClient

def update_urlencoded(data: str, key: str, value: Any):
    d = dict(parse_qsl(data))
    d[key] = value
    return urlencode(d)

def update_json(data: str, key: str, value: Any):
    d = json.loads(data)
    d[key] = value
    return json.dumps(d)

class ScheduledCallback:
    def __init__(
        self, auth_config: CallbackConfig, scheduled_tick: int = 0
    ):
        self.config = auth_config
        self.scheduled_tick = scheduled_tick
        self.secret_client = MockSecretClient()

        ctype = self.config.headers["Content-Type"]
        if ctype == "application/x-www-form-urlencoded":
            self.update_fn = update_urlencoded
        else:
            self.update_fn = update_json

    async def callback(self) -> dict[str, Any] | None:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=self.config.url,
                headers=self.config.headers,
                content=self.config.body
            )

            if response:
                data = response.json()
                rt = data["refresh_token"]

                # Update in-memory refresh token
                self.config.body = self.update_fn(
                    self.config.body, "refresh_token", rt
                )

                return data
            

