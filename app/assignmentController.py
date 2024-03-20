from flask import send_file, Response, render_template, render_template_string,request, session, redirect,  url_for, flash, send_from_directory, abort, make_response
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
import csv
from io import StringIO


@app.route('/assignments', methods=['GET'])
@authenticate
def get_assignments(user):
    assignments = find_assignments(user)
    return render_template('assignments.html',  assignments=assignments, user=user)



@app.route('/assignments/<int:assignmentId>', methods=['GET'])
@authenticate
def get_assignment_details(user, assignmentId):
    assignment = getAssignmentsById(assignmentId, user)
    if assignment is None:
        return redirect('/')

    isOwner = assignment.createdBy == user.id
    submissions = get_user_submissions_for_assignment(user.id, assignmentId)
    testCases = get_test_Cases(isOwner, assignmentId)

    # Fetch related TestCaseFile entries for each test case
    for test_case in testCases:
        test_case.files = TestCaseFile.query.filter_by(testCaseId=test_case.id).all()

    return render_template('assignment-details.html',  testCases=testCases, submissions=submissions, isOwner=isOwner, user=user, assignment=assignment)


@app.route('/add-assignments/<int:course_id>', methods=['GET'])
@authenticate
def list_assignments(user, course_id):
    assignments = find_user_assignments(user.id)
    return render_template('select_assignment.html', user=user, assignments=assignments, course_id=course_id)



@app.route('/edit-assignment/<int:assignment_id>', methods=['POST'])
@authenticate
def update_assignment(user, assignment_id):
    if user.role != 3:  # Assuming role 3 is an Instructor
        flash("Unauthorized access.")
        return redirect('/')
    
    assignment = getAssignmentsById(assignment_id, user)
    if not assignment or assignment.createdBy != user.id:
        flash("Assignment not found or access denied.")
        return redirect('/')
    
    # Grab form data
    name = request.form.get('name')
    start_date = request.form.get('startDate')
    end_date = request.form.get('endDate')
    is_public = request.form.get('isPublic') == 'on'


    # Assuming these functions exist and properly update the database
    success = update_assignment_details(assignment_id, name, start_date, end_date, is_public)
    if success:
        flash('Assignment successfully updated.')
        return redirect(f'/assignments/{assignment_id}')
    else:
        flash('Failed to update assignment.')
        return redirect(f'/edit-assignment/{assignment_id}')
    


@app.route('/edit-assignment/<int:assignment_id>', methods=['GET'])
@authenticate
def update_get_assignment(user, assignment_id):
    if user.role != 3:  # Assuming role 3 is an Instructor
        flash("Unauthorized access.")
        return redirect('/')
    
    assignment = getAssignmentsById(assignment_id, user)
    if not assignment or assignment.createdBy != user.id:
        flash("Assignment not found or access denied.")
        return redirect('/')
    
    testCases = get_test_Cases(True,assignment_id )
    
    return render_template(
            'edit-assignment.html',
            user=user,
            testCases=testCases,
            assignment=assignment,
            msg="")


@app.route('/create-assignment', methods=['GET'])
@authenticate
def get_create_assignment(user):
    # Check if the current user's role is 3 (Instructor)
    if user.role == 3:
        # User is an Instructor, show the create-assignment page
        return render_template('create-assignment.html', user=user)
    else:
        # User is not an Instructor, redirect to the home page
        return redirect('/')
    

@app.route('/add-assignment/<int:course_id>/<int:assignment_id>', methods=['GET'])
@authenticate
def add_assignment_to_course(user, course_id, assignment_id):
    # Assume `assign_to_course` is a function that creates or updates a record
    # linking the assignment to the course, potentially checking that
    # the user has permission to modify the course and owns the assignment.
    success = assign_to_course(course_id, assignment_id, user.id)
    if success:
        return redirect(f'/courses/{course_id}')  # Redirect back to the course details
    else:
        return "Error adding assignment", 400



