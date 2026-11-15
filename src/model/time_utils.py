from datetime import datetime, timedelta

def timeslots_overlap(t1, t2):
    if t1.day != t2.day:
        return False

    start1 = datetime.strptime(t1.start_time, "%H:%M")
    start2 = datetime.strptime(t2.start_time, "%H:%M")

    end1 = start1 + timedelta(minutes=t1.duration_min)
    end2 = start2 + timedelta(minutes=t2.duration_min)

    return start1 < end2 and start2 < end1