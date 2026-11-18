
import csv
from datetime import datetime, timedelta
from pathlib import Path


# Export a completed timetable as a human-readable CSV schedule.
# Convert internal section, timeslot, and room IDs into descriptive values.
# Preserve the section ID so multiple sections of a course remain distinguishable.
# Create the output directory automatically if it does not exist.
def export_schedule(timetable, sections, rooms, timeslots, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "course_id",
            "section_id",
            "day",
            "start_time",
            "end_time",
            "room",
            "instructor_id",
        ])

        for section_id, (timeslot_id, room_id) in timetable.items():
            section = sections[section_id]
            timeslot = timeslots[timeslot_id]
            room = rooms[room_id]

            # Calculate the end time using the timeslot duration.
            start = datetime.strptime(timeslot.start_time, "%H:%M")
            end = start + timedelta(minutes=timeslot.duration_min)

            # Include the building to distinguish rooms across buildings.
            room_label = f"{room.building}-{room.id}"

            writer.writerow([
                section.course_id,
                section.id,
                timeslot.day,
                timeslot.start_time,
                end.strftime("%H:%M"),
                room_label,
                section.instructor_id,
            ])

    return output_path
