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
import nonsense


'''
This file defines data models and related business logics
'''


db = SQLAlchemy(app)


class Assignment(db.Model):
    """A class to represent the Assignment Entity."""

    # Stores the id
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    startDate = db.Column(db.DateTime, nullable=True)
    endDate = db.Column(db.DateTime, nullable=True)
    createdBy = db.Column(db.Integer, nullable=True)
    mossUrl = db.Column(db.String(800), nullable=True)

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

class CourseAssignment(db.Model):
    """A class to represent the CourseAssignment Entity."""

    # Stores the id
    id = db.Column(db.Integer, primary_key=True)
    courseId = db.Column(db.Integer, nullable=False)
    assignmentId = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "<CourseAssignment %r>" % self.id
    
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



def get_user_submissions_for_assignment(user_id, assignment_id):
    return Submission.query.filter_by(userId=user_id, assignmentId=assignment_id).all()



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

def enrollInCourse(course_code, enrollment_password, user):
    if user.role != 1:
        return False

    course = Course.query.filter_by(courseCode=course_code).first()
        
    if course and course.enrollmentPassword == enrollment_password:
        # Assume user_id is the ID of the currently logged-in student
        user_course = UserCourse(courseId=course.id, userId=user.id, userRole=1)
        db.session.add(user_course)
        db.session.commit()
        return True
    return False

def enrollTaInCourse(courseId, user, ta_email):
    if user.role != 3:
        return False
    
    course = Course.query.filter(Course.id == courseId).first()

    user = User.query.filter(User.email == ta_email).first()
    if course and user and user.role == 2:
        user_course = UserCourse(courseId=course.id, userId=user.id, userRole=2)
        db.session.add(user_course)
        db.session.commit()
        return True

    return False



def findUserById(user_id):
    user = User.query.filter(User.id == user_id).first()
    return user


def getCourseById(courseId, user):
    #find course
    course = Course.query.filter(Course.id == courseId).all()
    if len(course) < 1:
        return None
    
    #check that the user can view this course
    if not checkUserInCourse:
        return None
    
    return course[0]

def getAssignmentsById(assignmentId, user):
    #find assignment
    assignment = Assignment.query.filter(Assignment.id == assignmentId).all()
    if len(assignment) < 1:
        return None

    return assignment[0]

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

def getAssignmentsForCourse(courseId, user):
    try:
        # Explicitly specify the join condition and filter by userId
        assignments = db.session.query(Assignment).\
            join(CourseAssignment, CourseAssignment.assignmentId == Assignment.id).\
            filter(CourseAssignment.courseId == courseId).all()
        return assignments
    except Exception as e:
        print(f"Error fetching assignments for user {user.id}: {e}")
        return []

def find_assignments(user):
    assignments = Assignment.query.filter(Assignment.createdBy == user.id).all()
    return assignments

def checkUserInCourse(courseId, userId):
    userCourse = UserCourse.query.filter(and_(UserCourse.courseId == courseId, UserCourse.userId == userId)).all()
    
    return len(userCourse) > 0
    

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
    
def create_course(name, course_code, year, semester, start_date, end_date, userId):
    # Generate a unique password for course enrollment
    enrollment_password = token_urlsafe(16)  # Generates a URL-safe text string, containing 16 random bytes
    
    # Check if the generated password is truly unique
    while Course.query.filter_by(enrollmentPassword=enrollment_password).first() is not None:
        # If the generated password is not unique, generate a new one
        enrollment_password = token_urlsafe(16)

    course = Course(name=name, courseCode=course_code, year=year,
                    semester=semester, startDate=start_date, endDate=end_date, 
                    createdBy=userId, enrollmentPassword=enrollment_password) # Add the password here
    db.session.add(course)
    db.session.commit()

    userCourse = UserCourse(courseId=course.id, userId=userId, userRole=3)
    db.session.add(userCourse)
    db.session.commit()
    return True

