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


@app.route('/admin/create-user', methods=['GET', 'POST'])
@authenticate
def admin_create_user(user):
    if user.role != 4:  # Check if user is admin
        return abort(403)

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']  # Consider hashing the password
        student_number = request.form.get('student_number', None)
        role = int(request.form['role'])

        # Create and save the new user
        new_user = User(username=username, email=email, password=password, 
                        student_number=student_number, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('User created successfully.', 'success')
        return redirect('/admin/users')

    return render_template('admin_create_user.html', user=user)

@app.route('/admin/users', methods=['GET'])
@authenticate
def admin_users(user):
    if user.role != 4:  # Check if user is admin
        return abort(403)

    users = User.query.all()
    return render_template('admin_users.html', users=users, user=user)


@app.route('/admin/user-courses/<int:user_id>', methods=['GET'])
@authenticate
def admin_user_courses(user, user_id):
    if user.role != 4:
        return abort(403)

    user_courses = Course.query.join(UserCourse, UserCourse.courseId == Course.id).filter(UserCourse.userId == user_id).all()
    all_courses = Course.query.all()  # For adding to a course
    return render_template('admin_user_courses.html', user=user, user_courses=user_courses, user_id=user_id, all_courses=all_courses)


@app.route('/admin/remove-user-from-course/<int:user_id>/<int:course_id>', methods=['POST'])
@authenticate
def admin_remove_user_from_course(user, user_id, course_id):
    if user.role != 4:
        return abort(403)
    
    user_course = UserCourse.query.filter_by(userId=user_id, courseId=course_id).first()
    if user_course:
        db.session.delete(user_course)
        db.session.commit()
        flash('User removed from course successfully.', 'success')
    return redirect(url_for('admin_user_courses', user_id=user_id))


@app.route('/admin/add-user-to-course/<int:user_id>', methods=['POST'])
@authenticate
def admin_add_user_to_course(user, user_id):
    if user.role != 4:
        return abort(403)

    course_id = request.form.get('course_id')
    if not course_id:
        # Handle the error appropriately, perhaps by flashing a message or logging
        return redirect(url_for('admin_user_courses', user_id=user_id))

    # Convert course_id to int
    course_id = int(course_id)

    # Proceed with the original logic to add the user to the course
    # Check if the user is already enrolled in the course
    existing_enrollment = UserCourse.query.filter_by(courseId=course_id, userId=user_id).first()
    if existing_enrollment:
        # Handle this case appropriately, e.g., flash a message
        return redirect(url_for('admin_user_courses', user_id=user_id))

    # Add the user to the course
    user_course = UserCourse(courseId=course_id, userId=user_id, userRole=1)  # Adjust userRole as needed
    db.session.add(user_course)
    db.session.commit()

    # Redirect back to the user's courses page
    return redirect(url_for('admin_user_courses', user=user, user_id=user_id))



@app.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@authenticate
def admin_edit_user(user, user_id):
    if user.role != 4:
        return abort(403)

    user_to_edit = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user_to_edit.username = request.form['username']
        user_to_edit.email = request.form['email']
        # Consider adding password update logic here
        user_to_edit.student_number = request.form.get('student_number', None)
        user_to_edit.role = int(request.form['role'])

        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect('/admin/users')

    return render_template('admin_edit_user.html', user_to_edit=user_to_edit, user=user)

@app.route('/contact-admin', methods=['GET', 'POST'])
@authenticate 
def contact_admin(user):
    if request.method == 'POST':
        issue_name = request.form['issue_name']
        issue_description = request.form['issue_description']
        category = request.form['category']
        user_id = user.id  # Assuming you're using Flask-Login or similar for user management

        help_request = HelpRequest(
            issue_name=issue_name,
            issue_description=issue_description,
            category=category,
            user_id=user_id
        )
        db.session.add(help_request)
        db.session.commit()

        # Here, handle sending the email/notification as required
        flash('Your request has been submitted successfully.', 'success')
        return redirect('/')  # Redirect to a different page as appropriate

    return render_template('contact_admin.html', user=user)

@app.route('/admin/delete-request/<int:request_id>', methods=['POST'])
@authenticate
def admin_delete_request(user, request_id):
    if user.role != 4:  # Ensure the user is an admin
        return abort(403)

    help_request = HelpRequest.query.get_or_404(request_id)
    db.session.delete(help_request)
    db.session.commit()

    flash('Help request deleted successfully.', 'success')
    return redirect(url_for('admin_view_requests'))


@app.route('/admin/requests', methods=['GET'])
@authenticate
def admin_view_requests(user):
    if user.role != 4:  # Ensure the user is an admin
        return abort(403)
    
    # Fetch all help requests and the email of the user who made each request
    help_requests = db.session.query(HelpRequest, User.email).join(User, HelpRequest.user_id == User.id).all()
    
    return render_template('admin_view_requests.html', user=user, help_requests=help_requests)




@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@authenticate
def admin_delete_user(user, user_id):
    if user.role != 4:
        return abort(403)

    user_to_delete = User.query.get_or_404(user_id)
    db.session.delete(user_to_delete)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect('/admin/users')
