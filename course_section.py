class CourseSection:
    def __init__(self,  enrollment_size, equipment, deliveryModality, duration, is_lab = False):
        self.is_lab = is_lab
        self.equipment = equipment
        self.enrollment_size = enrollment_size
        self.deliveryModality == deliveryModality # online/in person/hybrid
        self.duration = duration
        