
import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT = Path("data/university")
RANDOM_SEED = 42
rng = random.Random(RANDOM_SEED)

NUM_COHORTS = 105
COURSES_PER_COHORT = 5
INSTRUCTORS_PER_DEPARTMENT = 15
NUM_ROOMS = 100
NUM_LAB_ROOMS = 25

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
START_HOUR = 8
END_HOUR = 20

# These are synthetic departments, not KSU's official
# organizational structure.
DEPARTMENTS = {
    "CS": "ENG",
    "MATH": "SCI",
    "BIOL": "SCI",
    "CHEM": "SCI",
    "PHYS": "SCI",
    "ENGL": "HUM",
    "HIST": "HUM",
    "PSYC": "SOC",
    "ECON": "BUS",
    "BUS": "BUS",
    "COMM": "HUM",
    "ART": "ART",
}

# Departments where some courses require laboratory rooms.
LAB_DEPARTMENTS = {"CS", "BIOL", "CHEM", "PHYS"}

# Repeated exactly 21 times:
# 21 * (60 + 80 + 100 + 120 + 140) = 10,500 students.
COHORT_SIZES = [60, 80, 100, 120, 140] * 21

# ============================================================
# HELPERS
# ============================================================

def write_csv(filename, headers, rows):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / filename

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)

    return path


def serialize_slots(slots):
    return ";".join(
        sorted(slots, key=lambda slot: int(slot[1:]))
    )


def serialize_boolean(value):
    return str(value).lower()


# ============================================================
# GENERATE TIMESLOTS
# ============================================================

timeslots = []

for day in DAYS:
    for hour in range(START_HOUR, END_HOUR):
        timeslot_id = f"T{len(timeslots) + 1}"

        timeslots.append((
            timeslot_id,
            day,
            f"{hour:02d}:00",
            60,
        ))

write_csv(
    "timeslots.csv",
    ["id", "day", "start_time", "duration_min"],
    timeslots,
)

slot_ids = [row[0] for row in timeslots]


# ============================================================
# GENERATE ROOMS
# ============================================================

rooms = []
room_details = {}

buildings = ["ENG", "SCI", "HUM", "SOC", "BUS", "ART"]

# Labs have varied capacities, including large teaching labs.
lab_capacities = [60, 100, 150, 200, 250]

# General-purpose rooms range from smaller classrooms
# to large lecture halls.
classroom_capacities = [60, 90, 120, 160, 220, 300]

for i in range(1, NUM_ROOMS + 1):
    room_id = f"R{i}"
    is_lab = i <= NUM_LAB_ROOMS

    if is_lab:
        capacity = lab_capacities[
            (i - 1) % len(lab_capacities)
        ]
    else:
        capacity = classroom_capacities[
            (i - NUM_LAB_ROOMS - 1)
            % len(classroom_capacities)
        ]

    building = buildings[(i - 1) % len(buildings)]

    rooms.append((
        room_id,
        capacity,
        serialize_boolean(is_lab),
        building,
    ))

    room_details[room_id] = {
        "capacity": capacity,
        "is_lab": is_lab,
        "building": building,
    }

write_csv(
    "rooms.csv",
    ["id", "capacity", "is_lab", "building"],
    rooms,
)


# ============================================================
# GENERATE INSTRUCTORS
# ============================================================

first_names = [
    "James", "Sarah", "Daniel", "Emily", "Michael",
    "Olivia", "David", "Sophia", "Samuel", "Grace",
    "Anthony", "Amina", "Joseph", "Maya", "Benjamin",
    "Fatima", "Alexander", "Isabella", "Noah", "Chloe",
]

last_names = [
    "Carter", "Mitchell", "Thompson", "Johnson",
    "Williams", "Brown", "Davis", "Wilson",
    "Anderson", "Taylor", "Martin", "Clark",
    "Lewis", "Walker", "Harris", "Robinson",
    "Young", "King", "Scott", "Green",
]

name_pairs = [
    (first, last)
    for first in first_names
    for last in last_names
]

rng.shuffle(name_pairs)

instructors = []
instructor_domains = {}
department_instructors = defaultdict(list)

department_codes = list(DEPARTMENTS.keys())

instructor_number = 0

