import httpx
from  httpx import Response
from auth_config import AuthConfig
import re

class ScheduledCallback:
    def __init__(
        self, auth_config: AuthConfig, scheduled_tick: int
    ):
        self.auth_config = auth_config
        self.scheduled_tick = scheduled_tick

    async def callback(self) -> Response:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=self.auth_config.url,
                headers=self.auth_config.headers,
                content=self.auth_config.body
            )

            if response:
                data = response.json()
                self.auth_config.body = re.sub(
                    pattern=r"refresh_token=[^&]*",
                    repl=f"refresh_token={data["refresh_token"]}",
                    string=self.auth_config.body
                )
                # TO DO: put the access token in the key-vault
                # data['access_token'] -> customer keyvault
            return response
