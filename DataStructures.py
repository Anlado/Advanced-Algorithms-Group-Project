"""Data structures for the Purdue university course timetabling dataset.

Time units used throughout (from the dataset header):
  - A day has 288 slots of 5 minutes each (slot 0 = 00:00, slot 90 = 7:30 AM).
  - A week has 7 days, Monday first.
"""
from dataclasses import dataclass, field
from typing import Optional

SLOT_MINUTES = 5
SLOTS_PER_DAY = 288
NR_DAYS = 7
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@dataclass
class Room:
    id: int
    capacity: int
    location: tuple[int, int]          # (x, y) coordinates, used for travel distance
    constraint: bool = True            # False means the room may be double-booked
    discouraged: bool = False
    # Availability pattern from <sharing>: one character per `pattern_unit` slots,
    # covering the whole week. Empty means always available.
    pattern: str = ""
    pattern_unit: int = 6
    not_available_char: str = "X"
    free_for_all_char: str = "F"
    # Pattern character -> department id that may use the room at that time.
    departments: dict[str, int] = field(default_factory=dict)

    def is_available(self, day: int, start: int, length: int,
                     department: Optional[int] = None) -> bool:
        """True if the room can be used on `day` from slot `start` for `length` slots."""
        if not self.pattern:
            return True
        first = (day * SLOTS_PER_DAY + start) // self.pattern_unit
        last = (day * SLOTS_PER_DAY + start + length - 1) // self.pattern_unit
        for ch in self.pattern[first:last + 1]:
            if ch == self.not_available_char:
                return False
            if ch == self.free_for_all_char:
                continue
            if department is not None and self.departments.get(ch) != department:
                return False
        return True


@dataclass
class TimeOption:
    """One allowed meeting pattern for a section, e.g. MWF 8:30 for 50 minutes."""
    days: str            # 7-character bitmask, Monday first, e.g. "1010100" = MWF
    start: int           # start slot within the day
    length: int          # duration in slots
    break_time: int      # minutes required after the class
    pref: float          # preference (negative = preferred, positive = discouraged)

    @property
    def end(self) -> int:
        return self.start + self.length

    @property
    def day_indices(self) -> list[int]:
        return [i for i, d in enumerate(self.days) if d == "1"]

    def overlaps(self, other: "TimeOption") -> bool:
        """True if the two meeting patterns share a day and overlap in time."""
        shares_day = any(a == "1" and b == "1" for a, b in zip(self.days, other.days))
        return shares_day and self.start < other.end and other.start < self.end

    def __str__(self) -> str:
        days = "".join(DAY_NAMES[i][:2] for i in self.day_indices)
        minutes = self.start * SLOT_MINUTES
        return f"{days} {minutes // 60:02d}:{minutes % 60:02d} ({self.length * SLOT_MINUTES} min)"


@dataclass
class RoomOption:
    """One allowed room for a section, with its preference."""
    room_id: int
    pref: float


@dataclass
class Section:
    """A class (course section): the variable the solver assigns a time and room to."""
    id: int
    offering: Optional[int]          # course offering this section belongs to
    config: Optional[int]
    subpart: int                     # e.g. lecture vs. lab subpart of the course
    parent: Optional[int]            # parent section id (e.g. lab -> its lecture)
    class_limit: int                 # enrollment limit
    department: int
    dates: str                       # bitmask of semester dates the class meets
    nr_rooms: int = 1                # rooms needed (0 = no room needed)
    room_to_limit_ratio: float = 1.0 # room capacity must be >= class_limit * ratio
    committed: bool = False
    instructor_ids: list[int] = field(default_factory=list)
    times: list[TimeOption] = field(default_factory=list)
    rooms: list[RoomOption] = field(default_factory=list)

    @property
    def min_room_capacity(self) -> float:
        return self.class_limit * self.room_to_limit_ratio


@dataclass
class Instructor:
    id: int
    section_ids: list[int] = field(default_factory=list)


@dataclass
class GroupConstraint:
    """A rule between several sections, e.g. SAME_ROOM, BTB, SPREAD."""
    id: int
    type: str
    pref: str                       # "R" required, "P" prohibited, or a number (soft)
    section_ids: list[int] = field(default_factory=list)

    @property
    def is_hard(self) -> bool:
        return self.pref in ("R", "P")

    @property
    def weight(self) -> float:
        """Soft penalty weight; 0 for hard constraints."""
        return 0.0 if self.is_hard else float(self.pref)


@dataclass
class Student:
    id: int
    offerings: dict[int, float] = field(default_factory=dict)   # offering id -> weight
    prohibited_sections: set[int] = field(default_factory=set)


@dataclass
class Assignment:
    """The solver's decision for one section."""
    section_id: int
    time: TimeOption
    room_ids: list[int] = field(default_factory=list)


@dataclass
class Dataset:
    nr_days: int
    slots_per_day: int
    rooms: dict[int, Room]
    sections: dict[int, Section]
    instructors: dict[int, Instructor]
    constraints: list[GroupConstraint]
    students: list[Student]
    # offering id -> section ids, for linking student requests to sections
    offering_sections: dict[int, list[int]] = field(default_factory=dict)

    def summary(self) -> str:
        hard = sum(1 for c in self.constraints if c.is_hard)
        return "\n".join([
            f"Rooms:        {len(self.rooms)}",
            f"Sections:     {len(self.sections)}",
            f"Instructors:  {len(self.instructors)}",
            f"Constraints:  {len(self.constraints)} ({hard} hard, {len(self.constraints) - hard} soft)",
            f"Students:     {len(self.students)}",
            f"Offerings:    {len(self.offering_sections)}",
        ])
