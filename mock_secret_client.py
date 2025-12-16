import asyncio
from dataclasses import dataclass

RESPONSE_TIME = 0.1

@dataclass
class MockSecret:
    value: str

class MockSecretClient:
    def __init__(self) -> None:
        self.data: dict[str, MockSecret] = {}

    async def get_secret(self, name: str) -> MockSecret:
        await asyncio.sleep(RESPONSE_TIME)
        dummy_secret = MockSecret(value="DUMMY VALUE FOR TESTING")
        return self.data.get(name, dummy_secret)
    
    async def set_secret(self, name: str, value: str) -> None:
        await asyncio.sleep(RESPONSE_TIME)
        self.data[name] = MockSecret(value=value)
        return None