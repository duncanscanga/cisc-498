from flask import send_file, render_template, render_template_string,request, session, redirect,  url_for, flash, send_from_directory, abort, make_response
from app.models import *
from app.assignmentServer import *
from app.courseServer import *
from app.userServer import *
from app import app
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from functools import wraps


def authenticate(inner_function):
    @wraps(inner_function)
    def wrapped_inner(*args, **kwargs):
        # check did we store the key in the session
        if 'logged_in' in session:
            email = session['logged_in']
            try:
                user = User.query.filter_by(email=email).one_or_none()
                if user:
                    # if the user exists, call the inner_function
                    # with user as parameter and any arguments it needs
                    return inner_function(user, *args, **kwargs)
            except Exception as e:
                # It's a good idea to log the exception here
                pass
        else:
            # else, redirect to the login page
            return redirect('/login')
    return wrapped_inner



@app.route('/login', methods=['GET'])
def login_get():
    return render_template('login.html',
                           message='Please login to your account')


@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    user = login(email, password)
    if user:
        session['logged_in'] = user.email
        """
        Session is an object that contains sharing information
        between a user's browser and the end server.
        Typically it is packed and stored in the browser cookies.
        They will be past along between every request the browser made
        to this services. Here we store the user object into the
        session, so we can tell if the client has already login
        in the following sessions.
        """
        # success! go back to the home page
        # code 303 is to force a 'GET' request
        return redirect('/', code=303)
    else:
        return render_template('login.html',
                               message='Incorrect email or password.')




@app.route('/')
@authenticate
def home(user):
    courses = find_courses(user)
    return render_template('index.html',  courses=courses, user=user)


@app.route('/register', methods=['GET'])
def register_get():
    # templates are stored in the templates folder
    return render_template('register.html', message='')


@app.route('/register', methods=['POST'])
def register_post():
    email = request.form.get('email')
    name = request.form.get('name')
    student_number = request.form.get('student-number')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    role = request.form.get('role')
    error_message = None

    if password != password2:
        error_message = "The passwords do not match."
    else:
        # use backend api to register the user
        success = register(name, email, student_number, password, role)
        if not success:
            error_message = "Registration failed."
    # if there is any error messages when registering new user
    # at the backend, go back to the register page.
    if error_message:
        return render_template('register.html', message=error_message)
    else:
        return redirect('/login')


@app.route('/logout')
def logout():
    if 'logged_in' in session:
        session.pop('logged_in', None)
    return redirect('/')
