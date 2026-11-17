from src.model.time_utils import time_to_minutes


def calculate_instructor_preference_penalty(timetable, sections, instructors):
    total_penalty = 0
    for section in sections:
        timeslot_id, _ = timetable[section.id]

        instructor = instructors[section.instructor_id]

        if instructor.preferred_slots and timeslot_id not in instructor.preferred_slots:
            total_penalty += 1
    return total_penalty

def calculate_cohort_idle_time_penalty(timetable, sections, timeslots, cohort_ids):
    def get_start_time(section):
        timeslot_id, _ = timetable[section.id]
        timeslot = timeslots[timeslot_id]
        return timeslot.start_time
    
    total_idle_time = 0
    for cohort_id in cohort_ids:
        dailySchedule = {}
        for section in sections:
            # Find the scheduled classes belonging to cohort
            if section.cohort_id == cohort_id:
                timeslot_id, _ = timetable[section.id]

                # Group those classes by day
                day = timeslots[timeslot_id].day
                if day not in dailySchedule:
                    dailySchedule[day] = []
                dailySchedule[day].append(section)

        for day in dailySchedule:
            dailySchedule[day] = sorted(dailySchedule[day], key=get_start_time)

            length = len(dailySchedule[day])
            for i in range(length - 1):
                currentSection = dailySchedule[day][i]
                nextSection = dailySchedule[day][i+1]

                current_timeslot_id, _  = timetable[currentSection.id]
                current_timeslot = timeslots[current_timeslot_id]

                next_timeslot_id, _ = timetable[nextSection.id]
                next_timeslot = timeslots[next_timeslot_id]

                current_end = time_to_minutes(current_timeslot.start_time) + current_timeslot.duration_min
                next_start = time_to_minutes(next_timeslot.start_time)

                gap = max(0, next_start - current_end)

                total_idle_time += gap
            
    return total_idle_time

def calculate_total_penalty(
    timetable, 
    sections, 
    instructors, 
    timeslots, 
    cohort_ids, 
    idle_w, 
    preference_w,
):

    idle_penalty = calculate_cohort_idle_time_penalty(timetable, sections, timeslots, cohort_ids)

    preference_penalty = calculate_instructor_preference_penalty(timetable, sections, instructors)

    total_penalty = (idle_w * idle_penalty) + (preference_w * preference_penalty)

    return total_penalty