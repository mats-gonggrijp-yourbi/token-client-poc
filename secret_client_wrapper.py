from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient

class SecretClientWrapper:
    def __init__(self, url: str) -> None:
        self.cred = DefaultAzureCredential()
        self.client = SecretClient(url, self.cred)

    async def close(self) -> None:
        await self.cred.close()
        await self.client.close()

    async def get_secret(self, name: str) -> str:
        secret = await self.client.get_secret(name)
        if not (value := secret.value):
            raise ValueError(f"No value for secret: {name}")
        return value
    
    async def update_secret(self, name: str, value: str) -> None:
        await self.client.set_secret(name, value)
        return None

