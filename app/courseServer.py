from app import app
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, session, redirect,  url_for, flash, send_from_directory, abort, make_response
from sqlalchemy import null, text, desc, asc, and_, or_, nullslast, cast, Float, func
from validate_email import validate_email
from datetime import date
from secrets import token_urlsafe
import subprocess
import os
import re
import mosspy
from nostril import nonsense
from app.models import *


def enrollInCourse(course_code, enrollment_password, user):
    if user.role != 1:
        return False

    course = Course.query.filter_by(courseCode=course_code).first()
        
    if course and course.enrollmentPassword == enrollment_password:
        # Assume user_id is the ID of the currently logged-in student
        user_course = UserCourse(courseId=course.id, userId=user.id, userRole=1)
        course.numOfStudents = course.numOfStudents + 1
        db.session.add(user_course)
        db.session.commit()
        return True
    return False

def enrollTaInCourse(courseId, user, ta_email):
    if user.role != 3:
        return False
    
    ta = User.query.filter(User.email == ta_email).first()
    
    userCourse = UserCourse.query.filter(and_(UserCourse.userId == ta.id, UserCourse.courseId == courseId)).all()
    if len(userCourse) > 0:
        return False
    
    course = Course.query.filter(Course.id == courseId).first()
    if course and ta and ta.role == 2:
        user_course = UserCourse(courseId=course.id, userId=ta.id, userRole=2)
        course.numOfTAs = course.numOfTAs + 1
        db.session.add(user_course)
        db.session.commit()
        return True

    return False


def getCourseById(courseId, user):
    #find course
    course = Course.query.filter(Course.id == courseId).first()
    
    # #check that the user can view this course
    # if not checkUserInCourse(courseId, user.id):
    #     return None
    
    return course


def getUsersForCourse(courseId, user):
    try:
        # Explicitly specify the join condition and filter by userId
        users = db.session.query(User).\
            join(UserCourse, UserCourse.userId == User.id).\
            filter(UserCourse.courseId == courseId).all()
        return users
    except Exception as e:
        print(f"Error fetching users for course {courseId}: {e}")
        return []
    

def checkUserInCourse(courseId, userId):
    userCourse = UserCourse.query.filter(and_(UserCourse.courseId == courseId, UserCourse.userId == userId)).all()
    
    return len(userCourse) > 0


 
def create_course(name, course_code, year, semester, start_date, end_date, userId):
    # Generate a unique password for course enrollment
    enrollment_password = token_urlsafe(16)  # Generates a URL-safe text string, containing 16 random bytes
    
    # Check if the generated password is truly unique
    while Course.query.filter_by(enrollmentPassword=enrollment_password).first() is not None:
        # If the generated password is not unique, generate a new one
        enrollment_password = token_urlsafe(16)

    course = Course(name=name, courseCode=course_code, year=year,
                    semester=semester, startDate=start_date, endDate=end_date, 
                    createdBy=userId, enrollmentPassword=enrollment_password, numOfTAs=0, numOfStudents=0) # Add the password here
    db.session.add(course)
    db.session.commit()

    userCourse = UserCourse(courseId=course.id, userId=userId, userRole=3)
    db.session.add(userCourse)
    db.session.commit()
    return True


def assign_to_course(course_id, assignment_id, userId):
    courseAssignment = CourseAssignment(courseId = course_id, assignmentId=assignment_id)
    db.session.add(courseAssignment)
    db.session.commit()
    return True