@app.route('/submit-assignment/<int:assignment_id>', methods=['POST'])
@authenticate
def submit_assignment(user, assignment_id):
    # Check if the post request has the file part
    if 'assignment_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['assignment_file']
    
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if not file.filename.endswith(".c"):
        flash('Not a \'C\' file')
        return redirect(request.url)


    if file:
        original_filename = secure_filename(file.filename)
        # Define the path for the assignment folder
        assignment_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'assignment-{assignment_id}')
        # Define the path for the user's folder within the assignment folder
        user_folder = os.path.join(assignment_folder, f'user-{user.id}')

        # Check if the user's folder exists within the assignment folder, create it if it doesn't
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

        # Append user ID to the filename before its extension to ensure uniqueness
        filename, file_extension = os.path.splitext(original_filename)
        # unique_filename = f"{filename}_{user.id}{file_extension}"
        unique_filename = f"{filename}{file_extension}"
        
        # Save the file in the user's folder within the assignment folder with the unique filename
        file_path = os.path.join(user_folder, unique_filename)
        file.save(file_path)
        
        # Redirect or respond as necessary after file upload
        flash('File successfully uploaded')
        # Log the submission with the unique filename and path
        print("here")
        submission = addSubmissionLog(unique_filename, user, assignment_id)
        print("here2")
        # After saving the file, call the auto-grading function
        grade_submission(file_path, assignment_id, submission )
        
        return redirect(f'/assignments/{assignment_id}')
    
    return 'File upload failed', 400



@app.route('/toggle-visibility/<int:assignment_id>/<int:test_case_id>', methods=['POST'])
@authenticate
def toggle_visibility(user, assignment_id, test_case_id):
    # Ensure user is authorized to edit the assignment/test case (e.g., is the instructor)
    if user.role != 3:
        flash("You are not authorized to perform this action.")
        return redirect(url_for('get_assignment_details', assignmentId=assignment_id))

    # Find the test case and toggle its visibility
    togglevisiblity(test_case_id)
    

    return redirect(url_for('get_assignment_details', assignmentId=assignment_id))



@app.route('/confirm-assignment/<int:assignment_id>', methods=['GET'])
@authenticate
def confirm_assignment(user, assignment_id):
    # submit to moss
    submission_directory = os.path.join(app.config['UPLOAD_FOLDER'], f'assignment-{assignment_id}')
    file = submit_to_moss(submission_directory, assignment_id)  # This should be modified to handle and show any possible error properly
    return redirect(f'/assignments/{assignment_id}')



@app.route('/upload-testcase/<int:assignment_id>', methods=['POST'])
@authenticate
def upload_testcase(user, assignment_id):
    if 'testcase_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['testcase_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        testcase_folder = app.config['TESTCASE_FOLDER']
        
        # Ensure directory exists
        os.makedirs(testcase_folder, exist_ok=True)
        
        # Save file
        assignment_testcase_folder = os.path.join(testcase_folder, f'assignment-{assignment_id}')
        os.makedirs(assignment_testcase_folder, exist_ok=True)
        file_path = os.path.join(assignment_testcase_folder, filename)
        file.save(file_path)

        visible = 'visible' in request.form and request.form['visible'] == 'true'
        
        # Create or update TestCase and TestCaseFile entries
        addTestCaseLog(filename, user, assignment_id, visible, 100)

        flash('Test case file successfully uploaded')
        return redirect(f'/assignments/{assignment_id}')
    
    return 'File upload failed', 400


@app.route('/upload-testcase-file/<int:testcase_id>/<int:assignment_id>', methods=['POST'])
@authenticate
def upload_testcasefile(user, testcase_id, assignment_id):
    if 'testcase_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['testcase_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        testcase_folder = app.config['TESTCASE_FOLDER']
        
        # Ensure base testcase folder exists
        os.makedirs(testcase_folder, exist_ok=True)
        
        # Construct the path for the assignment's test case folder
        assignment_testcase_folder = os.path.join(testcase_folder, f'assignment-{assignment_id}', f'testcase-{testcase_id}')
        # Ensure the specific test case folder exists, create if not
        os.makedirs(assignment_testcase_folder, exist_ok=True)
        
        # Update file_path to include the specific test case folder
        file_path = os.path.join(assignment_testcase_folder, filename)
        file.save(file_path)

        # Assuming addTestCaseLog() is adapted to handle the TestCaseFile model creation
        # This function or a similar one should create a TestCaseFile entry linked to the testcase_id
        addTestCaseFileEntry(testcase_id, assignment_id, filename)

        flash('Test case file successfully uploaded')
        return redirect(f'/assignments/{assignment_id}')
    
    return 'File upload failed', 400

