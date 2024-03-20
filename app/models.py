from app import app
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, session, redirect,  url_for, flash, send_from_directory, abort, make_response
from sqlalchemy import null, text, desc, asc, and_, or_, nullslast, cast, Float, func
from validate_email import validate_email
from datetime import date, datetime
from secrets import token_urlsafe
import subprocess
import os
import re
import mosspy
from nostril import nonsense


'''
This file defines data models and related business logics
'''


db = SQLAlchemy(app)

class HelpRequest(db.Model):
    """A class to represent Help Requests from users."""

    id = db.Column(db.Integer, primary_key=True)
    issue_name = db.Column(db.String(255), nullable=False)
    issue_description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return "<HelpRequest %r>" % self.id


class Assignment(db.Model):
    """A class to represent the Assignment Entity."""

    # Stores the id
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    startDate = db.Column(db.DateTime, nullable=True)
    endDate = db.Column(db.DateTime, nullable=True)
    createdBy = db.Column(db.Integer, nullable=True)
    mossUrl = db.Column(db.String(800), nullable=True)
    isPublic = db.Column(db.Boolean, nullable=True)
    dailyLatePenalty = db.Column(db.Integer, nullable=True, default=0)  # Daily late penalty rate as a percentage
    courseId = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return "<Assignment %r>" % self.id
    
class Course(db.Model):
    """A class to represent the Course Entity."""

    # Stores the id
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    courseCode = db.Column(db.String(200), nullable=False, unique=True)
    year = db.Column(db.String(200), nullable=True)
    semester = db.Column(db.String(200), nullable=True)
    startDate = db.Column(db.DateTime, nullable=True)
    endDate = db.Column(db.DateTime, nullable=True)
    createdBy = db.Column(db.Integer, nullable=True)
    enrollmentPassword = db.Column(db.String(50), nullable=False, unique=True)
    numOfStudents = db.Column(db.Integer, nullable=True)
    numOfTAs = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return "<Course %r>" % self.id
    
class UserCourse(db.Model):
    """A class to represent the UserCourse Entity."""

    # Stores the id
    id = db.Column(db.Integer, primary_key=True)
    courseId = db.Column(db.Integer, nullable=False)
    userId = db.Column(db.Integer, nullable=False)
    userRole = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "<UserCourse %r>" % self.id

class Submission(db.Model):
    """A class to represent the Submission Entity."""

    # Stores the id
    id = db.Column(db.Integer, primary_key=True)
    assignmentId = db.Column(db.Integer, nullable=False)
    userId = db.Column(db.Integer, nullable=False)
    submissionDate = db.Column(db.DateTime, nullable=False)
    fileName = db.Column(db.String(500), nullable=False)
    overwritten = db.Column(db.Boolean, nullable=True)
    assignmentName = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return "<Submission %r>" % self.id
    
