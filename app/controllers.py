from flask import render_template, request, session, redirect,  url_for, flash, send_from_directory, abort, make_response
from app.models import addSubmissionLog, addTestCaseLog, assign_to_course,Course, create_assignment, create_course, enrollInCourse, enrollTaInCourse, find_assignments, find_courses, find_user_assignments, findUserById, get_test_Cases, get_user_submissions_for_assignment, getAssignmentsById, getAssignmentsForCourse, getCourseById, getSubmissions, getUsersForCourse, login, Submission, User, register, remove_testcase, update_assignment_details, update_user
from app import app
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from functools import wraps


def authenticate(inner_function):
    @wraps(inner_function)
    def wrapped_inner(*args, **kwargs):
        # check did we store the key in the session
        if 'logged_in' in session:
            email = session['logged_in']
            try:
                user = User.query.filter_by(email=email).one_or_none()
                if user:
                    # if the user exists, call the inner_function
                    # with user as parameter and any arguments it needs
                    return inner_function(user, *args, **kwargs)
            except Exception as e:
                # It's a good idea to log the exception here
                pass
        else:
            # else, redirect to the login page
            return redirect('/login')
    return wrapped_inner



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

@app.route('/view-grade/<int:submission_id>')
@authenticate
def view_grade(user, submission_id):
    # Ensure that only authenticated users, TAs, and instructors can download submissions
    if user.role not in [2, 3]:
        #check if user is looking at its own work
        submission = Submission.query.filter_by(id=submission_id).first()
        if submission.userId != user.id:
        # Forbidden access attempt
            return make_response('Access denied', 403)
    
    submission = Submission.query.filter_by(id=submission_id).first()

    student = findUserById(submission.userId)

    return render_template('view-grades.html',
                           message='', user=user, student=student )





@app.route('/login', methods=['GET'])
def login_get():
    return render_template('login.html',
                           message='Please login to your account')


@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    user = login(email, password)
    if user:
        session['logged_in'] = user.email
        """
        Session is an object that contains sharing information
        between a user's browser and the end server.
        Typically it is packed and stored in the browser cookies.
        They will be past along between every request the browser made
        to this services. Here we store the user object into the
        session, so we can tell if the client has already login
        in the following sessions.
        """
        # success! go back to the home page
        # code 303 is to force a 'GET' request
        return redirect('/', code=303)
    else:
        return render_template('login.html',
                               message='Incorrect email or password.')


@app.route('/assignments', methods=['GET'])
@authenticate
def get_assignments(user):
    assignments = find_assignments(user)
    print(assignments)
    return render_template('assignments.html',  assignments=assignments, user=user)


@app.route('/')
@authenticate
def home(user):
    courses = find_courses(user)
    return render_template('index.html',  courses=courses, user=user)


@app.route('/register', methods=['GET'])
def register_get():
    # templates are stored in the templates folder
    return render_template('register.html', message='')


@app.route('/register', methods=['POST'])
def register_post():
    email = request.form.get('email')
    name = request.form.get('name')
    student_number = request.form.get('student-number')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    role = request.form.get('role')
    error_message = None

    if password != password2:
        error_message = "The passwords do not match."
    else:
        # use backend api to register the user
        success = register(name, email, student_number, password, role)
        if not success:
            error_message = "Registration failed."
    # if there is any error messages when registering new user
    # at the backend, go back to the register page.
    if error_message:
        return render_template('register.html', message=error_message)
    else:
        return redirect('/login')


@app.route('/logout')
def logout():
    if 'logged_in' in session:
        session.pop('logged_in', None)
    return redirect('/')


# Route to send the user update template
@app.route('/update-user', methods=['GET'])
@authenticate
def get_update_user(user):
    # Return the template with the user's current information
    return render_template(
        'update_user.html',
        user=user,
        msg="Please modify the information you want to update below.")

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

    # Assuming these functions exist and properly update the database
    success = update_assignment_details(assignment_id, name, start_date, end_date)
    
    if success:
        flash('Assignment successfully updated.')
        return redirect(f'/assignments/{assignment_id}')
    else:
        flash('Failed to update assignment.')
        return redirect(f'/edit-assignment/{assignment_id}')

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
    
@app.route('/courses/<int:courseId>', methods=['GET'])
@authenticate
def get_course_details(user, courseId):
    course = getCourseById(courseId, user)
    assignments = getAssignmentsForCourse(courseId, user)
    users = getUsersForCourse(courseId, user)
    if course == None:
        return redirect('/')

    return render_template('course-details.html', users=users, user=user, course=course, assignments=assignments)

@app.route('/assignments/<int:assignmentId>', methods=['GET'])
@authenticate
def get_assignment_details(user, assignmentId):
    assignment = getAssignmentsById(assignmentId, user)
    if assignment == None:
        return redirect('/')

    isOwner = assignment.createdBy == user.id
    submissions = get_user_submissions_for_assignment(user.id, assignmentId)
    testCases = get_test_Cases(isOwner,assignmentId )
    return render_template('assignment-details.html', testCases=testCases, submissions=submissions,isOwner=isOwner, user=user, assignment=assignment)

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


@app.route('/add-assignments/<int:course_id>', methods=['GET'])
@authenticate
def list_assignments(user, course_id):
    assignments = find_user_assignments(user.id)
    return render_template('select_assignment.html', user=user, assignments=assignments, course_id=course_id)

@app.route('/users/<int:user_id>/<int:course_id>')
@authenticate
def user_details(user, user_id, course_id):
    # Ensure only TAs and instructors can view this page
    if user.role not in [2, 3]:
        return ('/')
    
    student = findUserById(user_id)
    course = getCourseById(course_id, user)
    submissions = getSubmissions(course_id, user_id)

    return render_template('user_details.html', student=student, user=user, course=course, submissions=submissions)


@app.route('/add-ta/<int:course_id>', methods=['GET', 'POST'])
@authenticate
def add_ta(user, course_id):
    course = getCourseById(course_id, user)
    if request.method == 'POST':
        ta_email = request.form['taEmail']
        result = enrollTaInCourse(course_id, user, ta_email)
        return redirect(f'/courses/{course_id}')
    
    return render_template('add_ta.html', user=user, course=course)


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

    # Call your function to create a new course instance in the database
    # Assuming such a function exists and is named 'create_course'
    success = create_assignment(name,start_date, end_date, user.id)

    # Redirect based on the operation success
    if success:
        # Assuming you want to redirect to a page showing all courses or a confirmation page
        return redirect('/assignments')
    else:
        # Stay on the create course page and show an error message
        return render_template('create-assignment.html', user=user, msg="Failed to create assignment.")


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
        addSubmissionLog(unique_filename, user, assignment_id)
        return redirect(f'/assignments/{assignment_id}')
    
    # Handle cases where file upload does not succeed
    return 'File upload failed', 400


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
        
        # Assuming each assignment's test cases are stored in a specific subdirectory
        assignment_testcase_folder = os.path.join(testcase_folder, f'assignment-{assignment_id}')
        os.makedirs(assignment_testcase_folder, exist_ok=True)
        
        file_path = os.path.join(assignment_testcase_folder, filename)
        file.save(file_path)

        visible = 'visible' in request.form and request.form['visible'] == 'true'
        
        flash('Test case file successfully uploaded')
        addTestCaseLog(filename, user, assignment_id, visible)
        return redirect(f'/assignments/{assignment_id}')
    
    return 'File upload failed', 400
