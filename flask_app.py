from flask import session, Flask, make_response, render_template, request, redirect
from MishaDataBase import *
from base_dict import BaseDict

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/')
def index():
    return redirect('/start')


@app.route('/start', methods=['POST', 'GET'])
def start():
    global pupils_dict, base_dict
    user = session.get('user_login', '_')
    print(user)
    if user == '_' and request.method == 'GET':  # сессии с этого браузера еще не было
        # возвращаем форму авторизации
        print('login')
        return make_response(render_template('login.html'))

    if user == '_' and request.method == 'POST':  # сейчас к нам должна была прийти заполненная форма авторизации
        # # проверка на пустоту полей формы
        # if '' not in request.form.values():
        user_data = get_user_by_login(request.form.get('username', 'Логин не задан'))
        print(user_data)
        # проверка на наличие такого логина в базе
        if user_data:
            # проверка пароля
            if checkpw(bytes(request.form['password'], 'utf-8'), user_data.h_password):
                # проверка роли
                # если логина учителя не было на форме, то значит пользователь сам учитель
                if request.form['role'] == 'teacher':
                    if user_data.role == 'teacher':
                        base_dict.add_teacher(request.form.get('username', '_'))
                        base_dict.add_question(request.form.get('username', '_'),
                                               'пустой вопрос для уравнения индексов', 0, 0)
                        session['user_login'] = request.form['username']
                        return redirect('/teacher')
                    else:
                        return make_response(render_template('login.html',
                                                             message='Вы не учитель'))
                # иначе - студент
                if user_data.role == 'student':
                    # проверка существования учителя
                    if get_user_by_login(request.form['teacher_login']):
                        print(base_dict.dict)
                        if request.form['teacher_login'] in base_dict.dict.keys():
                            # добавление ученика в pupils dict
                            pupils_dict[request.form['username']] = request.form['teacher_login']
                            #  и в base dict на урок к учителю
                            base_dict.add_student_answer(request.form['teacher_login'], request.form['username'],
                                                         user_data.FIO, False)
                            # проверка, были ли уже заданы вопросы на уроке. если да - проставление всех вопросов,
                            # кроме последнего, неверными
                            lesson_data = base_dict.get_lesson_data(request.form['teacher_login'])
                            print(lesson_data)
                            while len(lesson_data['answers'][request.form['username']]) < len(
                                    lesson_data['question']) - 1:
                                base_dict.add_student_answer(request.form['teacher_login'], request.form['username'],
                                                             'Не отвечено', False)
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
        user_data = get_user_by_login(session['user_login'])
        if not user_data:
            session['user_login'] = '_'
            return redirect('/start')
        if user_data.role == 'student' and user not in pupils_dict:
            return redirect(f'/logout/student/{user_data.Login}')
        if user_data.role == 'student':
            return redirect('/student')
        if user_data.role == 'teacher' and user_data.Login in base_dict.dict.keys():
            return redirect('/teacher')
        if user_data.role == 'teacher':
            return redirect(f'/logout/teacher/{user_data.Login}')


@app.route('/register/<role>', methods=['GET', 'POST'])
def reg_stud(role):
    if role == 'student':
        text = 'Ученика'
    else:
        text = 'Учителя'
    if request.method == 'GET':
        return make_response(render_template('register.html', text=text, role=role))
    else:
        add_user('db/users_database.db', request.form['fullName'], request.form['username'], request.form['password'], role, '',
                 0)
        return redirect('/start')


# @app.route('/register/teacher')
# def reg_teach():
#     return make_response(render_template('register.html', role='Учителя'))


@app.route("/logout/<role>/<user_login>", methods=['GET'])
def out(role, user_login):
    if role == 'student':
        # здесь - удаление ученика с урока учителя и из pupils_dict
        if user_login in pupils_dict:
            base_dict.dict[pupils_dict[user_login]]['answers'].pop(user_login, None)
        pupils_dict.pop(user_login, None)
    else:
        # здесь - удаления урока учителя из base_dict и
        # удаление всех учеников, которые остались у него на уроке на текущий момент из pupils_dict
        base_dict.dict.pop(user_login, None)
        # решила сделать отдельный список с учениками на удаление, потому что
        # вроде бы изменение содержания словаря во время прохождения по его элементам плохая идея
        to_delete = []
        for student, teacher in pupils_dict.items():
            if teacher == user_login:
                to_delete.append(student)
        for student in to_delete:
            pupils_dict.pop(student, None)
    session['user_login'] = '_'
    return redirect('/start')


