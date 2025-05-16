from flask import session, Flask, make_response, render_template, request, redirect
from MishaDataBase import *
from base_dict import BaseDict

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/start', methods=['POST', 'GET'])
def start():
    global pupils_dict, base_dict
    user = session.get('user_login', '_')
    print(user)
    if user == '_' and request.method == 'GET':  # сессии с этого браузера еще не было
        # возвращаем форму авторизации
        return make_response(render_template('login.html'))

    if user == '_' and request.method == 'POST':  # сейчас к нам должна была прийти заполненная форма авторизации
        # # проверка на пустоту полей формы
        # if '' not in request.form.values():
        user_data = get_user_by_login('users_database.db', request.form.get('username', 'Логин не задан'))
        print(user_data)
        # проверка на наличие такого логина в базе
        if user_data:
            # проверка пароля
            if checkpw(bytes(request.form['password'], 'utf-8'), user_data['h_password']):
                # проверка роли
                # если логина учителя не было на форме, то значит пользователь сам учитель
                if request.form['role'] == 'teacher':
                    if user_data['role'] == 'teacher':
                        base_dict.add_teacher(request.form.get('username', '_'))
                        base_dict.add_question(request.form.get('username', '_'),
                                               'пустой вопрос для уравнения индексов', 0, 0)
                        session['user_login'] = request.form['username']
                        return redirect('/teacher')
                    else:
                        return make_response(render_template('login.html',
                                                             message='Вы не учитель'))
                # иначе - студент
                if user_data['role'] == 'student':
                    # проверка существования учителя
                    if get_user_by_login('users_database.db', request.form['teacher_login']):
                        if request.form['teacher_login'] in base_dict.dict.keys():
                            # добавление ученика в pupils dict
                            pupils_dict[request.form['username']] = request.form['teacher_login']
                            #  и в base dict на урок к учителю
                            base_dict.add_student_answer(request.form['teacher_login'], request.form['username'],
                                                         user_data['FIO'])
                            # проверка, были ли уже заданы вопросы на уроке. если да - проставление всех вопросов,
                            # кроме последнего, неверными
                            lesson_data = base_dict.get_lesson_data(user)
                            while len(lesson_data['answers'][request.form['username']]) < len(lesson_data['questions']) - 1:
                                base_dict.add_student_answer(request.form['teacher_login'], request.form['username'], '')
                            # обновление куки
                            session['user_login'] = request.form['username']
                            return redirect('/student')
                        return make_response(
                            render_template('login.html',
                                            message='Этот учитель не ведет урок'))
                    return make_response(render_template('login.html',
                                                         message='Логин учителя не найден'))
                return make_response(render_template('login.html',
                                                     message='Вы не студент'))
            return make_response(
                render_template('login.html', message='Неверный пароль'))
        return make_response(
            render_template('login.html',
                            message='Пользователь с таким логином не найден'))
    else:  # у нас авторизованный пользователь
        user_data = get_user_by_login('users_database.db', session['user_login'])
        if not user_data:
            session['user_login'] = '_'
            return redirect('/start')
        if user_data['role'] == 'student' and pupils_dict[user_data['login']] not in base_dict.dict.keys():
            return redirect(f'/logout/student/{user_data['login']}')
        if user_data['role'] == 'student':
            return redirect('/student')
        if user_data['role'] == 'teacher' and user_data['login'] in base_dict.dict:
            return redirect('/teacher')
        if user_data['role'] == 'teacher':
            return redirect(f'/logout/teacher/{user_data['login']}')


@app.route('/logout/teacher')
def logout_teacher_shortcut():
    user = session.get('user_login', '_')
    return redirect(f'/logout/teacher/{user}')


@app.route("/logout/<role>/<user_login>", methods=['GET'])
def out(role, user_login):
    if role == 'student':
        pupils_dict.pop(user_login, None)  # безопасно удаляем
    session['user_login'] = '_'
    return redirect('/start')


