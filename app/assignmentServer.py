from app import app
from app.models import *
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, session, redirect,  url_for, flash, send_from_directory, abort, make_response
from sqlalchemy import null, text, desc, asc, and_, or_, nullslast, cast, Float, func, not_
from validate_email import validate_email
from datetime import date
from datetime import datetime, timedelta
from secrets import token_urlsafe
import subprocess
import os
import sys
import importlib.util
import re
import mosspy
from nostril import nonsense

def get_user_submissions_for_assignment(user_id, assignment_id):
    return Submission.query.filter_by(userId=user_id, assignmentId=assignment_id, overwritten=0).all()

def getStudentGrade(assignmentId, userId):
    # Calculate the total possible score for the assignment
    total_possible_score = db.session.query(
        func.sum(TestCase.maxScore)
    ).filter(TestCase.assignmentId == assignmentId).scalar()

    if total_possible_score is None:
        total_possible_score = 0

    # Identify the most recent submission for the student for the assignment
    latest_submission = db.session.query(
        Submission
    ).filter(Submission.assignmentId == assignmentId, Submission.userId == userId).order_by(Submission.id.desc()).first()

    # If there's no submission, return 0 as the total score
    if not latest_submission:
        return {
            'student_id': User.query.get(userId).student_number,
            'score': 0,
            'total_possible_score': total_possible_score
        }

    # Calculate the total score for the most recent submission
    total_score = db.session.query(
        func.sum(SubmissionResult.score)
    ).filter(SubmissionResult.submissionId == latest_submission.id).scalar()

    if total_score is None:
        total_score = 0

    # Adjust the total score based on manualLateMarks, if any
    manual_late_marks = latest_submission.manualLateMarks if latest_submission.manualLateMarks else 0
    adjusted_total_score = max(0, total_score - manual_late_marks)

    # Retrieve the student's number and their score
    user = User.query.get(userId)
    if user:
        return {
            'student_id': user.student_number,
            'score': adjusted_total_score,  # Use the adjusted score
            'total_possible_score': total_possible_score
        }

    # In case the user is not found, return None or an appropriate default value
    return None




def getGrades(assignmentId):
    # Calculate the total possible score for the assignment
    total_possible_score = db.session.query(
        func.sum(TestCase.maxScore)
    ).filter(TestCase.assignmentId == assignmentId).scalar()

    if total_possible_score is None:
        total_possible_score = 0

    # First, identify the most recent submission for each student for the assignment
    recent_submissions = db.session.query(
        Submission.userId,
        db.func.max(Submission.id).label('latest_submission_id')
    ).filter(Submission.assignmentId == assignmentId
    ).group_by(Submission.userId).subquery()

    # Next, fetch the manualLateMarks for the most recent submission for each student
    manual_late_marks_subquery = db.session.query(
        Submission.userId.label('userId'),
        Submission.manualLateMarks.label('manualLateMarks')
    ).join(
        recent_submissions,
        Submission.id == recent_submissions.c.latest_submission_id
    ).subquery()

    # Join this with SubmissionResults to aggregate scores only for the most recent submissions
    aggregated_scores = db.session.query(
        recent_submissions.c.userId,
        func.sum(SubmissionResult.score).label('total_score'),
        manual_late_marks_subquery.c.manualLateMarks
    ).join(
        SubmissionResult,
        SubmissionResult.submissionId == recent_submissions.c.latest_submission_id
    ).join(
        manual_late_marks_subquery,
        manual_late_marks_subquery.c.userId == recent_submissions.c.userId
    ).group_by(
        recent_submissions.c.userId,
        manual_late_marks_subquery.c.manualLateMarks
    ).all()

    # Retrieve student numbers and adjust scores, including total possible score
    grades = []
    for userId, total_score, manualLateMarks in aggregated_scores:
        user = User.query.get(userId)
        if user:
            # Adjust the total score based on manualLateMarks, if any
            manual_late_marks = manualLateMarks if manualLateMarks else 0
            adjusted_total_score = max(0, total_score - manual_late_marks)
            grades.append({
                'student_id': user.student_number,
                'score': adjusted_total_score,  # Use the adjusted score
                'total_possible_score': total_possible_score
            })

    return grades





def getAssignmentsById(assignmentId, user):
    #find assignment
    assignment = Assignment.query.filter(Assignment.id == assignmentId).all()
    if len(assignment) < 1:
        return None

    return assignment[0]