@app.route('/create-testcase/<int:assignment_id>', methods=['POST'])
@authenticate
def post_create_testcase(user, assignment_id):
    # Ensure the user creating the course is an instructor
    if user.role != 3:
        return redirect('/')
    
    success = create_testcase(assignment_id, user.id, True, 100)

    # Redirect based on the operation success
    if success:
        # Assuming you want to redirect to a page showing all courses or a confirmation page
        return redirect(f'/assignments/{assignment_id}')
    else:
        # Stay on the create course page and show an error message
        return redirect(f'/assignments/{assignment_id}')
    


@app.route('/create-assignment', methods=['POST'])
@authenticate
def post_create_assignment(user):
    # Ensure the user creating the course is an instructor
    if user.role != 3:
        return redirect('/')

    # Grab form data related to course creation
    name = request.form.get('name')
    start_date = request.form.get('startDate')
    end_date = request.form.get('endDate')

    # Convert start_date and end_date from string to datetime objects
    # Assuming date format in the form is 'YYYY-MM-DD'
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
    except ValueError:
        # Handle incorrect date format or other conversion errors
        return render_template('create-assignment.html', user=user, msg="Invalid date format.")

    success = create_assignment(name,start_date, end_date, user.id)

    # Redirect based on the operation success
    if success:
        return redirect('/assignments')
    else:
        # Stay on the create course page and show an error message
        return render_template('create-assignment.html', user=user, msg="Failed to create assignment.")
    

@app.route('/delete-testcase/<int:assignment_id>/<int:testcase_id>', methods=['GET'])
@authenticate
def delete_testcase(user, assignment_id, testcase_id):
    if user.role != 3:  # Assuming role 3 is an Instructor
        flash("Unauthorized access.")
        return redirect('/')
    
    assignment = getAssignmentsById(assignment_id, user)
    if not assignment or assignment.createdBy != user.id:
        flash("Assignment not found or access denied.")
        return redirect('/')
    
    # Assuming this function exists and properly deletes the test case from the database
    success = remove_testcase(testcase_id, assignment_id)
    
    if success:
        flash('Test case successfully deleted.')
    else:
        flash('Failed to delete test case.')
    
    return redirect(f'/assignments/{assignment_id}')


@app.route('/view-grade/<int:assignment_id>/<int:submission_id>')
@authenticate
def view_grade(user, assignment_id, submission_id):
    # Ensure that only authenticated users, TAs, and instructors can download submissions
    if user.role not in [2, 3]:
        #check if user is looking at its own work
        submission = Submission.query.filter_by(id=submission_id, assignmentId=assignment_id).first()
        if submission.userId != user.id:
        # Forbidden access attempt
            return make_response('Access denied', 403)
        

    # Fetch the submission based on submission_id, user_id, and assignment_id
    submission = Submission.query.filter_by(id=submission_id, assignmentId=assignment_id).first()

    submissionResults = getSubmissionResults(submission_id, submission)
    
    student = findUserById(submission.userId)

    return render_template('view-grades.html',
                           message='', user=user, student=student, submissionResults=submissionResults )




@app.route('/download-submission/<int:assignment_id>/<int:submission_id>')
@authenticate
def download_submission(user, assignment_id, submission_id):
    # Ensure that only authenticated users, TAs, and instructors can download submissions
    if user.role not in [2, 3]:
        #check if user is looking at its own work
        submission = Submission.query.filter_by(id=submission_id, assignmentId=assignment_id).first()
        if submission.userId != user.id:
        # Forbidden access attempt
            return make_response('Access denied', 403)

    # Fetch the submission based on submission_id, user_id, and assignment_id
    submission = Submission.query.filter_by(id=submission_id, assignmentId=assignment_id).first()
    
    if submission:
        # Adjust the directory path to include the user-specific folder
        directory = os.path.join(app.config['UPLOAD_FOLDER'], f'assignment-{assignment_id}', f'user-{submission.userId}')
        
        # Attempt to send the file from the directory
        try:
            return send_from_directory(directory, submission.fileName, as_attachment=True)
        except FileNotFoundError:
            # File not found
            return make_response('File not found', 404)
    return 'Submission not found', 404

@app.route('/download-grades/<int:assignment_id>')
@authenticate
def download_grades(user, assignment_id):
    # Ensure that only instructors can download grades
    if user.role not in [2, 3]:
        return make_response('Access denied', 403)

    grades = getGrades(assignment_id)

    # Generate CSV
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Student ID', 'Total Score', 'Max Score'])
    for grade in grades:
        cw.writerow([grade['student_id'], grade['score'], grade['total_possible_score']])

    response = Response(si.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=grades_assignment_{assignment_id}.csv'
    return response