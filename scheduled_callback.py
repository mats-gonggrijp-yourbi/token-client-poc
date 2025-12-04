import httpx
from  httpx import Response
from auth_config import AuthConfig
from secret_client_wrapper import SecretClientWrapper
from urllib.parse import parse_qsl, urlencode
from typing import Any
import json

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
        self, auth_config: AuthConfig, scheduled_tick: int
    ):
        self.auth_config = auth_config
        self.scheduled_tick = scheduled_tick
        self.secret_client = SecretClientWrapper(
            f"https://ybi{auth_config.customer_alias}-kv.vault.azure.net/"
        )

        ctype = self.auth_config.headers["Content-Type"]
        if ctype == "application/x-www-form-urlencoded":
            self.update_fn = update_urlencoded
        else:
            self.update_fn = update_json

    async def callback(self) -> Response:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=self.auth_config.url,
                headers=self.auth_config.headers,
                content=self.auth_config.body
            )

            if response:
                data = response.json()
                at = data["access_token"]
                rt = data["refresh_token"]

                # Update keyvault access and refresh tokens
                await self.secret_client.update_secret("RefreshToken", rt)
                await self.secret_client.update_secret("AccessToken", at)
                print("Callback done..")

                # Update in-memory refresh token
                print("Updating refresh token: ", self.auth_config.body)
                self.auth_config.body = self.update_fn(
                    self.auth_config.body, "refresh_token", rt
                )
                print("Updated refresh token: ", self.auth_config.body)


            return response
