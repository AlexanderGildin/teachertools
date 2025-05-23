class BaseDict():
    def __init__(self):
        self.dict = {}

    def add_teacher(self, teacher_login):  # добавляет учителя
        teacher_dict = {}
        teacher_dict["question"] = []
        teacher_dict["answers"] = {}
        teacher_dict["status"] = "Задан очередной вопрос"
        self.dict[teacher_login] = teacher_dict

    def add_question(self, teacher_login, question_text, correct_answer, weight):  # добавляет вопрос
        self.dict[teacher_login]["question"].append([question_text, correct_answer, weight])

    def add_student_answer(self, teacher_login, student, answer, mark):  # добавляет ответ ученика на вопрос
        # если ученика еще нет на уроке, создаем ключ с учеником и пустой список как значение. (к нам пришли ФИО)
        if not self.dict[teacher_login]["answers"].get(student):
            self.dict[teacher_login]["answers"][student] = []
        self.dict[teacher_login]["answers"][student].append([answer, mark])

    def change_mark(self, teacher_login, student):  # меняет правильность или неправильность последнего ответа ученика
        self.dict[teacher_login]["answers"][student][-1][1] = not self.dict[teacher_login]["answers"][student][-1][1]

    def change_mark_by_index(self, teacher_login, student, quest_index):
        try:
            self.dict[teacher_login]["answers"][student][quest_index][1] = not \
                self.dict[teacher_login]["answers"][student][quest_index][1]

            return True
        except:
            return False

    def get_lesson_status(self, teacher_login):
        try:
            return self.dict[teacher_login]["status"]
        except:
            return ""

    def change_lesson_status(self, teacher_login):
        if self.dict[teacher_login]["status"] == 'Пауза':
            self.dict[teacher_login]["status"] = 'Задан очередной вопрос'
        elif self.dict[teacher_login]["status"] == 'Задан очередной вопрос':
            self.dict[teacher_login]["status"] = 'Пауза'

    def get_last_question_data(self, teacher_login):
        try:
            return self.dict[teacher_login]["question"][-1]
        except:
            return ()

    def get_lesson_data(self, teacher_login):
        try:
            return self.dict[teacher_login]
        except:
            return {}


if __name__ == "__main__":
    from pupils_dict import PupilsDict

    dict = BaseDict()
    p_dict = PupilsDict()
    p_dict.add_teacher("sgildin")
    p_dict.add_student("sgildin", "Timur123")
    print(p_dict.dict)
    dict.add_teacher("sgildin")
    dict.add_question("sgildin", "что такое словарь?", "ассоциативный массив", 5)
    dict.add_student_answer("sgildin", "Тимур", "ассоциативный массив")
    dict.chаnge_mark("sgildin", "Тимур")
    print(dict.dict)
