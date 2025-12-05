import asyncio

# Typical azure keyvault response times
WAIT_TIME = 1.0

# TO DO: when wait time on external services is too large it breaks everything 
#   -> need safe margins and failure mitigation tactics

class MockSecretClient:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    async def get_secret(self, name: str) -> str | None:
        await asyncio.sleep(WAIT_TIME)
        return self.data.get(name, None)
    
    async def set_secret(self, name: str, value: str) -> None:
        await asyncio.sleep(WAIT_TIME)
        self.data[name] = value
        return None