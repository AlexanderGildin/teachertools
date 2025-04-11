class BaseDict():
    def __init__(self):
        self.dict = {}

    def add_teacher(self, teacher_login): # добавляет учителя
        teacher_dict = {}
        teacher_dict["question"] = []
        teacher_dict["answers"] = {}
        teacher_dict["status"] = ""
        self.dict[teacher_login] = teacher_dict

    def add_question(self, teacher_login, question_text, correct_answer, mark): # добавляет вопрос
        self.dict[teacher_login]["question"].append([question_text, correct_answer, mark])

    def add_student_answer(self, teacher_login, student, answer): # добавляет ответ ученика на вопрос
        if not self.dict[teacher_login]["answers"].get(student): # проверку существует ли ученик в словаре с ответами
            self.dict[teacher_login]["answers"][student] = []
        mark = answer == self.dict[teacher_login]["question"][-1][1] # проверка совпадает ли с правильным ответом на последний вопрос
        self.dict[teacher_login]["answers"][student].append([answer, mark])

    def chаnge_mark(self, teacher_login, student): # меняет правильность или неправильность последнего ответа ученика
        self.dict[teacher_login]["answers"][student][-1][1] = not self.dict[teacher_login]["answers"][student][-1][1]


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