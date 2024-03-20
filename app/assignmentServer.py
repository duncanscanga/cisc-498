from app import app
from app.models import *
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


def get_user_submissions_for_assignment(user_id, assignment_id):
    return Submission.query.filter_by(userId=user_id, assignmentId=assignment_id).all()
def getGrades(assignmentId):
    # Calculate the total possible score for the assignment
    total_possible_score = db.session.query(
        func.sum(TestCase.maxScore)
    ).filter(TestCase.assignmentId == assignmentId).scalar()

    # First, identify the most recent submission for each student for the assignment
    recent_submissions = db.session.query(
        Submission.userId,
        db.func.max(Submission.id).label('latest_submission_id')
    ).filter(Submission.assignmentId == assignmentId
    ).group_by(Submission.userId).subquery()

    # Next, join this with SubmissionResults to aggregate scores only for the most recent submissions
    aggregated_scores = db.session.query(
        recent_submissions.c.userId,
        func.sum(SubmissionResult.score).label('total_score')
    ).join(SubmissionResult, SubmissionResult.submissionId == recent_submissions.c.latest_submission_id
    ).group_by(recent_submissions.c.userId).all()

    # Retrieve student numbers and corresponding scores, including total possible score
    grades = []
    for userId, total_score in aggregated_scores:
        user = User.query.get(userId)
        if user:
            grades.append({
                'student_id': user.student_number, 
                'score': total_score, 
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



def addSubmissionLog(filename_with_user_id, user, assignment_id):
    pastSubmissions = Submission.query.filter(and_( Submission.userId == user.id, Submission.assignmentId == assignment_id)).all()
    for pastSubmission in pastSubmissions:
        #overwrite each past submission to only store the latest
        pastSubmission.overwritten = True
    submission = Submission(assignmentId = assignment_id, userId=user.id, fileName=filename_with_user_id, submissionDate=func.now())
    db.session.add(submission)
    db.session.commit()
    db.session.flush() 
    return submission

def getSubmissions(course_id, user_id):
    submissions = Submission.query.filter(Submission.userId == user_id)\
                                  .join(Assignment, Assignment.id == Submission.assignmentId)\
                                  .join(CourseAssignment, CourseAssignment.assignmentId == Assignment.id)\
                                  .filter(CourseAssignment.courseId == course_id)\
                                  .order_by(Submission.submissionDate).all()
    for submisison in submissions:
        submisison.assignmentName = Assignment.query.filter(Assignment.id == submisison.assignmentId).first().name
    return submissions

def getSubmissionResults(submissionId, submission):
    submissionResults = SubmissionResult.query.filter(SubmissionResult.submissionId == submissionId).all()
    if len(submissionResults) > 0:
        assignmnet = Assignment.query.filter(Assignment.id == submission.assignmentId).first()
        if assignmnet.isPublic:
            return submissionResults
        else:
            # remove all results where the test cases were hidden
            updatedSubmissionResults = []
            for submissionResult in submissionResults:
                testCase = TestCase.query.filter(TestCase.id == submissionResult.testCaseId).first()
                if testCase.visible:
                    updatedSubmissionResults.append(submissionResult)
            return updatedSubmissionResults
    return []

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
def compile_and_run_c_program(c_file_name, input_txt_name):
    # Assuming current directory contains the files
    current_dir = ""
    c_file_path = os.path.join(current_dir, c_file_name)
    input_txt_path = os.path.join(current_dir, input_txt_name)

    # Compile the C program to an executable named 'student_output'
    compile_command = ["gcc", c_file_path, "-o", "student_output"]
    compile_result = subprocess.run(compile_command, capture_output=True)
    if compile_result.returncode != 0:
        # Handle compilation error properly
        return None

    # Run the compiled program with input from the txt file
    with open(input_txt_path, 'r') as input_file:
        run_command = ["./student_output"]
        run_result = subprocess.run(run_command, stdin=input_file, text=True, capture_output=True)
        if run_result.returncode == 0:
            return run_result.stdout
        else:
            # Handle runtime error properly
            return None

def auto_grade(c_file_name, input_txt_name):
    print("Grading submission...")
    
    # Run the grading logic
    output = compile_and_run_c_program(c_file_name, input_txt_name)
    
    if output is not None:
        print("Output of the student's program:")
        print(output)
    else:
        print("Failed to compile or execute the student's program.")
    
    return 0

def grade_submission(file_path, assignment_id, submission ):
    #first test case:
    print("1")
    result = grade_submission2(file_path)
    logGradingResult(result, "", 1, submission)

    #second test case:
    result = testCleanCompile(file_path)
    logGradingResult(result, "", 2, submission)

    #third test case:
    notes = checkCode(file_path)
    logGradingResult(result, notes, 3, submission)


    return result

def checkCode(c_file_path):
    with open(c_file_path) as response:
            answer = response.read()

    notes = "\n"

    notes = notes + 'Analysis of code:'


    # check for usage of comments in student code
    notes = notes +'\nComments:\n'
    single_count = int(answer.count('//'))
    multiple_count = int(answer.count('/*'))
    sums = single_count + multiple_count
    if sums >= 1:
        notes = notes +str(sums) + ' comments used in the program.\n'
    else:
        notes = notes +'No comments used in the program.\n'



   

    #check for structures
    notes = notes +'\nStructures:\n'
    no_space = ''.join(answer.split())
    structures_checked = ['for(', 'while(', 'if(', 'elseif(', 'else(', 'switch(']
    for structure in structures_checked:
        if int(no_space.count(structure) >= 1):
            notes = notes + 'Structure: ' + structure + ' was found\n'



    notes = notes +'\nVariables:\n'
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
                                    notes = notes +"\033[1;31m********************************************************************************\033[0m\n"
                                    notes = notes +s + " - \033[1;31mNONSENSE. CHECK CODE.\033[0m\n"
                                    notes = notes +"\033[1;31m********************************************************************************\033[0m\n"
                                else:
                                    notes = notes +s + " - \033[1;32mREAL WORD\033[0m\n"
                            else:
                                notes = notes +s + " - \033[1;34mCHECK CODE IF THIS IS NONSENSE, TOO SHORT FOR AUTODETECTOR\033[0m\n"
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
                            notes = notes +"\033[1;31m********************************************************************************\033[0m\n"
                            notes = notes +s + " - \033[1;31mNONSENSE. CHECK CODE.\033[0m\n"
                            notes = notes +"\033[1;31m********************************************************************************\033[0m\n"
                        else:
                            notes = notes +s + " - \033[1;32mREAL WORD\033[0m\n"
                    else:
                        notes = notes +s + " - \033[1;34mCHECK CODE IF THIS IS NONSENSE, TOO SHORT FOR AUTODETECTOR\033[0m\n"
            word = ''
        else:
            word += answer[x]
        x += 1



    return notes

def logGradingResult(result, notes, testCaseId, submission):
    submission = Submission.query.filter(Submission.id == int(submission.id)).all()[0]
    testCase = TestCase.query.filter(TestCase.id == testCaseId).all()[0]
    gradedSubmission = SubmissionResult(assignmentId=submission.assignmentId, testCaseId=testCaseId, notes=notes, submissionId= submission.id, userId=submission.userId, gradeDate=func.now(), fileName=submission.fileName, score=result, maxScore = testCase.maxScore )
    db.session.add(gradedSubmission)
    db.session.commit()

def testCleanCompile(c_file_path):
    compile_process = subprocess.run(["gcc", c_file_path, "-o", "student_program"], capture_output=True, text=True)
    if compile_process.returncode != 0:
        # Handle compilation error properly, perhaps return a score of 0 or a specific error code
        return 0
    return 100


def grade_submission2(c_file_path):
    compile_process = subprocess.run(["gcc", c_file_path, "-o", "student_program"], capture_output=True, text=True)
    if compile_process.returncode != 0:
        # Handle compilation error properly, perhaps return a score of 0 or a specific error code
        return 0

    inputs = "5000.67 10000.89 25000.01\n2000.82 3000.01 500.33\n10"
    expected_output_patterns = [
        r"The cost of truck 1 after \d+ years is \$\d+\.?\d*",
        # Add more patterns as needed
    ]

    run_process = subprocess.run(["./student_program"], input=inputs, capture_output=True, text=True)
    if run_process.returncode != 0:
        # Handle runtime error properly, perhaps return a score of 0 or a specific error code
        return 0

    actual_output = run_process.stdout

    score = 100
    penalty_per_error = 10

    for pattern in expected_output_patterns:
        if not re.search(pattern, actual_output, re.MULTILINE):
            score -= penalty_per_error

    # Return the final score as an integer
    return score



def find_user_assignments(userId):
    assignments = Assignment.query.filter(Assignment.createdBy == userId).all()
    return assignments



def create_assignment(name, start_date, end_date, userId):
    assignment = Assignment(name=name,startDate=start_date, endDate=end_date, createdBy = userId)
    db.session.add(assignment)
    db.session.commit()
    return True


  
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

def update_assignment_details(assignment_id, name, start_date, end_date, is_public):
    assignment = Assignment.query.filter(Assignment.id == assignment_id).all()
    if len(assignment) < 1:
        return False
    assignment = assignment[0]
    assignment.name = name
    assignment.start_date = start_date
    assignment.end_date = end_date
    assignment.isPublic = is_public
    db.session.commit()
    return True