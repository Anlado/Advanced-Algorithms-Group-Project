import xml.etree.ElementTree as ET

def Parse_Dataset(file_name):
    tree = ET.parse(file_name)
    root = tree.getroot()

    instructors = []
    students = []

    for instructor in root.find('instructor'):
        instructor_obj = Instructor(
            id=instructor.get('id')
        )
        instructors.append(instructor_obj)

    for student in root.find('students'):
        student_obj = Student(
            id=student.get('id')
        )
        students.append(student_obj)

    return {
        'instructors': instructors,
        'students': students
    }
