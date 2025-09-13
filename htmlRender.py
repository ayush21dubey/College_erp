from flask import Flask, render_template, redirect, request, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import os
import threading
import time
from datetime import datetime
import json

# Import our database and scraping modules
from connectdb import init_db, get_student, add_student, update_student_attendance, add_attendance_records, get_student_stats, log_login, get_db_connection

try:
    from scrapp import scrape_student_data
    SCRAPING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Scraping module not available: {e}")
    SCRAPING_AVAILABLE = False
    def scrape_student_data(roll_number, password):
        return None

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Initialize database
init_db()

# Store scraping status for each user
scraping_status = {}

def create_sample_data(roll_number):
    """Create sample data for testing when scraping is not available"""
    return {
        'student_info': {
            'name': f'Student {roll_number}',
            'institution': 'Shri Ramswaroop Memorial GPC',
            'academic_career': 'Undergraduate',
            'term': 'Semester 1 year 2501 UG/PG',
            'total_attendance_percent': 85.5,
            'medical_attendance_percent': 90.0,
            'attendance_percent': 87.5
        },
        'records': [
            {
                'class_number': 'CS101',
                'class_title': 'Data Analytics',
                'subject_catalog': 'CS BCS-052',
                'academic_career': 'Undergraduate',
                'institution': 'Shri Ramswaroop Memorial GPC',
                'attendance_percentage': 88.5
            },
            {
                'class_number': 'CS102',
                'class_title': 'Machine Learning Techniques',
                'subject_catalog': 'CS BCS-055',
                'academic_career': 'Undergraduate',
                'institution': 'Shri Ramswaroop Memorial GPC',
                'attendance_percentage': 92.0
            },
            {
                'class_number': 'CS103',
                'class_title': 'Database Management System',
                'subject_catalog': 'CS BCS-501',
                'academic_career': 'Undergraduate',
                'institution': 'Shri Ramswaroop Memorial GPC',
                'attendance_percentage': 75.5
            }
        ],
        'total_attendance': 85.5,
        'medical_attendance': 90.0
    }

def scrape_data_background(roll_number, password):
    """Background task to scrape student data"""
    try:
        scraping_status[roll_number] = {'status': 'scraping', 'progress': 0}
        
        # Check if scraping is available
        if not SCRAPING_AVAILABLE:
            # Create sample data for testing
            scraping_status[roll_number]['progress'] = 50
            scraped_data = create_sample_data(roll_number)
        else:
            # Simulate scraping process
            scraping_status[roll_number]['progress'] = 25
            
            # Call the actual scraping function
            scraped_data = scrape_student_data(roll_number, password)
        
        if scraped_data:
            # Get student from database
            student = get_student(roll_number)
            if student:
                # Update student info with scraped data
                student_info = scraped_data.get('student_info', {})
                if student_info:
                    # Update student details in database
                    conn = get_db_connection()
                    conn.execute('''
                        UPDATE students 
                        SET name = ?, institution = ?, academic_career = ?, term = ?,
                            total_attendance_percent = ?, medical_attendance_percent = ?
                        WHERE roll_number = ?
                    ''', (
                        student_info.get('name', student['name']),
                        student_info.get('institution', student['institution']),
                        student_info.get('academic_career', student['academic_career']),
                        student_info.get('term', student['term']),
                        scraped_data.get('total_attendance', 0),
                        scraped_data.get('medical_attendance', 0),
                        roll_number
                    ))
                    conn.commit()
                    conn.close()
                
                # Add attendance records
                records = scraped_data.get('records', [])
                add_attendance_records(student['id'], records)
                
                scraping_status[roll_number] = {'status': 'completed', 'progress': 100}
            else:
                scraping_status[roll_number] = {'status': 'error', 'message': 'Student not found in database'}
        else:
            scraping_status[roll_number] = {'status': 'error', 'message': 'Failed to scrape data'}
            
    except Exception as e:
        scraping_status[roll_number] = {'status': 'error', 'message': str(e)}

