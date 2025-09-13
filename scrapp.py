# pandas import moved to function level to avoid import errors

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
import csv
from werkzeug.security import generate_password_hash

# ##############################################################################
# CONFIGURATION
# ##############################################################################

LOGIN_URL = "https://campus.srmcem.ac.in/psp/ps/?cmd=login"
ATTENDANCE_URL = "https://campus.srmcem.ac.in/psp/ps/EMPLOYEE/HRMS/c/MANAGE_ACADEMIC_RECORDS.STDNT_ATTEND_TERM.GBL"

def scrape_student_data(roll_number, password):
    """
    Scrape attendance data for a single student
    Returns a dictionary with student info and attendance records
    """
    driver = None
    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize Chrome
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 30)

        print(f"Scraping data for {roll_number}...")
        driver.get(LOGIN_URL)

        # --- 1. LOG IN ---
        username_field = wait.until(EC.presence_of_element_located((By.ID, "userid")))
        password_field = driver.find_element(By.ID, "pwd")
        login_button = driver.find_element(By.NAME, "Submit")

        username_field.send_keys(roll_number)
        password_field.send_keys(password)
        login_button.click()

        # Wait for dashboard
        wait.until(EC.presence_of_element_located((By.ID, "pthnavcontainer")))
        print("Login successful. Navigating to attendance page...")

        driver.get(ATTENDANCE_URL)

        # --- 2. HANDLE IFRAMES ---
        time.sleep(5)  # allow page to settle
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print("Total iframes found:", len(iframes))

        # Try switching to the first main iframe
        try:
            driver.switch_to.frame("ptifrmtgtframe")
            print("Switched to iframe: ptifrmtgtframe")
        except:
            print("No iframe with id='ptifrmtgtframe'. Trying first iframe...")
            if len(iframes) > 0:
                driver.switch_to.frame(iframes[0])
                print("Switched to first iframe.")

        # --- 3. WAIT FOR TABLE ---
        Result = driver.find_element(By.ID, "RESULT3$0")
        Result.click()
        print("Waiting for attendance table...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//table[contains(@id,'STDNT_ENRL')]")))
        print("Attendance table found!")

        # --- 4. SCRAPE DATA ---
        page_html = driver.page_source
        soup = BeautifulSoup(page_html, "html.parser")
        
        # Extract student information
        student_info = extract_student_info(soup)
        
        # Extract attendance records
        attendance_records = extract_attendance_records(soup)
        
        # Save debug page
        with open(f"debug_page_{roll_number}.html", "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"Saved debug_page_{roll_number}.html for inspection.")

        return {
            'student_info': student_info,
            'records': attendance_records,
            'total_attendance': student_info.get('total_attendance_percent', 0),
            'medical_attendance': student_info.get('medical_attendance_percent', 0)
        }

    except Exception as e:
        print(f"An error occurred while scraping data for {roll_number}: {e}")
        return None

    finally:
        if driver:
            driver.quit()
        print("Browser closed.")

def extract_student_info(soup):
    """Extract student information from the page"""
    student_info = {}
    
    try:
        # Extract student name
        name_element = soup.find("span", {"id": "PERSONAL_DTSAVW_NAME"})
        if name_element:
            student_info['name'] = name_element.text.strip()
        
        # Extract institution
        institution_element = soup.find("span", {"id": "INSTITUTION_TBL_DESCR"})
        if institution_element:
            student_info['institution'] = institution_element.text.strip()
        
        # Extract academic career
        career_element = soup.find("span", {"id": "ACAD_CAR_TBL_DESCR"})
        if career_element:
            student_info['academic_career'] = career_element.text.strip()
        
        # Extract term
        term_element = soup.find("span", {"id": "TERM_VAL_TBL_DESCR"})
        if term_element:
            student_info['term'] = term_element.text.strip()
        
        # Extract total attendance percentage
        total_attendance_element = soup.find("span", {"id": "SRM_LEAVE_WRK_AMOUNT_DUE"})
        if total_attendance_element:
            try:
                student_info['total_attendance_percent'] = float(total_attendance_element.text.strip())
            except:
                student_info['total_attendance_percent'] = 0
        
        # Extract medical attendance percentage
        medical_attendance_element = soup.find("span", {"id": "SRM_LEAVE_WRK_AMOUNT_DIFF"})
        if medical_attendance_element:
            try:
                student_info['medical_attendance_percent'] = float(medical_attendance_element.text.strip())
            except:
                student_info['medical_attendance_percent'] = 0
        
        # Extract attendance percentage
        attendance_element = soup.find("span", {"id": "SRM_CLAS_PER_DR_TOTAL_PERCENT"})
        if attendance_element:
            try:
                student_info['attendance_percent'] = float(attendance_element.text.strip())
            except:
                student_info['attendance_percent'] = 0
                
    except Exception as e:
        print(f"Error extracting student info: {e}")
    
    return student_info

def extract_attendance_records(soup):
    """Extract attendance records from the table"""
    records = []
    
    try:
        data_table = soup.find("table", {"id": lambda x: x and "STDNT_ENRL" in x})
        
        if data_table:
            rows = data_table.find("tbody").find_all("tr") if data_table.find("tbody") else data_table.find_all("tr")[1:]
            
            for row in rows:
                columns = row.find_all("td")
                if len(columns) >= 6:
                    try:
                        # Extract class number
                        class_number = columns[0].text.strip()
                        
                        # Extract class title
                        class_title = columns[1].text.strip()
                        
                        # Extract subject/catalog
                        subject_catalog = columns[2].text.strip()
                        
                        # Extract academic career
                        academic_career = columns[3].text.strip()
                        
                        # Extract institution
                        institution = columns[4].text.strip()
                        
                        # Extract attendance percentage
                        attendance_percentage = 0
                        try:
                            attendance_text = columns[5].text.strip()
                            attendance_percentage = float(attendance_text)
                        except:
                            attendance_percentage = 0
                        
                        record = {
                            "class_number": class_number,
                            "class_title": class_title,
                            "subject_catalog": subject_catalog,
                            "academic_career": academic_career,
                            "institution": institution,
                            "attendance_percentage": attendance_percentage
                        }
                        records.append(record)
                        
                    except Exception as e:
                        print(f"Error processing row: {e}")
                        continue
            
            print(f"Successfully extracted {len(records)} attendance records")
        else:
            print("Could not find attendance table")
            
    except Exception as e:
        print(f"Error extracting attendance records: {e}")
    
    return records

def batch_scrape_all_students():
    """
    Batch scrape all students from the original credentials list
    This is kept for backward compatibility
    """
    credentials_list = [
        {"username": "BE23CS060", "password": "212004"},
        {"username": "BE23CS013", "password": "288"},
    ]
    
    scraped_data_from_all_accounts = []
    
    for credentials in credentials_list:
        print(f"--- Processing user: {credentials['username']} ---")
        
        result = scrape_student_data(credentials["username"], credentials["password"])
        
        if result and result['records']:
            for record in result['records']:
                record["scraped_by_user"] = credentials["username"]
                scraped_data_from_all_accounts.append(record)
            
            print(f"Successfully scraped {len(result['records'])} records for user {credentials['username']}")
        else:
            print(f"Could not scrape data for {credentials['username']}")
        
        print("-" * 30)
    
    # Save to CSV
    if scraped_data_from_all_accounts:
        try:
            import pandas as pd
            df = pd.DataFrame(scraped_data_from_all_accounts)
            df.to_csv("erp_scraped_data.csv", index=False)
            print("Data saved to erp_scraped_data.csv")
        except ImportError:
            # Fallback to CSV module
            with open("erp_scraped_data.csv", "w", newline="", encoding="utf-8") as csvfile:
                if scraped_data_from_all_accounts:
                    fieldnames = scraped_data_from_all_accounts[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(scraped_data_from_all_accounts)
            print("Data saved to erp_scraped_data.csv (using csv module)")
    else:
        print("No data was collected.")

if __name__ == "__main__":
    # Run batch scraping
    batch_scrape_all_students()
