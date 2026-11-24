
from dataclasses import dataclass

@dataclass
class Instructor:
    # Unique instructor identifier
    id: str

    # Instructor's first
    first_name: str

    # Instructor's last name
    last_name: str

    # Courses or subject areas they're qualified to teach
    domains: set[str]

    # Timeslots when they cannot teach
    unavailable_slots: set[str]

    # Additional timeslots that must remain free
    required_no_teach_slots: set[str]

    # Timeslots they would prefer to teach
    preferred_slots: set[str]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
