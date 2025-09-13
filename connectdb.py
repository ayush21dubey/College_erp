import sqlite3
import os
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('student_erp.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = get_db_connection()
    
    # Create students table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            institution TEXT,
            academic_career TEXT,
            term TEXT,
            total_attendance_percent REAL,
            medical_attendance_percent REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create attendance_records table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            class_number TEXT,
            class_title TEXT,
            subject_catalog TEXT,
            academic_career TEXT,
            institution TEXT,
            attendance_percentage REAL,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')
    
    # Create login_logs table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_student(roll_number, password, name=None, institution=None, academic_career=None, term=None):
    """Add a new student to the database"""
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO students (roll_number, password, name, institution, academic_career, term)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (roll_number, password, name, institution, academic_career, term))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_student(roll_number):
    """Get student by roll number"""
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE roll_number = ?', (roll_number,)).fetchone()
    conn.close()
    return student

def update_student_attendance(roll_number, total_attendance, medical_attendance):
    """Update student's attendance percentages"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE students 
        SET total_attendance_percent = ?, medical_attendance_percent = ?
        WHERE roll_number = ?
    ''', (total_attendance, medical_attendance, roll_number))
    conn.commit()
    conn.close()

def add_attendance_records(student_id, records):
    """Add attendance records for a student"""
    conn = get_db_connection()
    try:
        # Clear existing records for this student
        conn.execute('DELETE FROM attendance_records WHERE student_id = ?', (student_id,))
        
        # Insert new records
        for record in records:
            conn.execute('''
                INSERT INTO attendance_records 
                (student_id, class_number, class_title, subject_catalog, academic_career, institution, attendance_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, record['class_number'], record['class_title'], 
                  record['subject_catalog'], record['academic_career'], 
                  record['institution'], record['attendance_percentage']))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding attendance records: {e}")
        return False
    finally:
        conn.close()

def get_attendance_records(student_id):
    """Get attendance records for a student"""
    conn = get_db_connection()
    records = conn.execute('''
        SELECT * FROM attendance_records 
        WHERE student_id = ? 
        ORDER BY class_number
    ''', (student_id,)).fetchall()
    conn.close()
    return records

def log_login(student_id, ip_address, user_agent):
    """Log student login"""
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO login_logs (student_id, ip_address, user_agent)
        VALUES (?, ?, ?)
    ''', (student_id, ip_address, user_agent))
    
    # Update last login time
    conn.execute('''
        UPDATE students SET last_login = CURRENT_TIMESTAMP WHERE id = ?
    ''', (student_id,))
    
    conn.commit()
    conn.close()

def get_student_stats(student_id):
    """Get comprehensive stats for a student"""
    conn = get_db_connection()
    
    # Get student info
    student = conn.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
    
    # Get attendance records
    records = conn.execute('''
        SELECT * FROM attendance_records 
        WHERE student_id = ? 
        ORDER BY attendance_percentage DESC
    ''', (student_id,)).fetchall()
    
    # Get login history
    login_history = conn.execute('''
        SELECT login_time FROM login_logs 
        WHERE student_id = ? 
        ORDER BY login_time DESC 
        LIMIT 10
    ''', (student_id,)).fetchall()
    
    conn.close()
    
    return {
        'student': dict(student) if student else None,
        'attendance_records': [dict(record) for record in records],
        'login_history': [dict(login) for login in login_history]
    }

# Initialize database when module is imported
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