class SubmissionResult(db.Model):
    """A class to represent the SubmissionResult Entity."""

    # Stores the id
    id = db.Column(db.Integer, primary_key=True)
    assignmentId = db.Column(db.Integer, nullable=False)
    testCaseId = db.Column(db.Integer, nullable=False)
    submissionId = db.Column(db.Integer, nullable=False)
    userId = db.Column(db.Integer, nullable=False)
    gradeDate = db.Column(db.DateTime, nullable=False)
    fileName = db.Column(db.String(500), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    maxScore = db.Column(db.Integer, nullable=True)


    def __repr__(self):
        return "<SubmissionResult %r>" % self.id

class CourseAssignment(db.Model):
    """A class to represent the CourseAssignment Entity."""

    # Stores the id
    id = db.Column(db.Integer, primary_key=True)
    courseId = db.Column(db.Integer, nullable=False)
    assignmentId = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "<CourseAssignment %r>" % self.id
    
class TAStudent(db.Model):
    """A class to represent the TAStudent Entity."""

    # Stores the id
    id = db.Column(db.Integer, primary_key=True)
    courseId = db.Column(db.Integer, nullable=False)
    studentId = db.Column(db.Integer, nullable=False)
    taId = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "<TAStudent %r>" % self.id
    
class TestCase(db.Model):
    """A class to represent the Assignment Entity."""

    # Stores the id
    id = db.Column(db.Integer, primary_key=True)
    visible = db.Column(db.Boolean, nullable=False)
    assignmentId = db.Column(db.Integer, nullable=False)
    userId = db.Column(db.Integer, nullable=False)
    submissionDate = db.Column(db.DateTime, nullable=False)
    fileName = db.Column(db.String(550), nullable=True)
    name = db.Column(db.String(550), nullable=True)
    maxScore = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return "<TestCase %r>" % self.id
    

class TestCaseFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    testCaseId = db.Column(db.Integer, nullable=False)
    assignmentId = db.Column(db.Integer, nullable=False)
    fileName = db.Column(db.String(550), nullable=False)

    def __repr__(self):
        return "<TestCaseFile %r>" % self.id


class User(db.Model):
    """A class to represent the User Entity."""

    # Stores the id
    id = db.Column(db.Integer, primary_key=True)
    # Stores the username
    username = db.Column(db.String(80), nullable=False)
    # Stores the email
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Stores the password
    password = db.Column(db.String(80), nullable=False)
    # Stores the real name (not required)
    student_number = db.Column(db.String(80), unique=False, nullable=True)
    role = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "<User %r>" % self.id


# create all tables
db.create_all()


def register(name, email, student_number, password,role):
    '''
    Register a new user
      Parameters:
        name (string):        user name
        email (string):       user email
        student_number (string): student's university number
        password (string):    user password
        role (int):           user role (1=Student, 2=TA, 3=Instructor)
      Returns:
        True if registration succeeded otherwise False
    '''
    # Check that the email has to follow addr-spec defined in RFC 5322
    if not email_check(email):
        return False

    # check if the email has been used:
    existed = User.query.filter_by(email=email).all()
    if len(existed) > 0:
        return False

    # check if the email and password are not empty:
    if not not_empty(email) and not not_empty(password):
        return False

    # Check that the password has to meet the required complexity:
    # minimum length 6, at least one upper case, at least one lower
    # case, and at least one special character.
    if not pw_check(password):
        return False

    # Check that has to be non-empty, alphanumeric-only,
    # and space allowed only if it is not as the prefix or suffix
    if not alphanumeric_check(name):
        return False

    # Check that user name is longer than 2 but less than 20
    if not length_check(name, 3, 20):
        return False
    
    #check role
    try:
        role = int(role)
        if role not in [1, 2, 3]:
            role = 1
    except ValueError:
        # If role is not an integer, default to 1
        role = 1
    

    # create a new user
    user = User(username=name, email=email, student_number=student_number,
                password=password,role=role)
    # add it to the current database session
    db.session.add(user)
    # actually save the user object
    db.session.commit()

    return True


def login(email, password):
    '''
    Check login information:
      First, email and password inputs needs to meet the same email/
      password requiremnts in the email_check and pw_check functions

      Parameters:
        email (string):    user email
        password (string): user password
      Returns:
        The user object if login succeeded otherwise None
    '''
    # The email and password inputs need to meet the requirements
    # specified in email_check and pw_check
    if email_check(email) and pw_check(password) is True:
        # compare email/password with the originally registered email/password
        valids = User.query.filter_by(email=email, password=password).all()
        if len(valids) != 1:
            return None
        return valids[0]
    else:
        return False
   
        
def pw_check(password):
    '''
    Ensure the password is valid
      Parameters:
        password (string):     user password
      Returns:
        True if password is valid otherwise False
    '''
    # Needs to be at least 6 characters
    if len(password) < 6:
        return False

    has_upper = False
    has_lower = False
    has_special = False

    # For each character, update upper, lower,
    # and special flags if char matches the requirement
    for c in password:
        if c.isupper():
            has_upper = True
        elif c.islower():
            has_lower = True
        elif not c.isalnum():
            has_special = True

    # Only return true if all the flags got set to True at least once
    return has_upper and has_lower and has_special



# Uses the validate_email library to ensure the email is valid.
# We can use this single line inside the methods that need it
# instead of leaving it as its own function.
def email_check(email):
    return validate_email(email)



def alphanumeric_check(title):
    '''
    Check if the given title satisfies:
    R4-1: The title of the product has to be alphanumeric-only,
    and space allowed only if it is not as prefix and suffix.
    Parameters:
        title (string):       title of the listing
    Returns:
        True if the requirements are meant, otherwise False
    '''
    if title[0] == " " or title[-1] == " ":
        return False
    for element in range(0, len(title)):
        if not (title[element].isalnum() or title[element] == " "):
            return False
    return True


def length_check(str, min, max):
    '''
    Check if the length of the string is valid
    Parameters:
        str (string):         string to be checked
        min (int):            minimum bound
        max (int):            maximum bound
    Returns:
        True if the requirements are meant, otherwise False
    '''
    if len(str) <= max and len(str) >= min:
        return True
    return False

def not_empty(word):
    '''
    Checks R1-1 if the email
    or password is empty
    '''
    if len(word) == 0:
        return False
    return True
