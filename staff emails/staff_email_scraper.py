import csv
from datetime import datetime
from playwright.sync_api import sync_playwright

url = 'https://www.ucsb.edu/directory'
output_file = 'Staff emails.csv'

# Get the start time
start_time = datetime.now()

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url)

    # Click the "Department" radio button
    department_radio = page.wait_for_selector("#edit-active-2", state="visible")
    department_radio.click()

    # Get all the department options
    department_dropdown = page.wait_for_selector("#edit-dept", state="visible")
    department_options = [option.get_attribute("value") for option in department_dropdown.query_selector_all("option")]

    # Remove the first "Select Department" option
    department_options = department_options[1:]

    all_email_addresses = []

    # Loop through each department option
    for i, department_option in enumerate(department_options, start=1):
        print(f"{department_option} ({i}/{len(department_options)})")
        
        department_dropdown = page.wait_for_selector("#edit-dept", state="visible")
        department_dropdown.select_option(value=department_option)

        # Click the "Submit" button
        submit_button = page.wait_for_selector("#edit-submit", state="visible")
        submit_button.click()

        # Wait for the results page to load
        page.wait_for_url("**/directory**")

        # Extract the email addresses from the table
        email_addresses = []
        for row in page.query_selector_all("tr"):
            email_link = row.query_selector("a[href^='mailto:']")
            if email_link:
                email_address = email_link.get_attribute("href").split(":")[1]
                email_addresses.append(email_address)

        all_email_addresses.extend(email_addresses)

    # Write the email addresses to a CSV file
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for email_address in all_email_addresses:
            writer.writerow([email_address])

    browser.close()
    end_time = datetime.now()
    print(f"Script runtime: {end_time - start_time}")
