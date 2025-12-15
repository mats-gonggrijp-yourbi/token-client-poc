import asyncio

RESPONSE_TIME = 0.1

class MockSecretClient:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    async def get_secret(self, name: str) -> str | None:
        await asyncio.sleep(RESPONSE_TIME)
        return self.data.get(name, "DUMMY VALUE FOR TESTING")
    
    async def set_secret(self, name: str, value: str) -> None:
        await asyncio.sleep(RESPONSE_TIME)
        self.data[name] = value
        return None