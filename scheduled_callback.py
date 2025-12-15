import httpx
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
        self, config: CallbackConfig
    ):
        self.config = config
        self.secret_client = MockSecretClient()
        self.due_tick = 0
        self.cancelled = False

        ctype = self.config.headers["Content-Type"]
        if ctype == "application/x-www-form-urlencoded":
            self.update_fn = update_urlencoded
        else:
            self.update_fn = update_json

    async def callback(self) -> None:
        async with httpx.AsyncClient() as client:
            headers = self.config.headers.copy()

            response = await client.post(
                url=self.config.url,
                headers=headers,
                content=self.config.body
            )

            if response:
                data = response.json()
                rt = data["refresh_token"]

                # Update in-memory refresh token
                self.config.body = self.update_fn(
                    self.config.body, "refresh_token", rt
                )
                await self.secret_client.set_secret("RefreshToken", data["refresh_token"])
                await self.secret_client.set_secret("AccessToken", data["access_token"])

            return None            