@app.route('/student', methods=['POST', 'GET'])
def student():
    global pupils_dict, base_dict

    user = session.get('user_login', '_')
    print('STUDENT')
    print(base_dict.dict)
    print(pupils_dict)
    print(user)
    user_data = get_user_by_login(user)
    print(user_data)
    if user_data and user != '_':
        teacher = pupils_dict.get(user, '')
        print(teacher)
        # если учителя по ключу нет, то авторизованного студента в pupils dict нет. значит, учитель разлогинился
        if teacher:
            if base_dict.get_lesson_status(teacher) == 'Задан очередной вопрос':
                # данные по последнему вопросу в виде списка ["вопрос", "верный ответ", вес]
                quest_data = base_dict.get_last_question_data(teacher)
                print(quest_data, 'LAST QUEST DATA FOR STUDENT FORM')
                # если число вопросов и число ответов ученика одинаково, ученик уже дал ответ на последний вопрос.
                if len(base_dict.dict[teacher]['question']) == len(base_dict.dict[teacher]['answers'][user]):
                    print('student ученик уже дал ответ на последний вопрос.')
                    return render_template('student.html', lesson_status='Пауза',
                                           user_data=user_data.to_dict(
                                               only=('FIO', 'Login', 'h_password', 'role', 'status_str', 'status_int')))
                # если ученик ответил на все вопросы кроме последнего, возвращаем вопрос
                if len(base_dict.dict[teacher]['answers'][user]) == len(base_dict.dict[teacher]['question']) - 1:
                    if request.method == 'POST':
                        print('student к нам пришел ответ на последний вопрос')
                        # к нам пришел ответ ученика. добавление его в base_dict. форма ожидания следующего вопроса.
                        base_dict.add_student_answer(teacher, user, request.form['studentAnswer'],
                                                     request.form['studentAnswer'] == quest_data[1])
                        return redirect('/student')
                    print('student все вопросы кроме последнего, возвращаем вопрос')
                    # в другом случае рендерим форму вопроса
                    return render_template('student.html',
                                           lesson_status=base_dict.get_lesson_status(teacher), quest_data=quest_data,
                                           user_data=user_data.to_dict(
                                               only=('FIO', 'Login', 'h_password', 'role', 'status_str', 'status_int')))
            else:
                return render_template('student.html', lesson_status='Пауза',
                                       user_data=user_data.to_dict(
                                           only=('FIO', 'Login', 'h_password', 'role', 'status_str', 'status_int')))
    # школьник автоматически разлогинивается, если: 
    # - логина под которым он авторизован в бд нет
    # - логина школьника нет в pupils dict
    # - урок у учителя к которому он прикреплен не идет
    # если случится ситуация, что почему-то количество вопросов и ответов различается более чем на 2, ученик тоже вылетит
    return redirect(f'/logout/student/{user}')


@app.route('/teacher', methods=['POST', 'GET'])
def teacher_lesson():
    global pupils_dict, base_dict
    print(base_dict.dict)
    user = session.get('user_login', '_')
    if user and user != '_':
        lesson_data = base_dict.get_lesson_data(user)
        if lesson_data:
            if request.method == 'POST':
                base_dict.change_mark_by_index(user, request.values['studentLogin'], request.values['questionIndex'])
                return redirect('/teacher')
            if len(lesson_data['question']) == 1:
                questions = []
            else:
                questions = lesson_data['question'][1:]
            if lesson_data['status'] == 'Пауза':
                change_status = 'Разрешить ученикам давать ответы'
            else:
                change_status = 'Запретить ученикам давать ответы'
            answers = {}
            for stud, ans in lesson_data['answers'].items():
                if len(ans) > 1:
                    answers[(get_FIO_by_username(stud), stud)] = ans[1:]
                else:
                    answers[(get_FIO_by_username(stud), stud)] = []
            return render_template('teacher_main.html',
                                   user=user,
                                   lesson_data=lesson_data,
                                   questions=questions,
                                   answers=answers,
                                   change_status=change_status)
        # в другом случае у учителя не идет урок. при завершении несуществующего урока ошибки не будет
        return redirect(f'/teacher/finish_lesson/{user}')
    return redirect(f'/logout/teacher/{user}')


@app.route('/<user_login>/<quest_num>')
def change_quest_mark(user_login, quest_num):
    user = session.get('user_login', '_')
    if user != '_' and get_user_by_login(user):
        if user_login in pupils_dict and user_login in base_dict.get_lesson_data(user)['answers'].keys():
            print(base_dict.change_mark_by_index(user, user_login, int(quest_num)))
        return redirect('/teacher')
    return redirect(f'/logout/teacher/{user}')


@app.route('/create', methods=['POST', 'GET'])
def new_quest():
    global base_dict
    user = session.get('user_login', '_')
    if request.method == 'POST':
        try:
            print(base_dict.dict, user)
            print(request.values['questionText'], request.values['correctAnswer'])
            print(request.values['weight'])
            print(int(request.values['weight']))
            base_dict.add_question(user, request.values['questionText'], request.values['correctAnswer'],
                                   int(request.values['weight']))
            # base_dict.dict[user]['status'] = 'Задан очередной вопрос'
            # пройтись по всем ученикам на уроке и проверить дали ли они ответ на последние вопросы.
            # если нет - сразу делать их неверными
            lesson_data = base_dict.get_lesson_data(user)
            print(base_dict.dict)
            for pupil, answers in lesson_data['answers'].items():
                while len(answers) < len(lesson_data['question']) - 1:
                    base_dict.add_student_answer(user, pupil, 'Не отвечено', False)
            return redirect('/teacher')
        except Exception as err:
            return render_template('create.html', user=user,
                                   message=f'Что-то пошло не так. Проверьте корректность введенных данных. {err}')
    return render_template('create.html', user=user)


@app.route('/change_lesson_status')
def change_lesson_status():
    user = session.get('user_login', '_')
    if user != '_':
        if base_dict.get_lesson_status(user):
            base_dict.change_lesson_status(user)
        return redirect('/teacher')
    return redirect(f'/logout/teacher/{user}')


@app.route('/teacher/finish_lesson/<teacher>')
def finish(teacher):
    global base_dict
    base_dict.dict.pop(teacher, None)
    base_dict.add_teacher(teacher)
    base_dict.add_question(teacher, 'пустой вопрос для уравнения индексов', 0, 0)
    return redirect('/teacher')


if __name__ == '__main__':
    db_session.global_init("db/users_database.db")
    pupils_dict = {}
    base_dict = BaseDict()
    app.run(port=8080, host='192.168.1.106')
