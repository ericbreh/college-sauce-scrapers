import csv
from datetime import datetime
from playwright.sync_api import sync_playwright

url = 'https://my.sa.ucsb.edu/public/curriculum/coursesearch.aspx'
quarter = 'SPRING 2024'
course_level = 'Undergraduate'

# Get the start time
start_time = datetime.now()

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

    ta_data = []
    unique_professors = set()
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
        
        saved_title = ''
        for row in rows:
            course_id = row.query_selector('#CourseTitle').inner_text().strip()
            title = row.query_selector('td:nth-child(3)').inner_text().strip()
            professor = row.query_selector('td:nth-child(6)').inner_text().strip().replace('\n', ', ')
            
            if title: 
                saved_title = title
                
            if professor and not title:
                if professor not in unique_professors:
                    unique_professors.add(professor)
                    ta_data.append({
                        'course_id': course_id,
                        'title': saved_title,
                        'ta_name': professor,
                    })
            
    browser.close()

end_time = datetime.now()
print(f"Script runtime: {end_time - start_time}")

# Save the course data to a CSV file
with open('ta names.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = [
                'course_id',
                'title',
                'ta_name',
                ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(ta_data)