def getAssignmentsForCourse(courseId, user):
    try:
        assignments = Assignment.query.filter(Assignment.courseId == courseId).all()
        return assignments
    except Exception as e:
        print(f"Error fetching assignments for user {user.id}: {e}")
        return []
    
def find_assignments(user):
    assignments = Assignment.query.filter(Assignment.createdBy == user.id).all()
    return assignments



def addSubmissionLog(filename_with_user_id, user, assignment_id):
    pastSubmissions = Submission.query.filter(and_( Submission.userId == user.id, Submission.assignmentId == assignment_id)).all()

    for pastSubmission in pastSubmissions:
        #overwrite each past submission to only store the latest
        pastSubmission.overwritten = True

    submission = Submission(assignmentId = assignment_id, userId=user.id, fileName=filename_with_user_id, submissionDate=func.now(), overwritten=False, taOverallComments="")

    db.session.add(submission)

    db.session.commit()
    db.session.flush() 

    latePenalty = getLatePenalty(submission)

    submission.manualLateMarks = latePenalty
    db.session.commit()

    return submission

def getSubmissions(course_id, user_id):
    submissions = Submission.query.filter(and_(Submission.userId == user_id, not_(Submission.overwritten))).all()

    submissions = Submission.query.filter(and_(Submission.userId == user_id, not_(Submission.overwritten)))\
                                  .join(Assignment, Assignment.id == Submission.assignmentId)\
                                  .filter(Assignment.courseId == course_id)\
                                  .order_by(Submission.submissionDate).all()
    for submisison in submissions:
        submisison.assignmentName = Assignment.query.filter(Assignment.id == submisison.assignmentId).first().name
    return submissions

def getSubmissionResults(submissionId, submission, user):
    submissionResults = SubmissionResult.query.filter(SubmissionResult.submissionId == submissionId).all()
    if len(submissionResults) > 0:

        assignmnet = Assignment.query.filter(Assignment.id == submission.assignmentId).first()
        if assignmnet.isPublic:
            return submissionResults
        else:
            #user is a TA or instructor

            if user.role == 2 or user.role == 3:
                return submissionResults
            # remove all results where the test cases were hidden
            updatedSubmissionResults = []
      
            for submissionResult in submissionResults:
                testCase = TestCase.query.filter(TestCase.id == submissionResult.testCaseId).first()
                if testCase.visible:
                    updatedSubmissionResults.append(submissionResult)
            return updatedSubmissionResults
    return []

def numOfSubmissions(assignmentId):
    # Query the Submission table to count distinct userIds for the given assignmentId
    count = db.session.query(Submission.userId).filter(Submission.assignmentId == assignmentId).distinct().count()
    return count

def get_test_Cases(isOwner, assignmentId):
    testCases = []
    if isOwner:
        testCases = TestCase.query.filter(TestCase.assignmentId == assignmentId).all()
    else:
        testCases = TestCase.query.filter(and_(TestCase.assignmentId == assignmentId, TestCase.visible == 1)).all()
    return testCases

def addTestCaseLog(filename_with_user_id, user, assignment_id, visible, maxScore):
    test_case = TestCase(visible=visible, assignmentId=assignment_id, userId=user.id, submissionDate=func.now(), maxScore=maxScore)
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

def create_testcase(assignment_id, userId, visible, maxScore):
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
        maxScore=maxScore,
        # Assuming you add a 'name' field to TestCase for storing "Test Case _"
        name=new_test_case_name  
    )
    
    # Add the new TestCase to the database session and commit it
    db.session.add(new_test_case)
    db.session.commit()
    
    return new_test_case


def submit_to_moss(submission_directory, assignmentId):
    userid = 732044316  # Your Moss user ID
    m = mosspy.Moss(userid, "c")  # Specify "c" for C language

    for root, dirs, files in os.walk(submission_directory):
        for file in files:
            if file.endswith(".c"):  # Ensure only C files are added
                full_path = os.path.join(root, file)
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

