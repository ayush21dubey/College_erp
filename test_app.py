#!/usr/bin/env python3
"""
Test script for the Student ERP System
This script tests the database functionality and basic app components
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from connectdb import init_db, add_student, get_student, update_student_attendance, add_attendance_records, get_student_stats
from werkzeug.security import generate_password_hash, check_password_hash

def test_database():
    """Test database operations"""
    print("🧪 Testing Database Operations...")
    
    # Initialize database
    print("1. Initializing database...")
    init_db()
    print("✅ Database initialized successfully")
    
    # Test adding a student
    print("2. Testing student creation...")
    test_roll = "BE23CS999"
    test_password = "test123"
    hashed_password = generate_password_hash(test_password)
    
    # Add student
    result = add_student(test_roll, hashed_password, "Test Student", "Test Institution", "Undergraduate", "Test Term")
    if result:
        print("✅ Student added successfully")
    else:
        print("❌ Failed to add student")
        return False
    
    # Test getting student
    print("3. Testing student retrieval...")
    student = get_student(test_roll)
    if student:
        print(f"✅ Student retrieved: {student['name']}")
    else:
        print("❌ Failed to retrieve student")
        return False
    
    # Test password verification
    print("4. Testing password verification...")
    if check_password_hash(student['password'], test_password):
        print("✅ Password verification successful")
    else:
        print("❌ Password verification failed")
        return False
    
    # Test updating attendance
    print("5. Testing attendance update...")
    update_student_attendance(test_roll, 85.5, 90.0)
    updated_student = get_student(test_roll)
    if updated_student['total_attendance_percent'] == 85.5:
        print("✅ Attendance update successful")
    else:
        print("❌ Attendance update failed")
        return False
    
    # Test adding attendance records
    print("6. Testing attendance records...")
    test_records = [
        {
            'class_number': 'CS101',
            'class_title': 'Test Subject 1',
            'subject_catalog': 'CS-101',
            'academic_career': 'Undergraduate',
            'institution': 'Test Institution',
            'attendance_percentage': 88.5
        },
        {
            'class_number': 'CS102',
            'class_title': 'Test Subject 2',
            'subject_catalog': 'CS-102',
            'academic_career': 'Undergraduate',
            'institution': 'Test Institution',
            'attendance_percentage': 92.0
        }
    ]
    
    result = add_attendance_records(student['id'], test_records)
    if result:
        print("✅ Attendance records added successfully")
    else:
        print("❌ Failed to add attendance records")
        return False
    
    # Test getting student stats
    print("7. Testing student stats...")
    stats = get_student_stats(student['id'])
    if stats['student'] and len(stats['attendance_records']) == 2:
        print("✅ Student stats retrieved successfully")
        print(f"   - Student: {stats['student']['name']}")
        print(f"   - Total Attendance: {stats['student']['total_attendance_percent']}%")
        print(f"   - Records: {len(stats['attendance_records'])}")
    else:
        print("❌ Failed to retrieve student stats")
        return False
    
    print("\n🎉 All database tests passed!")
    return True

def test_scraping_module():
    """Test scraping module imports and basic functionality"""
    print("\n🧪 Testing Scraping Module...")
    
    try:
        from scrapp import scrape_student_data, extract_student_info, extract_attendance_records
        print("✅ Scraping module imported successfully")
        
        # Test data extraction functions with mock data
        from bs4 import BeautifulSoup
        
        # Mock HTML for testing
        mock_html = """
        <html>
            <body>
                <span id="PERSONAL_DTSAVW_NAME">TEST STUDENT</span>
                <span id="INSTITUTION_TBL_DESCR">Test Institution</span>
                <span id="ACAD_CAR_TBL_DESCR">Undergraduate</span>
                <span id="TERM_VAL_TBL_DESCR">Test Term</span>
                <span id="SRM_LEAVE_WRK_AMOUNT_DUE">85.5</span>
                <span id="SRM_LEAVE_WRK_AMOUNT_DIFF">90.0</span>
                <span id="SRM_CLAS_PER_DR_TOTAL_PERCENT">87.5</span>
                <table id="STDNT_ENRL$0">
                    <tbody>
                        <tr>
                            <td>CS101</td>
                            <td>Test Subject</td>
                            <td>CS-101</td>
                            <td>Undergraduate</td>
                            <td>Test Institution</td>
                            <td>88.5</td>
                        </tr>
                    </tbody>
                </table>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(mock_html, 'html.parser')
        
        # Test student info extraction
        student_info = extract_student_info(soup)
        if student_info.get('name') == 'TEST STUDENT':
            print("✅ Student info extraction working")
        else:
            print("❌ Student info extraction failed")
            return False
        
        # Test attendance records extraction
        records = extract_attendance_records(soup)
        if len(records) == 1 and records[0]['class_number'] == 'CS101':
            print("✅ Attendance records extraction working")
        else:
            print("❌ Attendance records extraction failed")
            return False
        
        print("🎉 Scraping module tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import scraping module: {e}")
        return False
    except Exception as e:
        print(f"❌ Scraping module test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Student ERP System Tests\n")
    
    # Test database
    db_success = test_database()
    
    # Test scraping module
    scraping_success = test_scraping_module()
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    print(f"Database Tests: {'✅ PASSED' if db_success else '❌ FAILED'}")
    print(f"Scraping Tests: {'✅ PASSED' if scraping_success else '❌ FAILED'}")
    
    if db_success and scraping_success:
        print("\n🎉 ALL TESTS PASSED! The application is ready to use.")
        print("\nTo start the application, run:")
        print("python htmlRender.py")
        print("\nThen open http://localhost:5000 in your browser")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
