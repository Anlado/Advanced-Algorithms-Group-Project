from dataclasses import dataclass

@dataclass
class Room:
    id: str
    capacity: int
    is_lab: bool
    building: str