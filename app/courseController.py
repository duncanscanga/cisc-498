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


@app.route('/enroll', methods=['GET', 'POST'])
@authenticate
def enroll_course(user):
    if request.method == 'POST':
        course_code = request.form['courseCode']
        enrollment_password = request.form['enrollmentPassword']

        result = enrollInCourse(course_code, enrollment_password, user)
        if result:
            return redirect('/')  # Redirect to a confirmation page or dashboard
        else:
            flash('Invalid course code or enrollment password.', 'danger')

    # Render the enrollment form page if not POST or if there was an error
    return render_template('course_enrollment.html', user=user)



@app.route('/add-ta/<int:course_id>', methods=['GET', 'POST'])
@authenticate
def add_ta(user, course_id):
    course = getCourseById(course_id, user)
    if request.method == 'POST':
        ta_email = request.form['taEmail']
        result = enrollTaInCourse(course_id, user, ta_email)
        return redirect(f'/courses/{course_id}')
    
    return render_template('add_ta.html', user=user, course=course)



@app.route('/create-course', methods=['POST'])
@authenticate
def post_create_course(user):
    # Ensure the user creating the course is an instructor
    if user.role != 3:
        return redirect('/')

    # Grab form data related to course creation
    course_code = request.form.get('courseCode')
    name = request.form.get('name')
    year = request.form.get('year')
    semester = request.form.get('semester')
    start_date = request.form.get('startDate')
    end_date = request.form.get('endDate')

    # Convert start_date and end_date from string to datetime objects
    # Assuming date format in the form is 'YYYY-MM-DD'
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
    except ValueError:
        # Handle incorrect date format or other conversion errors
        return render_template('create-course.html', user=user, msg="Invalid date format.")

    # Call your function to create a new course instance in the database
    # Assuming such a function exists and is named 'create_course'
    success = create_course(name, course_code, year, semester, start_date, end_date, user.id)

    # Redirect based on the operation success
    if success:
        # Assuming you want to redirect to a page showing all courses or a confirmation page
        return redirect('/')
    else:
        # Stay on the create course page and show an error message
        return render_template('create-course.html', user=user, msg="Failed to create course.")



@app.route('/courses/<int:courseId>', methods=['GET'])
@authenticate
def get_course_details(user, courseId):
    course = getCourseById(courseId, user)
    assignments = getAssignmentsForCourse(courseId, user)
    users = getUsersForCourse(courseId, user)
    if course == None:
        return redirect('/')

    return render_template('course-details.html', users=users, user=user, course=course, assignments=assignments)



@app.route('/create-course', methods=['GET'])
@authenticate
def get_create_course(user):
    # Check if the current user's role is 3 (Instructor)
    if user.role == 3:
        # User is an Instructor, show the create-course page
        return render_template('create-course.html', user=user)
    else:
        # User is not an Instructor, redirect to the home page
        return redirect('/')
    