@app.route('/student', methods=['POST', 'GET'])
def student():
    global pupils_dict, base_dict
    user = session.get('user_login', '_')
    print(f"[DEBUG] Current user: {user}")  # Debugging output
    user_data = get_user_by_login('users_database.db', user)
    if not user_data:
        print("[DEBUG] User data not found in database.")  # Debugging output
        return redirect('/start')
    teacher = pupils_dict.get(user, '')
    print(f"[DEBUG] Teacher for user {user}: {teacher}")  # Debugging output
    if not teacher or teacher not in base_dict.dict:
        print("[DEBUG] Teacher not found or not in base_dict.")  # Debugging output
        return redirect(f'/logout/student/{user}')
    lesson_status = base_dict.get_lesson_status(teacher)
    print(f"[DEBUG] Lesson status for teacher {teacher}: {lesson_status}")  # Debugging output
    if lesson_status == 'Задан очередной вопрос':
        quest_data = base_dict.get_last_question_data(teacher)
        print(f"[DEBUG] Last question data: {quest_data}")  # Debugging output
        answers = base_dict.dict[teacher]['answers'].get(user, [])
        num_questions = len(base_dict.dict[teacher]['question'])
        num_answers = len(answers)
        print(f"[DEBUG] Number of questions: {num_questions}, Number of answers: {num_answers}")  # Debugging output
        if num_questions == num_answers:
            return render_template('student.html', lesson_status='Пауза')
        if num_questions == num_answers + 1:
            if request.method == 'POST':
                base_dict.add_student_answer(teacher, user, request.form['studentAnswer'])
                return redirect('/student')
            return render_template('student.html', lesson_status=lesson_status, quest_data=quest_data)
    if lesson_status == 'Пауза':
        return render_template('student.html', lesson_status='Пауза')
    print("[DEBUG] Redirecting to logout due to invalid lesson status.")  # Debugging output
    return redirect(f'/logout/student/{user}')


@app.route('/teacher', methods=['POST', 'GET'])
def teacher_lesson():
    global pupils_dict, base_dict
    user = session.get('user_login', '_')
    if user:
        lesson_data = base_dict.get_lesson_data(user)
        print(f"[DEBUG] Lesson data before validation: {lesson_data}")  # Debugging output

        # Проверка и инициализация ключей 'answers' и 'questions'
        if 'answers' not in lesson_data:
            print("[WARNING] 'answers' key is missing in lesson_data. Initializing...")
            lesson_data['answers'] = {}
        if 'questions' not in lesson_data:
            print("[WARNING] 'questions' key is missing in lesson_data. Initializing...")
            lesson_data['questions'] = []

        for pupil, answers in lesson_data['answers'].items():
            while len(answers) < len(lesson_data['questions']) - 1:
                base_dict.add_student_answer(user, pupil, '')
        if lesson_data:
            questions = lesson_data['questions']
            answers = {
                pupil: [(answer, question[1]) for answer, question in zip(answers, questions)]
                for pupil, answers in lesson_data['answers'].items()
            }
            return render_template('teacher_main.html', questions=questions, answers=answers)
        # в другом случае у учителя не идет урок. при завершении несуществующего урока ошибки не будет
        return redirect(f'/teacher/finish_lesson/{user}')
    return redirect(f'/logout/teacher/{user}')


@app.route('/new_quest', methods=['POST', 'GET'])
def new_quest():
    global base_dict
    user = session.get('user_login', '_')
    if request.method == 'POST':
        question = request.form.get('question')
        correct_answer = request.form.get('correct_answer')
        weight = request.form.get('weight', 1)  # по умолчанию 1
        if question and correct_answer:
            base_dict.add_question(user, question, correct_answer, weight)
            base_dict.dict[user]['status'] = 'Задан очередной вопрос'
            # пройтись по всем ученикам на уроке и проверить дали ли они ответ на последние вопросы.
            lesson_data = base_dict.get_lesson_data(user)
            print(f"[DEBUG] Lesson data: {lesson_data}")  # Debugging output
            if 'answers' not in lesson_data:
                print("[ERROR] 'answers' key is missing in lesson_data")
                return make_response("Internal Server Error: Missing 'answers' key", 500)
            for pupil, answers in lesson_data['answers'].items():
                while len(answers) < len(lesson_data['questions']) - 1:
                    base_dict.add_student_answer(user, pupil, '')
            return redirect('/teacher')
        return make_response('Некорректные данные формы', 400)
    return render_template('create.html', user_login=user)


@app.route('/teacher/finish_lesson/<teacher>')
def finish(teacher):
    global base_dict
    base_dict.dict.pop(teacher)
    base_dict.add_teacher(teacher)
    base_dict.add_question(teacher,'пустой вопрос для уравнения индексов', 0, 0)
    return redirect('/teacher')


if __name__ == '__main__':
    pupils_dict = {}
    base_dict = BaseDict()
    app.run(port=8080, host='127.0.0.1')
