from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/teacher')
# def generator():
#     return render_template('teacher_main.html')

# @app.route('/student')
# def student():
#     return render_template('student.html')

# @app.route('/login')
# def login():
#     return render_template('login.html')

# @app.route('/create')
# def create():
#     return render_template('create.html')

if __name__ == '__main__':
    app.run(debug=True)