def addSubmissionLog(filename_with_user_id, user, assignment_id):
    pastSubmissions = Submission.query.filter(and_( Submission.userId == user.id, Submission.assignmentId == assignment_id)).all()
    for pastSubmission in pastSubmissions:
        #overwrite each past submission to only store the latest
        pastSubmission.overwritten = True
    submission = Submission(assignmentId = assignment_id, userId=user.id, fileName=filename_with_user_id, submissionDate=func.now())
    db.session.add(submission)
    db.session.commit()
    db.session.flush() 
    return submission.id

def getSubmissions(course_id, user_id):
    submissions = Submission.query.filter(Submission.userId == user_id)\
                                  .join(Assignment, Assignment.id == Submission.assignmentId)\
                                  .join(CourseAssignment, CourseAssignment.assignmentId == Assignment.id)\
                                  .filter(CourseAssignment.courseId == course_id)\
                                  .order_by(Submission.submissionDate).all()
    for submisison in submissions:
        submisison.assignmentName = Assignment.query.filter(Assignment.id == submisison.assignmentId).first().name
    return submissions

def get_test_Cases(isOwner, assignmentId):
    testCases = []
    if isOwner:
        testCases = TestCase.query.filter(TestCase.assignmentId == assignmentId).all()
    else:
        testCases = TestCase.query.filter(and_(TestCase.assignmentId == assignmentId, TestCase.visible == 1)).all()
    return testCases

def addTestCaseLog(filename_with_user_id, user, assignment_id, visible):
    test_case = TestCase(visible=visible, assignmentId=assignment_id, userId=user.id, submissionDate=func.now())
    db.session.add(test_case)
    db.session.flush()  # To get test_case.id for the new entry
    # testCase = TestCase(assignmentId = assignment_id, visible=visible, userId=user.id, fileName=filename_with_user_id, submissionDate=func.now())
    # db.session.add(testCase)
    # db.session.commit()
    return True

def togglevisiblity(test_case_id):
    test_case = TestCase.query.filter_by(id=test_case_id).first()
    if test_case:
        test_case.visible = not test_case.visible
        db.session.commit()

def addTestCaseFileEntry(testcase_id, assignment_id, filename):
    test_case_file = TestCaseFile(testCaseId=testcase_id, assignmentId=assignment_id, fileName=filename)
    db.session.add(test_case_file)
    db.session.commit()

    return True

def create_testcase(assignment_id, userId, visible=True):
    # Query the number of existing TestCase objects for this assignmentId
    existing_test_cases_count = TestCase.query.filter_by(assignmentId=assignment_id).count()
    
   
    # Generate the new test case name
    new_test_case_name = f"Test Case {existing_test_cases_count + 1}"
    
    # Create a new TestCase object
    new_test_case = TestCase(
        visible=visible,
        assignmentId=assignment_id,
        userId=userId,
        submissionDate=func.now(),
        # Assuming you add a 'name' field to TestCase for storing "Test Case _"
        name=new_test_case_name  
    )
    
    # Add the new TestCase to the database session and commit it
    db.session.add(new_test_case)
    db.session.commit()
    
    return new_test_case


def compile_and_run_c_program(submission_path, input_text):
    compile_status = subprocess.run(["gcc", submission_path, "-o", "program_output"], capture_output=True)
    if compile_status.returncode != 0:
        print("Compilation Error:", compile_status.stderr.decode())
        return None
    
    run_status = subprocess.run(["./program_output"], input=input_text, text=True, capture_output=True)
    return run_status.stdout

def check(output, pattern, error_message, penalty):
    if not re.search(pattern, output, flags=re.MULTILINE):
        print(error_message)
        return penalty
    return 0



def submit_to_moss(submission_directory, assignmentId):
    print("here")
    userid = 732044316  # Your Moss user ID

    m = mosspy.Moss(userid, "c")  # Specify "c" for C language
    print("here2")

    for root, dirs, files in os.walk(submission_directory):
        for file in files:
            print(file)
            if file.endswith(".c"):  # Ensure only C files are added
                full_path = os.path.join(root, file)
                print("inside:")
                print(full_path)
                m.addFile(full_path)
    try:
        url = m.send(lambda file_path, display_name: print('*', end='', flush=True))
    except Exception as e:
        print(f"Error sending files to Moss: {e}")
    print("\nReport Url: " + url)

    assignmnet = Assignment.query.filter(Assignment.id == assignmentId).first()
    assignmnet.mossUrl = url
    db.session.commit()

    return url

