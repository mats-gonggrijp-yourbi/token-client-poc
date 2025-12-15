from pydantic import BaseModel

class TimeWheelConfig(BaseModel):
    base_tick: float
    wheels: int
    slots: int