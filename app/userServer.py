from app import app
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, session, redirect,  url_for, flash, send_from_directory, abort, make_response
from sqlalchemy import null, text, desc, asc, and_, or_, nullslast, cast, Float, func, not_
from validate_email import validate_email
from datetime import date
from secrets import token_urlsafe
import subprocess
import os
import re
import mosspy
from nostril import nonsense
from app.models import *

def findUserById(user_id):
    user = User.query.filter(User.id == user_id).first()
    return user

def find_courses(user):
    try:
        # Explicitly specify the join condition and filter by userId
        courses = db.session.query(Course).\
            join(UserCourse, UserCourse.courseId == Course.id).\
            filter(UserCourse.userId == user.id).all()
        return courses
    except Exception as e:
        print(f"Error fetching courses for user {user.id}: {e}")
        return []


def findUsersNotEnrolledInTA(user, course_id):
    if user.role != 3:
        return []
    
    # Query all students in the course
    all_students_in_course = db.session.query(User).join(UserCourse, User.id == UserCourse.userId).filter(
        and_(
            UserCourse.courseId == course_id,
            UserCourse.userRole == 1  # Assuming 1 is the role ID for students
        )
    ).all()

    # Query all student IDs assigned to any TA for this course
    assigned_student_ids = [ta_student.studentId for ta_student in TAStudent.query.filter_by(courseId=course_id).all()]

    # Filter out students who are already assigned to a TA
    unassigned_students = [student for student in all_students_in_course if student.id not in assigned_student_ids]

    return unassigned_students

def findUsersInCourse(user, course_id, userId):
    if user.role != 3:
        return []
    userCourses = UserCourse.query.filter(and_(UserCourse.courseId == course_id, UserCourse.userRole == 1)).all()
    students = []
    for userCourse in userCourses:
        students.append(User.query.filter(User.id == userCourse.userId).first())

    return students

def findAssignedStudents(user, user_id, course_id):
    if not (user.role == 3 or user.role == 2):
        return []
    userTAs = TAStudent.query.filter(and_(TAStudent.taId == user_id, TAStudent.courseId == course_id)).all()
    students = []
    for userTA in userTAs:
        students.append(User.query.filter(User.id == userTA.studentId).first())

    return students

def update_user(curr_name, new_name, new_email, new_student_number, new_pw):
    '''
    R3-1, R3-4: Allow user to update username, password, email,
    billing addr, and postal code.
    Parameters:
        curr_name   (String):     current username
        new_name    (String):     updated username
        new_email   (String):     updated email
        new_pw      (String):     updated password
    Returns:
        True if the transaction is successful, False otherwise
    '''
    # If the current user exists
    valid = User.query.filter_by(username=curr_name).all()
    if len(valid) == 1:
        # We check if the new information is of a valid format
        if (
            email_check(new_email) and
            alphanumeric_check(new_name) and
            length_check(new_name, 3, 19) and
            pw_check(new_pw)
        ):

            # We then check if the new username and email are unique:
            # If the user didn't update their existing names/passwords,
            # the query will return 1, which is ok (it's their record),
            # so ensure that the name and email have indeed been updated.
            if (
                ((len(User.query.filter_by(username=new_name).all()) > 0)
                    and valid[0].username != new_name) or
                ((len(User.query.filter_by(email=new_email).all()) > 0)
                    and valid[0].email != new_email)
            ):
                return False
            # If they're unique, update all the fields
            else:
                valid[0].username = new_name
                valid[0].email = new_email
                valid[0].student_number = new_student_number
                valid[0].password = new_pw
                db.session.commit()
                return True
        else:
            # If any of the fields are not formatted properly, return False
            return False
    else:
        # If the current user does not exist, return False right away
        return False
    