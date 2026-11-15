from src.model.time_utils import timeslots_overlap

def validate_section_assignment(section, room, timeslot, timetable, instructor, allSections, allTimeslots):
    if section.capacity > room.capacity:
        return False
    
    if section.needs_lab and not room.is_lab:
        return False
    
    if timeslot.id in instructor.unavailable_slots or timeslot.id in instructor.unavailable_slots:
        return False
    
    for existing_section_id, assignment in timetable.items():
        assigned_timeslot_id, assigned_room_id = assignment
        existing_section = allSections[existing_section_id]
        existing_timeslot = allTimeslots[assigned_timeslot_id]

        differentSections = existing_section_id != section.id
        shareInstructor = existing_section.instructor_id == section.instructor_id
        shareCohort = existing_section.cohort_id == section.cohort_id
        shareRoom = assigned_room_id == room.id
        
        overlap = timeslots_overlap(existing_timeslot, timeslot)
        
        if differentSections and (shareInstructor or shareCohort) and overlap:
            return False

        if differentSections and overlap and shareRoom:
            return False
        
    if section.subject_area not in instructor.domains:
        return False

    return True