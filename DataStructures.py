class Room:
    def __init__(self, id, capacity, location, is_available):
        self.id = id
        self.capacity = capacity
        self.location = location
        self.is_available = is_available

class Instructor: 
    def __init__(self, id, name):
        self.id = id
        self.name = name

class Schedule:
    def __init__(self, instructor, room, time):
        self.instructor = instructor
        self.room = room
        self.time = time

class Student:
    def __init__(self, id):
        self.id = id

class Course:
    def __init__(self, id, name, instructor, room):
        self.id = id
        self.name = name
        self.instructor = instructor
        self.room = room

class Timeslot:
    def __init__(self, id, start_time, end_time):
        self.id = id
        self.start_time = start_time
        self.end_time = end_time