def auto_grade(submission_path, assignment_id, submissionId):
    print("Retrieving submission record...")
    submission = Submission.query.filter_by(id=submissionId, assignmentId=assignment_id).first()
    if not submission:
        return make_response('Submission not found', 404)

    # Retrieve test cases for the assignment
    test_cases = TestCase.query.filter_by(assignmentId=assignment_id).all()
    
    for test_case in test_cases:
        print(f"Processing TestCase ID: {test_case.id}")

        # Retrieve files for this test case
        test_case_files = TestCaseFile.query.filter_by(testCaseId=test_case.id).all()
        
        for file in test_case_files:
            if file.fileName.endswith('.py'):
                # Assuming the file paths are stored as absolute paths or relative to a base directory
                
                assignment_folder = os.path.join(app.config['TESTCASE_FOLDER'], f'testcase-{file.testCaseId}')
                py_file_path = assignment_folder + "/" + file.fileName  # Modify this as needed
                print(py_file_path)
                try:
                    # Execute the .py file
                    result = subprocess.run(["python", py_file_path], capture_output=True, text=True)
                    print(f"Output for TestCase ID: {test_case.id} (.py):\n{result.stdout}")
                except Exception as e:
                    print(f"Error executing .py file for TestCase ID: {test_case.id}: {e}")

            elif file.fileName.endswith('.txt'):
                # Process .txt files as needed, e.g., as input for the C program or for validation
                txt_file_path = file.fileName  # Modify this as needed
                with open(txt_file_path, 'r') as txt_file:
                    input_text = txt_file.read()
                    # Here you could use input_text as input for running the C program
                    # Or compare it to expected output, etc.
                
                print(f"Processed .txt file for TestCase ID: {test_case.id}")

    # This is a simplified example. Adapt the logic for compiling, running, 
    # and checking output based on your specific requirements.

    # Remember to calculate and return the score based on the actual checks and validations you perform.
    return {"status": "Graded", "score": "Example Score"}

def assign_to_course(course_id, assignment_id, userId):
    courseAssignment = CourseAssignment(courseId = course_id, assignmentId=assignment_id)
    db.session.add(courseAssignment)
    db.session.commit()
    return True

def find_user_assignments(userId):
    assignments = Assignment.query.filter(Assignment.createdBy == userId).all()
    print(assignments)
    return assignments

def create_assignment(name, start_date, end_date, userId):
    assignment = Assignment(name=name,startDate=start_date, endDate=end_date, createdBy = userId)
    db.session.add(assignment)
    db.session.commit()
    return True

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
    
def remove_testcase(testcase_id, assignment_id=None):
    try:
        # If assignment_id is provided, use it for extra validation
        if assignment_id:
            testcase = TestCase.query.filter_by(id=testcase_id, assignmentId=assignment_id).first()
        else:
            testcase = TestCase.query.filter_by(id=testcase_id).first()
        
        if testcase:
            # find all TestCaseFiles
            testCaseFiles = TestCaseFile.query.filter_by(testCaseId=testcase_id).delete()
            db.session.delete(testcase)
            db.session.commit()
            return True
        else:
            return False  # Test case not found
    except Exception as e:
        print(f"Error removing test case: {e}")
        return False

def update_assignment_details(assignment_id, name, start_date, end_date):
    assignment = Assignment.query.filter(Assignment.id == assignment_id).all()
    if len(assignment) < 1:
        return False
    assignment = assignment[0]
    assignment.name = name
    assignment.start_date = start_date
    assignment.end_date = end_date
    db.session.commit()
    return True

def not_empty(word):
    '''
    Checks R1-1 if the email
    or password is empty
    '''
    if len(word) == 0:
        return False
    return True

