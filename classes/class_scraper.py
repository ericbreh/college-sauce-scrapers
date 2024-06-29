import csv
from datetime import datetime
from playwright.sync_api import sync_playwright
import pandas
from sqlalchemy import create_engine
from config import DB_CONFIG

# change this
quarter = 'SUMMER 2024'

url = 'https://my.sa.ucsb.edu/public/curriculum/coursesearch.aspx'
course_level = 'Undergraduate'
not_wanted_classes = ['INTERN', 'RESEARCH ASSISTANT', 'INDEPENDENT STUDIES', 'IND STUDY']

# Get the start time
start_time = datetime.now()

# Date created
date_created = start_time.strftime("%Y-%m-%d") + " 00:00:00"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url)

    # Get the options from the dropdown
    options = page.query_selector_all('#ctl00_pageContent1_courseList option')
    
    # get the subject values - ex. 'ANTH'
    subject_values = [option.get_attribute('value') for option in options]
    
    # get the subject titles - ex. 'Anthropology - ANTH'
    subject_titles = [' - '.join(map(str.strip, (option.get_property('innerText')).json_value().split('-'))) for option in options]

    # Create a list to store the course data
    course_data = []
    
    subject_counter = 0
    total_subjects = len(subject_values)
    
    for subject_value, subject_title in zip(subject_values, subject_titles):
        subject_counter += 1
        print(f"{subject_value} {subject_counter}/{total_subjects}")
        
        # Select options
        page.select_option('#ctl00_pageContent1_courseList', subject_value)
        page.select_option('#ctl00_pageContent1_quarterList', quarter)
        page.select_option('#ctl00_pageContent1_dropDownCourseLevels', course_level)

        # Click the search button
        page.click('#ctl00_pageContent1_searchButton')

        # Wait for the new page to load
        page.wait_for_load_state("networkidle")

        # Get the course information
        rows = page.query_selector_all('.CourseInfoRow')
        for row in rows:
            course_id = row.query_selector('#CourseTitle').inner_text().strip()
            title = row.query_selector('td:nth-child(3)').inner_text().strip()
            professor = row.query_selector('td:nth-child(6)').inner_text().strip().replace('\n', ', ')
            days = row.query_selector('td:nth-child(7)').inner_text().strip()
            time = row.query_selector('td:nth-child(8)').inner_text().strip()
            location = row.query_selector('td:nth-child(9)').inner_text().strip()

            # Add to database if it has title (if it is a course not section)
            if title and not any(not_wanted_class in title for not_wanted_class in not_wanted_classes):
                course_data.append({
                    'group_course_quarter': quarter,
                    'group_course_name': course_id,
                    'group_course_title': title,
                    'group_course_professor': professor,
                    'group_course_days': days,
                    'group_course_time': time,
                    'group_course_location': location,
                    "created_on": date_created,
                    "is_active": 1,
                    "group_course_subject_area": subject_title,                                
                })
            
    browser.close()

end_time = datetime.now()
print(f"Script runtime: {end_time - start_time}")

# Save the course data to a CSV file
with open(quarter+'.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = [
                'group_course_quarter',
                'group_course_name',
                'group_course_title',
                'group_course_professor',
                'group_course_days',
                'group_course_time',
                'group_course_location',
                "created_on",
                "is_active",
                "group_course_subject_area",
                ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(course_data)

# Upload to database
data = pandas.read_csv(quarter+'.csv')
engine = create_engine(f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
data.to_sql('group_courses', engine, if_exists='append', index=False)