@app.route('/')
def login():
    """Render login page"""
    return render_template('login.html')

@app.route('/login_handler', methods=['POST'])
def login_handler():
    """Handle login form submission"""
    roll_number = request.form.get('sid', '').strip()
    password = request.form.get('password', '').strip()
    
    if not roll_number or not password:
        flash('Please enter both roll number and password', 'error')
        return redirect(url_for('login'))
    
    # Check if student exists in database
    student = get_student(roll_number)
    
    if not student:
        # Try to add new student with hashed password
        hashed_password = generate_password_hash(password)
        if not add_student(roll_number, hashed_password):
            flash('Invalid credentials. Please check your roll number and password.', 'error')
            return redirect(url_for('login'))
        student = get_student(roll_number)
    
    # Verify password
    if not check_password_hash(student['password'], password):
        flash('Invalid credentials. Please check your roll number and password.', 'error')
        return redirect(url_for('login'))
    
    # Log the login
    log_login(student['id'], request.remote_addr, request.headers.get('User-Agent', ''))
    
    # Store student info in session
    session['student_id'] = student['id']
    session['roll_number'] = roll_number
    session['student_name'] = student['name'] or 'Student'
    
    # Start background scraping
    scraping_thread = threading.Thread(target=scrape_data_background, args=(roll_number, password))
    scraping_thread.daemon = True
    scraping_thread.start()
    
    return redirect(url_for('attendance_page'))

@app.route('/attendance')
def attendance_page():
    """Render attendance page"""
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    student_id = session['student_id']
    stats = get_student_stats(student_id)
    
    if not stats['student']:
        flash('Student data not found', 'error')
        return redirect(url_for('login'))
    
    return render_template('attendance.html', 
                         student=stats['student'],
                         attendance_records=stats['attendance_records'],
                         login_history=stats['login_history'])

@app.route('/scraping_status')
def get_scraping_status():
    """Get scraping status for current user"""
    if 'roll_number' not in session:
        return jsonify({'error': 'Not logged in'})
    
    roll_number = session['roll_number']
    status = scraping_status.get(roll_number, {'status': 'not_started'})
    return jsonify(status)

@app.route('/refresh_data')
def refresh_data():
    """Refresh student data by re-scraping"""
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    roll_number = session['roll_number']
    password = request.form.get('password', '')
    
    if not password:
        flash('Please enter your password to refresh data', 'error')
        return redirect(url_for('attendance_page'))
    
    # Start background scraping
    scraping_thread = threading.Thread(target=scrape_data_background, args=(roll_number, password))
    scraping_thread.daemon = True
    scraping_thread.start()
    
    flash('Data refresh started. Please wait a moment and refresh the page.', 'info')
    return redirect(url_for('attendance_page'))

@app.route('/dashboard')
def dashboard():
    """Render analytics dashboard"""
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    student_id = session['student_id']
    stats = get_student_stats(student_id)
    
    if not stats['student']:
        flash('Student data not found', 'error')
        return redirect(url_for('login'))
    
    # Calculate some analytics
    records = stats['attendance_records']
    total_subjects = len(records)
    high_attendance = len([r for r in records if r['attendance_percentage'] >= 80])
    low_attendance = len([r for r in records if r['attendance_percentage'] < 75])
    
    analytics = {
        'total_subjects': total_subjects,
        'high_attendance': high_attendance,
        'low_attendance': low_attendance,
        'average_attendance': sum(r['attendance_percentage'] for r in records) / total_subjects if total_subjects > 0 else 0
    }
    
    return render_template('dashboard.html', 
                         student=stats['student'],
                         analytics=analytics,
                         attendance_records=records)

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/api/attendance_data')
def api_attendance_data():
    """API endpoint for attendance data"""
    if 'student_id' not in session:
        return jsonify({'error': 'Not logged in'})
    
    student_id = session['student_id']
    stats = get_student_stats(student_id)
    
    return jsonify({
        'student': stats['student'],
        'attendance_records': stats['attendance_records']
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)