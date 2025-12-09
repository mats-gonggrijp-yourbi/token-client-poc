from pydantic import BaseModel

class TimeWheelConfig(BaseModel):
    id: int
    scale: str
    size: int
    seconds_per_tick: int
    tick_safety_margin: int
    num_workers: int
