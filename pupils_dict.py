class PupilsDict():
    def __init__(self):
        self.dict = {}
    def add_teacher(self, teacher):
        self.dict[teacher] = []
    def add_student(self, teacher, student_login):
        self.dict[teacher].append(student_login)