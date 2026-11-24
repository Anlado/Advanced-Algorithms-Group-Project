from dataclasses import dataclass

@dataclass
class Section:
    id: str
    course_id: str
    subject_area: str
    enrollment: int
    instructor_id: str
    needs_lab: bool
    cohort_id: str
    building_pref: str
    