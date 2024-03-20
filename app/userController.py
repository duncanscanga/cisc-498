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
from app.controllers import authenticate



@app.route('/users/<int:user_id>/<int:course_id>')
@authenticate
def user_details(user, user_id, course_id):
    # Ensure only TAs and instructors can view this page
    if user.role not in [2, 3]:
        return ('/')
    
    student = findUserById(user_id)
    course = getCourseById(course_id, user)
    submissions = getSubmissions(course_id, user_id)

    return render_template('user_details.html', student=student, user=user, course=course, submissions=submissions)



# Route to send the user update template
@app.route('/update-user', methods=['GET'])
@authenticate
def get_update_user(user):
    # Return the template with the user's current information
    return render_template(
        'update_user.html',
        user=user,
        msg="Please modify the information you want to update below.")



# Route to receive the updated user information
@app.route('/update-user', methods=['POST'])
@authenticate
def post_update_user(user):
    # First grab form data
    curr_name = user.username
    curr_email = user.email
    new_name = request.form.get('name')
    new_email = request.form.get('email')
    new_student_number = request.form.get('student-number')
    new_pw = request.form.get('password')

    # Evaluate if the update was successful:
    success = update_user(curr_name, new_name, new_email,
                          new_student_number, new_pw)
    # If so, return to home page
    # If not, stay on update_user.html with error msg
    if success:
        # We prompt the user to log back in to
        # restore session with valid new email
        if curr_email != new_email:
            return redirect('/logout')
        return redirect('/')
    else:
        return render_template(
            'update_user.html',
            user=user,
            msg="Update Failed!")