from dataclasses import dataclass

@dataclass
class Timeslot:
    id: str
    day: str
    start_time: str
    duration_min: int
