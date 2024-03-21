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


@app.route('/assign-students-to-ta/<int:course_id>/<int:ta_id>', methods=['POST'])
@authenticate
def assign_students_to_ta(user, course_id, ta_id):
    if user.role != 3:
        flash("Unauthorized access.")
        return redirect('/')

    student_ids = request.form.getlist('student_ids')
    for student_id in student_ids:
        # Create a new TAStudent entry
        taStudent = TAStudent.query.filter(and_(TAStudent.courseId == course_id, TAStudent.studentId==student_id, TAStudent.taId == ta_id)).all()
        if len(taStudent) < 1:
            new_ta_student = TAStudent(courseId=course_id, studentId=int(student_id), taId=ta_id)
            db.session.add(new_ta_student)
    
    db.session.commit()
    flash('Students successfully assigned to TA.')
    return redirect(f'/users/{ta_id}/{course_id}')

@app.route('/remove-student-from-ta/<int:course_id>/<int:ta_id>/<int:student_id>', methods=['POST'])
@authenticate
def remove_student_from_ta(user, course_id, ta_id, student_id):
    if user.role != 3:
        flash("Unauthorized access.")
        return redirect('/')

    # Query to find the specific TAStudent association
    ta_student = TAStudent.query.filter_by(courseId=course_id, taId=ta_id, studentId=student_id).first()
    if ta_student:
        db.session.delete(ta_student)
        db.session.commit()
        flash('Student successfully removed from TA.')
    else:
        flash('Association not found.')

    return redirect(f'/users/{ta_id}/{course_id}')

@app.route('/view-student/<int:user_id>/<int:course_id>')
@authenticate
def view_student(user, user_id, course_id):
    try:
        # Ensure only TAs and instructors can view this page
        if user.role not in [2, 3]:
            return redirect('/')

        student = findUserById(user_id)
        course = getCourseById(course_id, user)
        submissions = getSubmissions(course_id, user_id)


        return render_template('view-student.html',  student=student, user=user, course=course, submissions=submissions)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "An unexpected error occurred", 500
    


@app.route('/users/<int:user_id>/<int:course_id>')
@authenticate
def user_details(user, user_id, course_id):

    print("1")
    # Ensure only TAs and instructors can view this page
    if user.role not in [2, 3]:
        return redirect('/')

    student = findUserById(user_id)
    print("2")
    course = getCourseById(course_id, user)
    print("3")
    submissions = getSubmissions(course_id, user_id)
    print("4")

    if student.role == 2:
        print("5")
    # Fetch all students in the course
        students = findUsersInCourse(user, course_id, user_id)
        print("6")
        print(students)

    

    # Fetch all students already assigned to a TA in the course
        assignedStudents = findAssignedStudents(user, user_id, course_id)
        print("7")
    # Convert assignedStudents to a set of IDs for efficient lookup
        assignedStudentIds = {student.id for student in assignedStudents}
        print("8")

        print(assignedStudents)
        print(assignedStudentIds)


    # Filter out assigned students
        allStudents = [student for student in students if student.id not in assignedStudentIds]
        print("9")
    
    else:
        print("7")
        students = []
        
        assignedStudents = []
        allStudents = []

    print("loading page")


    return render_template('user_details.html', assignedStudents=assignedStudents, students=allStudents, student=student, user=user, course=course, submissions=submissions)


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