import json
import re
from JSONParser import JSONParser

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

import time

# Function to safely get shadow root
def expand_shadow_element(driver, element):
    return driver.execute_script('return arguments[0].shadowRoot', element)

def get_mycourses_data(driver):
    website = 'https://mycourses2.mcgill.ca/d2l/loginh/'
    driver.get(website)
    driver.maximize_window()
    
    # Auto click the sign-in button
    sign_in_button = driver.find_element(By.XPATH,'//a[@id="link1"]')
    sign_in_button.click()
    
    # Wait for the initial shadow host
    # Give the user 100 seconds to log into mycourses before crashing (feature not a bug)
    host1 = WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-my-courses")))
    shadow_root1 = expand_shadow_element(driver, host1)
    
    # Traverse through each nested shadow root
    host2 = WebDriverWait(shadow_root1, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-my-courses-container")))
    shadow_root2 = expand_shadow_element(driver, host2)
    
    host3 = WebDriverWait(shadow_root2, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-tabs")))
    host3_5 = WebDriverWait(host3, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-tab-panel#panel-search-my-enrollments")))
    host4 = WebDriverWait(host3_5, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-my-courses-content")))
    shadow_root4 = expand_shadow_element(driver, host4)
    
    #Reroute to viewAllCourses button
    host5 = WebDriverWait(shadow_root4, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-link#viewAllCourses")))
    driver.execute_script("arguments[0].click();", host5)
    
    # ------------------ NOW ON viewAllCourses PAGE OF MYCOURSES ------------------
    
    # ------------------ NOW SELECTING ALL BUTTON ON viewAllCourses PAGE OF MYCOURSES ------------------
    shadow_root3 = expand_shadow_element(driver, host3)
    all_button = WebDriverWait(shadow_root3, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'd2l-tab-internal[title="All"]')))
    
    # Use ActionChains to press the all tab
    actions = ActionChains(driver)
    actions.move_to_element(all_button).click().perform()
    
    # ------------------ NOW LOADING ALL OF THE COURSES IN viewAllCourses PAGE OF MYCOURSES ------------------
    # Now get all of the actual courses
    class_route_1 = WebDriverWait(shadow_root2, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-all-courses")))
    class_route_1_shadow = expand_shadow_element(driver, class_route_1)
    
    class_route_2 = WebDriverWait(class_route_1_shadow, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-my-courses-card-grid")))
    class_route_2_shadow = expand_shadow_element(driver, class_route_2)
    
    class_route_3 = WebDriverWait(class_route_2_shadow, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.course-card-grid")))
    driver.execute_script("arguments[0].scrollIntoView(true);", class_route_3)
    
    enrollment_cards = class_route_3.find_elements(By.XPATH, './/d2l-enrollment-card')
    new_cards = []
    while len(enrollment_cards) != len(new_cards):
        new_cards = enrollment_cards
        driver.execute_script("arguments[0].scrollIntoView(true);", enrollment_cards[-2])
        time.sleep(.5)
        enrollment_cards = class_route_3.find_elements(By.XPATH, './/d2l-enrollment-card')
    
    
    # Get all the course Titles
    course_names = []
    #Get all the urls for the MyCourses images
    image_urls = []
    # Get the course number
    course_codes = []
    for enrollment_card in enrollment_cards:
        enrollment_card_shadow = expand_shadow_element(driver, enrollment_card)
        organization_name = enrollment_card_shadow.find_element(By.CSS_SELECTOR, "d2l-organization-name")
        course_name = organization_name.text
        if 'Winter' in course_name or 'Fall' in course_name or 'Summer' in course_name:
            course_names.append(course_name)
    
            # Only get the course image if the name is a real course
            organization_image = enrollment_card_shadow.find_element(By.CSS_SELECTOR, "d2l-organization-image")
            organization_image_shadow = expand_shadow_element(driver, organization_image)
            course_image = WebDriverWait(organization_image_shadow, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-course-image")))
            course_image_shadow = expand_shadow_element(driver, course_image)
            # Get the image used in the course
            img_element = course_image_shadow.find_element(By.CSS_SELECTOR, "img.shown")
            src_url = img_element.get_attribute("srcset")
            # Extract the filename from the URL
            filename = re.split(" ", src_url)[-2]
            image_urls.append(filename)
    
    
            # Get the course number
            # 3. Find the nested d2l-card inside the enrollment card's shadow DOM
            d2l_card = enrollment_card_shadow.find_element(By.CSS_SELECTOR, "d2l-card")
            # 4. Expand d2l-card's shadow root
            d2l_card_shadow = expand_shadow_element(driver, d2l_card)
            # 5. Extract the link from the <a> tag inside the card's shadow DOM
            link_element = d2l_card_shadow.find_element(By.CSS_SELECTOR, "a[href]")
            course_url = link_element.get_attribute("href")
            course_code = re.split('/',course_url)[-1]
            course_codes.append(course_code)
    
    
    
    # print(course_names)
    # print(image_urls)
    # print(course_codes)
    #
    # print(len(course_names))
    # print(len(image_urls))
    # print(len(course_codes))
    
    
    courses_dict = {}
    for i in range(len(course_names)):
        try:
            api_url = f"https://mycourses2.mcgill.ca/d2l/api/le/unstable/{course_codes[i]}/content/toc?loadDescription=true"
    
            # Navigate to API endpoint using existing session
            driver.get(api_url)
    
            # Wait for content to load and get raw JSON
            WebDriverWait(driver, 10).until(
                lambda d: d.find_element(By.TAG_NAME, "pre")
            )
            raw_json = driver.find_element(By.TAG_NAME, "pre").text
            course_data = json.loads(raw_json)
    
            parser = JSONParser(course_data)
            folder = parser.get_dict()
    
            # print(folder)
    
            courses_dict[int(course_codes[i])] = {
                    "course_name": course_names[i],
                    "thumbnail_link": image_urls[i],
                    "folders": folder
                }
    
        except Exception as e:
            print(f"Failed to process {course_codes[i]}: {str(e)}")
            continue
    
    return courses_dict