import httpx
from callback_config import CallbackConfig
from urllib.parse import parse_qsl, urlencode
from typing import Any
import json
from azure.keyvault.secrets.aio import SecretClient
from azure.identity.aio import DefaultAzureCredential

def create_secret_strings(config: CallbackConfig):
    prefix = f"{config.module_alias}-{config.system_alias}-{config.instance_alias}"
    access_secret = f"{prefix}-access-token"
    refresh_secret = f"{prefix}-refresh-token"
    return access_secret, refresh_secret

def update_urlencoded(data: str, key: str, value: Any):
    d = dict(parse_qsl(data))
    d[key] = value
    return urlencode(d)

def update_json(data: str, key: str, value: Any):
    d = json.loads(data)
    d[key] = value
    return json.dumps(d)

def get_nested_value(data: dict[Any, Any], keys: list[Any]) -> Any:
    d = data
    for k in keys:
        d = d[k]
    return d

class ScheduledCallback:
    def __init__(
        self, config: CallbackConfig
    ):
        self.config = config
        self.secret_client = SecretClient(
            f"https://ybi{config.customer_alias}-kv.vault.azure.net/",
            credential=DefaultAzureCredential()
        )
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
                data: dict[Any, Any] = response.json()
                rt = get_nested_value(data, self.config.refresh_token_keys)
                at = get_nested_value(data, self.config.access_token_keys)

                # Update in-memory refresh token
                self.config.body = self.update_fn(self.config.body, "refresh_token", rt)

                acc_str, ref_str = create_secret_strings(self.config)
                await self.secret_client.set_secret(name=ref_str, value=rt)
                await self.secret_client.set_secret(name=acc_str, value=at)
                print("Updated keyvault secrets..")

            return None            

