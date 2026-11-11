import xml.etree.ElementTree as ET

from DataStructures import (
    Dataset, GroupConstraint, Instructor, Room, RoomOption, Section, Student, TimeOption,
)


def int_or_none(value):
    return int(value) if value is not None else None


def parse_room(el) -> Room:
    x, y = (int(v) for v in el.get("location").split(","))
    room = Room(
        id=int(el.get("id")),
        capacity=int(el.get("capacity")),
        location=(x, y),
        constraint=el.get("constraint", "true") == "true",
        discouraged=el.get("discouraged", "false") == "true",
    )
    sharing = el.find("sharing")
    if sharing is not None:
        pattern = sharing.find("pattern")
        room.pattern = pattern.text.strip()
        room.pattern_unit = int(pattern.get("unit", 6))
        free = sharing.find("freeForAll")
        if free is not None:
            room.free_for_all_char = free.get("value")
        not_avail = sharing.find("notAvailable")
        if not_avail is not None:
            room.not_available_char = not_avail.get("value")
        for dept in sharing.findall("department"):
            room.departments[dept.get("value")] = int(dept.get("id"))
    return room


def parse_section(el) -> Section:
    return Section(
        id=int(el.get("id")),
        offering=int_or_none(el.get("offering")),
        config=int_or_none(el.get("config")),
        subpart=int(el.get("subpart")),
        parent=int_or_none(el.get("parent")),
        class_limit=int(el.get("classLimit")),
        department=int(el.get("department")),
        dates=el.get("dates", ""),
        nr_rooms=int(el.get("nrRooms", 1)),
        room_to_limit_ratio=float(el.get("roomToLimitRatio", 1.0)),
        committed=el.get("committed", "false") == "true",
        instructor_ids=[int(i.get("id")) for i in el.findall("instructor")],
        times=[
            TimeOption(
                days=t.get("days"),
                start=int(t.get("start")),
                length=int(t.get("length")),
                break_time=int(t.get("breakTime", 0)),
                pref=float(t.get("pref", 0)),
            )
            for t in el.findall("time")
        ],
        rooms=[RoomOption(room_id=int(r.get("id")), pref=float(r.get("pref", 0))) for r in el.findall("room")],
    )


def parse_constraint(el) -> GroupConstraint:
    return GroupConstraint(
        id=int(el.get("id")),
        type=el.get("type"),
        pref=el.get("pref"),
        section_ids=[int(c.get("id")) for c in el.findall("class")],
    )


def parse_student(el) -> Student:
    return Student(
        id=int(el.get("id")),
        offerings={int(o.get("id")): float(o.get("weight", 1.0)) for o in el.findall("offering")},
        prohibited_sections={int(p.get("id")) for p in el.findall("prohibited-class")},
    )


def Parse_Dataset(file_name) -> Dataset:
    root = ET.parse(file_name).getroot()

    rooms = {r.id: r for r in map(parse_room, root.find("rooms"))}
    sections = {s.id: s for s in map(parse_section, root.find("classes"))}
    constraints = [parse_constraint(c) for c in root.find("groupConstraints")]
    students = [parse_student(s) for s in root.find("students")]

    # Instructors only appear inside classes, so build them from the sections.
    instructors = {}
    offering_sections = {}
    for section in sections.values():
        for inst_id in section.instructor_ids:
            instructors.setdefault(inst_id, Instructor(id=inst_id)).section_ids.append(section.id)
        if section.offering is not None:
            offering_sections.setdefault(section.offering, []).append(section.id)

    return Dataset(
        nr_days=int(root.get("nrDays", 7)),
        slots_per_day=int(root.get("slotsPerDay", 288)),
        rooms=rooms,
        sections=sections,
        instructors=instructors,
        constraints=constraints,
        students=students,
        offering_sections=offering_sections,
    )
