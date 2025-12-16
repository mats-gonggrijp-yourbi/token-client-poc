import httpx
from callback_config import CallbackConfig
from urllib.parse import parse_qsl, urlencode
from typing import Any
import json
from azure.keyvault.secrets.aio import SecretClient
from azure.identity.aio import DefaultAzureCredential
# from mock_secret_client import MockSecretClient

def create_secret_strings(config: CallbackConfig):
    prefix = f"{config.module_alias}-{config.system_alias}-{config.instance_alias}"
    access_secret = f"{prefix}-access-token"
    refresh_secret = f"{prefix}-refresh-token"
    return access_secret, refresh_secret

def _update_urlencoded(data: str, key: str, value: Any):
    d = dict(parse_qsl(data))
    d[key] = value
    return urlencode(d)

def _update_json(data: str, key: str, value: Any):
    d = json.loads(data)
    d[key] = value
    return json.dumps(d)

def _get_nested_value(data: dict[Any, Any], keys: list[Any]) -> Any:
    d = data
    for k in keys:
        d = d[k]
    return d

class ScheduledCallback:
    def __init__(self, config: CallbackConfig):
        self.config = config
        self.secret_client = SecretClient(
            f"https://ybi{config.customer_alias}-kv.vault.azure.net/",
            credential=DefaultAzureCredential()
        )
        # self.secret_client = MockSecretClient()
        self.due_tick = 0
        self.cancelled = False

        # Select what update function is necessary to update the request body
        ctype = self.config.headers["Content-Type"]
        if ctype == "application/x-www-form-urlencoded":
            self.update_fn = _update_urlencoded
        else:
            self.update_fn = _update_json

    async def callback(self) -> None:
        async with httpx.AsyncClient() as client:
            # Call the authorization endpoint
            print(f"Executing callback for customer {self.config.customer_alias}")
            response = await client.post(
                url=self.config.url,
                headers=self.config.headers,
                content=self.config.body
            )

            print(f"Response status: {response.status_code}")

            if response.status_code > 299:
                print(f"Response error: {response.text}")
                raise RuntimeError("Callback generated a response error")

            if response:
                # Get the refresh and access tokens from the data
                data: dict[Any, Any] = response.json()
                print(f"Received data: {data}")
                rt: str = _get_nested_value(data, self.config.refresh_token_keys)
                at: str = _get_nested_value(data, self.config.access_token_keys)

                print(
                    f"Received new access and refresh tokens: {rt[:5]}..., {at[:5]}...\n"
                )

                # Update the refresh token in the request body 
                self.config.body = self.update_fn(self.config.body, "refresh_token", rt)

                print(f"Updated request body with new refresh token\n")

                # Update the keyvault with the new access and refresh tokens
                acc_str, ref_str = create_secret_strings(self.config)
                await self.secret_client.set_secret(name=ref_str, value=rt)
                await self.secret_client.set_secret(name=acc_str, value=at)

                print("Updated keyvault with new refresh and access tokens")

            return None            