for department_index, department in enumerate(department_codes):
    for local_index in range(INSTRUCTORS_PER_DEPARTMENT):
        instructor_number += 1
        instructor_id = f"I{instructor_number}"

        first_name, last_name = name_pairs[
            instructor_number - 1
        ]

        # Most instructors specialize in one department.
        # Some are qualified in an additional related area.
        qualified = [department]

        if local_index % 5 == 0:
            secondary = department_codes[
                (department_index + 1) % len(department_codes)
            ]
            qualified.append(secondary)

        domains = ";".join(qualified)

        instructor_domains[instructor_id] = set(qualified)

        for domain in qualified:
            department_instructors[domain].append(instructor_id)

        # Scheduling restrictions are mutually exclusive.
        unavailable = set(rng.sample(slot_ids, 3))

        remaining = [
            slot for slot in slot_ids
            if slot not in unavailable
        ]

        required_no_teach = set(rng.sample(remaining, 2))

        available = [
            slot for slot in remaining
            if slot not in required_no_teach
        ]

        preferred = set(rng.sample(available, 20))

        instructors.append((
            instructor_id,
            first_name,
            last_name,
            domains,
            serialize_slots(unavailable),
            serialize_slots(required_no_teach),
            serialize_slots(preferred),
        ))

write_csv(
    "instructors.csv",
    [
        "id",
        "first_name",
        "last_name",
        "domains",
        "unavailable_slots",
        "required_no_teach_slots",
        "preferred_slots",
    ],
    instructors,
)


# ============================================================
# GENERATE UNIVERSITY COURSE SECTIONS
# ============================================================

# Each cohort represents a distinct group of students.
# Students within a cohort attend the same five sections.
#
# Four sections belong to the cohort's primary department.
# One section is an elective from another department.
#
# This preserves the current cohort-based conflict model.

sections = []
cohort_details = {}
instructor_teaching_load = Counter()
department_section_counts = Counter()

# Use round-robin assignment to distribute teaching loads.
department_assignment_cursor = defaultdict(int)

# Course levels are illustrative.
course_levels = [1000, 2000, 3000, 4000]


def choose_instructor(subject_area):
    candidates = department_instructors[subject_area]

    # Favor the instructor with the smallest current
    # teaching load. Break ties deterministically using
    # the rotating cursor.
    start = department_assignment_cursor[subject_area]

    ordered = (
        candidates[start:] + candidates[:start]
    )

    instructor_id = min(
        ordered,
        key=lambda candidate: instructor_teaching_load[
            candidate
        ],
    )

    department_assignment_cursor[subject_area] = (
        start + 1
    ) % len(candidates)

    instructor_teaching_load[instructor_id] += 1

    return instructor_id