def execute_python_function(file_path, function_path, *args, **kwargs):
    """
    Dynamically loads a Python function from a file and executes it.
    
    :param file_path: Path to the .py file containing the function.
    :param function_path: Dot-separated path to the function within the file.
    :param args: Positional arguments to pass to the function.
    :param kwargs: Keyword arguments to pass to the function.
    :return: The result of the function execution.
    """
    # Ensure the file path is secure and restricted to a safe directory
    if not file_path.startswith('/path/to/safe/directory'):
        raise ValueError("Insecure file path")

    spec = importlib.util.spec_from_file_location("module.name", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["module.name"] = module
    spec.loader.exec_module(module)
    
    # Navigate to the function based on function_path
    function = module
    for part in function_path.split('.'):
        function = getattr(function, part)
    
    return function(*args, **kwargs)


def grade_submission(file_path, assignment_id, submission):

    # Fetch all test cases for the assignment

    test_cases = TestCase.query.filter_by(assignmentId=assignment_id).all()



    for test_case in test_cases:

        if test_case.type == 'Compilation':

            result = testCleanCompile(file_path)
 
  
            if result:

                notes = "Compiled Successfully"
                score = test_case.maxScore
            else:
                notes = "Did not Compile"
                score = 0

            logGradingResult(score, notes, test_case.id, submission,"", 0, "")
  

        elif test_case.type == 'Output Comparison':

            result = testCleanCompile(file_path)
            
            if result:
                result, notes, diff_index, output, expected = grade_submission_with_input(file_path, test_case.input, test_case.expected_output)

                if result == 100:
                    score = test_case.maxScore
                else:
                    score = 0
            else:
                score = 0
                notes = "Could not Compile"
                output = ""
                diff_index = -1
                expected = ""
            

            logGradingResult(score, notes, test_case.id, submission, output, diff_index, expected)

        elif test_case.type == 'Code Check':

            notes = checkCode(file_path, "")
            score = test_case.maxScore

            logGradingResult(score, notes, test_case.id, submission, "", 0, "")
        elif test_case.type == 'Python Function':
            # Assume test_case.additional_info contains the function_path and args are stored appropriately
            # Example: test_case.additional_info = "path.to.function"
            try:
                # Assuming a safe directory where user-uploaded .py files are stored
                python_file_path = os.path.join('/safe/directory', test_case.fileName)
                result = execute_python_function(python_file_path, test_case.additional_info)
                notes = "Python function executed successfully."
                score = test_case.maxScore  # or derive score from result
            except Exception as e:
                notes = f"Error executing Python function: {e}"
                score = 0  # or a partial score based on the nature of the error

            logGradingResult(score, notes, test_case.id, submission, "", 0, "")
        elif test_case.type == 'File Name':
            equal = test_case.fileName == submission.fileName

            if equal:
                score = test_case.maxScore
                notes = "Correct File Name"
            else:
                score = 0
                notes = "Incorrect File Name"

            logGradingResult(score, notes, test_case.id, submission, submission.fileName, 0, test_case.fileName)

        elif test_case.type == 'Variable Name':
            equal = checkIfVariableInCode(file_path, test_case.variable)

            if equal:
                score = test_case.maxScore
                notes = "Variable used."
            else:
                score = 0
                notes = "Variable not found"

            logGradingResult(score, notes, test_case.id, submission, "", 0, test_case.variable)


def normalize_whitespace(text):
    """Normalize the whitespace in the text by replacing sequences of whitespace
    characters with a single space, and trimming leading and trailing whitespace."""
    return ' '.join(text.strip().split())
def find_first_difference_index(str1, str2):
    """Finds the index of the first difference between two strings.
    
    Args:
        str1 (str): The first string for comparison.
        str2 (str): The second string for comparison.
        
    Returns:
        int: The index of the first differing character, or -1 if the strings are identical.
    """
    min_length = min(len(str1), len(str2))
    for i in range(min_length):
        if str1[i] != str2[i]:
            return i
    # If one string is a substring of the other, return the start of the extra characters
    if len(str1) != len(str2):
        return min_length
    return -1

def grade_submission_with_input(c_file_path, inputs, expected_output):
    compile_process = subprocess.run(["gcc", c_file_path, "-o", "student_program"],
                                     capture_output=True, text=True)
    if compile_process.returncode != 0:
        return 0, "Compilation Error", None

    run_process = subprocess.run(["./student_program"], input=inputs,
                                 capture_output=True, text=True, universal_newlines=True)
    if run_process.returncode != 0:
        return 0, "Runtime Error", None

    actual_output = run_process.stdout.strip()
    normalized_actual_output = normalize_whitespace(actual_output)
    normalized_expected_output = normalize_whitespace(expected_output)


    diff_index = find_first_difference_index(normalized_actual_output, normalized_expected_output)
    
    if diff_index == -1:
        return 100, "Output matches expected output", -1, normalized_actual_output, normalized_expected_output
    else:
        return 0, f"Output does not match at index {diff_index}.", diff_index, normalized_actual_output, normalized_expected_output


def checkIfVariableInCode(c_file_path, variable):
    # Open the file to read its contents
    with open(c_file_path, 'r') as file:
        content = file.read()

    # Prepare the variable for a more accurate search to avoid partial matches
    # We add common separators before and after the variable name to ensure we're matching the variable itself
    # and not a substring of another word. Adjust these as necessary for your specific use cases.
    search_patterns = [
        f" {variable} ",  # Variable with spaces on both sides
        f" {variable}=",  # Variable assignment
        f"={variable}",   # Variable being assigned
        f" {variable},",  # Variable in a list of parameters or arguments
        f"({variable}",   # Variable after an opening parenthesis (function calls, etc.)
        f",{variable}",   # Variable in a list of parameters or arguments, not the first one
        f",{variable} ",  # Variable in a list, followed by a space
    ]

    # Search for the variable in the content using the patterns defined above
    for pattern in search_patterns:
        if pattern in content:
            return True  # Variable found

    # If the loop completes without finding the variable, it's not in the file
    return False

def checkCode(c_file_path, codeCheckAdditional):
    with open(c_file_path) as response:
        answer = response.read()

    notes = "\nAnalysis of code:\n"

    # Check for usage of comments in student code
    notes += "\nComments:\n"
    single_count = answer.count('//')
    multiple_count = answer.count('/*')
    total_comments = single_count + multiple_count
    if total_comments >= 1:
        notes += f"{total_comments} comments used in the program.\n"
    else:
        notes += "No comments used in the program.\n"

    # Check for structures
    notes += "\nStructures:\n"
    no_space = ''.join(answer.split())
    structures_checked = ['for(', 'while(', 'if(', 'elseif(', 'else(', 'switch(']
    structures_found = False
    for structure in structures_checked:
        if no_space.count(structure) >= 1:
            notes += f"Structure: {structure} was found\n"
            structures_found = True
    if not structures_found:
        notes += "No common programming structures found.\n"

    # Check for variables
    notes += "\nVariables:\n"
    x = 0
    word = ''
    while x < len(answer):
        if answer[x].isspace():
            variables = ['int', 'float', 'char', 'double', 'long']
            for vari in variables:
                if word == vari:
                    while answer[x].isspace():
                        x+=1
                    word = ''
                    while (not answer[x].isspace()) & (not answer[x] == ';'):
                        if answer[x] == ',':
                            s = vari + ' ' + word + ' found'
                            if(len(word) > 6):
                                if nonsense(word):
                                    notes += "\n"
                                    notes +=  s +  " NONSENSE. CHECK CODE.\n"
                                    notes += "\n"
                                else:
                                    notes += s +  " REAL WORD.\n"
                            else:
                                notes += s +  " CHECK CODE IF THIS IS NONSENSE, TOO SHORT FOR AUTODETECTOR\n"
                            x+=1
                            while answer[x].isspace():
                                x+=1
                            word = ''
                        word += answer[x]
                        x+=1
                    if word == 'main()':
                        continue
                    s = vari + ' ' + word + ' found'
                    if(len(word) > 6):
                        if nonsense(word):
                            notes += "\n"
                            notes += notes + s +  " NONSENSE. CHECK CODE.\n"
                            notes += "\n"
                        else:
                            notes += s +  " REAL WORD.\n"
                    else:
                        notes += s +  " CHECK CODE IF THIS IS NONSENSE, TOO SHORT FOR AUTODETECTOR\n"
            word = ''
        else:
            word += answer[x]
        x += 1


    return notes


def logGradingResult(result, notes, testCaseId, submission, output, index, expectedOutput):
    submission = Submission.query.filter(Submission.id == int(submission.id)).all()[0]
    testCase = TestCase.query.filter(TestCase.id == testCaseId).all()[0]
    gradedSubmission = SubmissionResult(assignmentId=submission.assignmentId, type=testCase.type, errorIndex=index, expectedOutput=expectedOutput, codeOutput=output, testCaseId=testCaseId, notes=notes, submissionId= submission.id, userId=submission.userId, gradeDate=func.now(), fileName=submission.fileName, score=result, maxScore = testCase.maxScore )
    db.session.add(gradedSubmission)
    db.session.commit()

def testCleanCompile(c_file_path):
    compile_process = subprocess.run(["gcc", c_file_path, "-o", "student_program"], capture_output=True, text=True)
    if compile_process.returncode != 0:
        # Handle compilation error properly, perhaps return a score of 0 or a specific error code
        return False
    return True


def find_user_assignments(userId):
    assignments = Assignment.query.filter(Assignment.createdBy == userId).all()
    return assignments



def create_assignment(name, start_date, end_date, userId, course_id):
    assignment = Assignment(name=name,startDate=start_date, endDate=end_date, createdBy = userId, courseId=course_id)
    db.session.add(assignment)
    db.session.commit()
    return True


def getLatePenalty(submission):
    """
    Calculate the late penalty for a submission, considering cases where the assignment end date might be None.
    Adds a grace period of 5 hours to the assignment end date before calculating penalties.

    Parameters:
    - submission: a Submission object with attributes `submissionDate` and a related `assignment` object 
                  with attributes `endDate` and `dailyLatePenalty`.

    Returns: 
    - The penalty as a percentage of the total score to be deducted.
    """
    assignment = Assignment.query.filter(Assignment.id == submission.assignmentId).first()
    # Check if due date is set; if not, return 0 penalty
    if assignment.endDate is None:
        return 0
    
    # Safely convert submissionDate and endDate to datetime if they are not already
    submissionDate = submission.submissionDate if isinstance(submission.submissionDate, datetime) \
        else datetime.strptime(submission.submissionDate, '%Y-%m-%d %H:%M:%S')

    dueDate = assignment.endDate if isinstance(assignment.endDate, datetime) \
        else datetime.strptime(assignment.endDate, '%Y-%m-%d %H:%M:%S')
    
    # Extend due date by 5 hours for the grace period
    extendedDueDate = dueDate + timedelta(hours=5)
    
    dailyLatePenalty = assignment.dailyLatePenalty
    # Check if the submission was late, considering the grace period
    if submissionDate > extendedDueDate:
        # Calculate the number of full days late, considering any part of a day as a full day
        delta = submissionDate - extendedDueDate
        days_late = delta.days + (1 if delta.seconds > 0 else 0)

        # Calculate the total penalty
        total_penalty = days_late * dailyLatePenalty
    else:
        # No penalty if the submission was on time or within the grace period
        total_penalty = 0

    return total_penalty

  
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

def update_assignment_details(assignment_id, name, start_date, end_date, is_public, daily_late_penalty):
    assignment = Assignment.query.filter(Assignment.id == assignment_id).all()
    if len(assignment) < 1:
        return False
    assignment = assignment[0]
    assignment.name = name
    if start_date is not None and start_date != '' and start_date != "" and len(start_date) > 4:
        date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        date = None
    assignment.startDate = date
    if end_date is not None and end_date != '' and end_date != "" and len(end_date) > 4:
        end_date2 = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date2 = None
    assignment.endDate = end_date2
    assignment.isPublic = is_public
    assignment.dailyLatePenalty = daily_late_penalty
    db.session.commit()
    return True



def findStudentsForTa(user, courseId):
    if not checkTa(user, courseId):
        return []
    students = TAStudent.query.filter(TAStudent.taId == user.id).all()
    result = []
    for student in students:
        result.append(User.query.filter(User.id == student.studentId).first())
    return result

def checkTa(user, courseId):
    courseEnrollment = UserCourse.query.filter(and_(UserCourse.userId == user.id, UserCourse.courseId == courseId)).all()
    if len(courseEnrollment) < 1:
        return False
    if courseEnrollment[0].userRole == 2 and user.role == 2:
        return True
    return False

def checkIfTa(user, assignment):
    courseEnrollment = UserCourse.query.filter(and_(UserCourse.userId == user.id, UserCourse.courseId == assignment.courseId)).all()
    if len(courseEnrollment) < 1:
        return False
    if courseEnrollment[0].userRole == 2 and user.role == 2:
        return True
    return False
