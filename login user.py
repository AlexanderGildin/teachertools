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
                        # session['user_login'] = request.form['username']
                        return make_response(
                            f'Вы авторизованы под именем {request.form.get('username', 'Логин не задан')}')
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
        # обратиться к бд к таблице Users, если нет записи в которой поле login == user
        # тогда форма авторизации с надписью "такой пользователь не найден"
        user_data = get_user_by_login('users_database.db', session['user_login'])
        if user_data['role'] == 'student' and pupils_dict[user_data['login']] not in base_dict.dict.keys():
            return redirect(f'/logout/student/{user_data['login']}')
        return make_response(user)


@app.route("/logout/<role>/<user_login>", methods=['POST', 'GET'])
def out(role, user_login):
    if role == 'student':
        # если ключа с логином ученика в словаре нет, ошибки НЕ будет
        pupils_dict.pop(user_login)
    session['user_login'] = '_'
    return redirect('/start')


@app.route('/student', methods=['POST', 'GET'])
def student():
    global pupils_dict, base_dict
    # user = session.get('user_login', '_')
    user = 'user_1'
    user_data = get_user_by_login('users_database.db', user)
    if user_data:
        teacher = pupils_dict.get(user, '')
        # если учителя по ключу нет, то авторизованного студента в pupils dict нет. может ли такое быть?
        if teacher:
            if base_dict.get_lesson_status(teacher) == 'Задан очередной вопрос.':
                # данные по последнему вопросу в виде списка ["вопрос", "верный ответ", вес]
                quest_data = base_dict.get_last_question_data(teacher)
                # если число вопросов и число ответов ученика одинаково, ученик уже дал ответ на последний вопрос.
                if len(base_dict.dict[teacher]['question']) == len(base_dict.dict[teacher]['answers'][user]) - 1:
                    return render_template('student.html', lesson_status='Пауза')
                # ЕСЛИ ученик зашел не с начала урока и вопросов было задано больше одного,
                # сделать автоматические неверные ответы на предыдущие задания

                # если ученик ответил на все вопросы кроме последнего, возвращаем вопрос
                if len(base_dict.dict[teacher]['question']) == len(base_dict.dict[teacher]['answers'][user]) - 2:
                    if request.method == 'POST':
                        # к нам пришел ответ ученика. добавление его в base_dict. форма ожидания следующего вопроса.
                        base_dict.add_student_answer(teacher, user, request.form['answer'])
                        return redirect('/student')
                    # в другом случае рендерим форму вопроса
                    return render_template('student.html',
                                           lesson_status=base_dict.get_lesson_status(teacher), quest_data=quest_data)
            if base_dict.get_lesson_status(teacher) == 'Пауза.':
                return render_template('student.html', lesson_status='Пауза')
    # школьник автоматически разлогинивается, если: 
    # - логина под которым он авторизован в бд нет
    # - логина школьника нет в pupils dict
    # - урок у учителя к которому он прикреплен не идет
    return redirect(f'/logout/student/{user}')


@app.route('/teacher', methods=['POST', 'GET'])
def teacher_lesson():
    global pupils_dict, base_dict
    user = session.get('user_login', '_')
    if user:
        lesson_data = base_dict.get_lesson_data(user)
        if lesson_data:
            if request.method == 'POST':
                # добавление вопроса в base dict и перезагрузка страницы
                base_dict.add_question(user, request.form["question"], request.form["correct_answer"],
                                       request.form["weight"])
                return redirect('/teacher')
            return f''
        # в другом случае у учителя не идет урок, поэтому мы автоматически начинаем новый и перезагружаем страницу
        base_dict.add_teacher(user)
        return redirect('/teacher')
    return redirect(f'/logout/teacher/{user}')


@app.route('/teacher/finish_lesson/<teacher>')
def finish(teacher):
    global base_dict
    base_dict.dict.pop(teacher)
    return redirect('/teacher')


if __name__ == '__main__':
    pupils_dict = {}
    base_dict = BaseDict()
    app.run(port=8080, host='127.0.0.1')