for cohort_index in range(NUM_COHORTS):
    cohort_number = cohort_index + 1
    cohort_id = f"C{cohort_number}"

    enrollment = COHORT_SIZES[cohort_index]

    primary_department = department_codes[
        cohort_index % len(department_codes)
    ]

    primary_index = department_codes.index(
        primary_department
    )

    # Cross-department elective.
    elective_department = department_codes[
        (primary_index + 3) % len(department_codes)
    ]

    cohort_details[cohort_id] = {
        "enrollment": enrollment,
        "primary_department": primary_department,
    }

    for course_index in range(COURSES_PER_COHORT):
        section_number = len(sections) + 1
        section_id = f"S{section_number}"

        is_elective = course_index == COURSES_PER_COHORT - 1

        if is_elective:
            subject_area = elective_department
        else:
            subject_area = primary_department

        # Create recognizable university-style course IDs.
        level = course_levels[course_index % len(course_levels)]

        course_number = level + (
            (cohort_index // len(department_codes)) % 20
        ) * 10 + course_index

        course_id = f"{subject_area}{course_number}"

        instructor_id = choose_instructor(subject_area)

        # For science/computing cohorts, one of the
        # primary-department sections requires a lab.
        needs_lab = (
            not is_elective
            and course_index == 3
            and subject_area in LAB_DEPARTMENTS
        )

        building_pref = DEPARTMENTS[subject_area]

        sections.append((
            section_id,
            course_id,
            subject_area,
            enrollment,
            instructor_id,
            serialize_boolean(needs_lab),
            cohort_id,
            building_pref,
        ))

        department_section_counts[subject_area] += 1

write_csv(
    "sections.csv",
    [
        "id",
        "course_id",
        "subject_area",
        "enrollment",
        "instructor_id",
        "needs_lab",
        "cohort_id",
        "building_pref",
    ],
    sections,
)


# ============================================================
# VALIDATE GENERATED DATASET
# ============================================================

expected_students = 10500
expected_sections = NUM_COHORTS * COURSES_PER_COHORT
expected_instructors = (
    len(DEPARTMENTS) * INSTRUCTORS_PER_DEPARTMENT
)

assert len(timeslots) == 60
assert len(rooms) == NUM_ROOMS
assert len(instructors) == expected_instructors
assert len(sections) == expected_sections
assert sum(COHORT_SIZES) == expected_students

# Verify unique identifiers.
assert len({row[0] for row in sections}) == len(sections)
assert len({row[0] for row in instructors}) == len(instructors)
assert len({row[0] for row in rooms}) == len(rooms)

# Verify each section has a qualified instructor.
for section in sections:
    (
        section_id,
        course_id,
        subject_area,
        enrollment,
        instructor_id,
        needs_lab,
        cohort_id,
        building_pref,
    ) = section

    assert subject_area in instructor_domains[instructor_id], (
        f"{section_id}: instructor {instructor_id} "
        f"is not qualified for {subject_area}"
    )

    assert enrollment == cohort_details[cohort_id][
        "enrollment"
    ]

    # At least one suitable room must exist.
    compatible_rooms = [
        room
        for room in room_details.values()
        if room["capacity"] >= enrollment
        and (
            needs_lab == "false"
            or room["is_lab"]
        )
    ]

    assert compatible_rooms, (
        f"{section_id}: no compatible room exists"
    )

# Verify instructor scheduling restrictions.
for instructor in instructors:
    unavailable = set(filter(
        None, instructor[4].split(";")
    ))

    required = set(filter(
        None, instructor[5].split(";")
    ))

    preferred = set(filter(
        None, instructor[6].split(";")
    ))

    assert unavailable.isdisjoint(required)
    assert unavailable.isdisjoint(preferred)
    assert required.isdisjoint(preferred)

# Verify each cohort has exactly five sections.
cohort_section_counts = Counter(
    section[6] for section in sections
)

assert len(cohort_section_counts) == NUM_COHORTS
assert all(
    count == COURSES_PER_COHORT
    for count in cohort_section_counts.values()
)

# Verify instructor teaching loads are reasonable.
assert max(instructor_teaching_load.values()) <= 6


# ============================================================
# SUMMARY
# ============================================================

print()
print("University dataset generated successfully.")
print("=" * 52)

print(f"Students represented: {expected_students:,}")
print(f"Student cohorts: {NUM_COHORTS}")
print(f"Course sections: {len(sections)}")
print(f"Academic departments: {len(DEPARTMENTS)}")
print(f"Instructors: {len(instructors)}")
print(f"Rooms: {len(rooms)}")
print(f"  Laboratory rooms: {NUM_LAB_ROOMS}")
print(f"  General classrooms: {NUM_ROOMS - NUM_LAB_ROOMS}")
print(f"Timeslots: {len(timeslots)}")

print()
print("Department section distribution:")

for department in department_codes:
    print(
        f"  {department:<6} "
        f"{department_section_counts[department]:>3} sections"
    )

print()
print("Enrollment distribution:")
print(f"  Smallest cohort: {min(COHORT_SIZES)}")
print(f"  Largest cohort: {max(COHORT_SIZES)}")
print(
    f"  Average cohort: "
    f"{sum(COHORT_SIZES) / NUM_COHORTS:.1f}"
)

print()
print("Instructor teaching loads:")
print(
    f"  Maximum: "
    f"{max(instructor_teaching_load.values())}"
)
print(
    f"  Minimum: "
    f"{min(instructor_teaching_load.values())}"
)

print()
print("Instructor scheduling preferences:")
print("  Unavailable slots: 3 per instructor")
print("  Required no-teach slots: 2 per instructor")
print("  Preferred slots: 20 per instructor")

print()
print(f"Random seed: {RANDOM_SEED}")
print(f"Output directory: {OUTPUT}")
print()
print("Dataset generation completed.")
