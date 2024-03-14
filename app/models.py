from app import app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import null, text, desc, asc, and_, or_, nullslast, cast, Float, func
from validate_email import validate_email
from datetime import date
from secrets import token_urlsafe


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
    fileName = db.Column(db.String(550), nullable=False)

    def __repr__(self):
        return "<TestCase %r>" % self.id


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
    submission = Submission(assignmentId = assignment_id, userId=user.id, fileName=filename_with_user_id, submissionDate=func.now())
    db.session.add(submission)
    db.session.commit()
    return True

def get_test_Cases(isOwner, assignmentId):
    testCases = []
    if isOwner:
        testCases = TestCase.query.filter(TestCase.assignmentId == assignmentId).all()
    else:
        testCases = TestCase.query.filter(and_(TestCase.assignmentId == assignmentId, TestCase.visible == 1)).all()
    return testCases

def addTestCaseLog(filename_with_user_id, user, assignment_id, visible):
    testCase = TestCase(assignmentId = assignment_id, visible=visible, userId=user.id, fileName=filename_with_user_id, submissionDate=func.now())
    db.session.add(testCase)
    db.session.commit()
    return True

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

