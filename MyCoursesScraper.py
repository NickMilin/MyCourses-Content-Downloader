from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import config
import time
import pandas as pd

# Set up Chrome options


options = Options()
options.add_experimental_option("detach", True)  # Prevents the browser from closing automatically

website = 'https://mycourses2.mcgill.ca/d2l/loginh/'
path = config.driverPath
service = Service(path)
driver = webdriver.Chrome(service=service, options=options)
driver.get(website)

# Auto click the sign-in button
sign_in_button = driver.find_element(By.XPATH,'//a[@id="link1"]')
sign_in_button.click()


# Function to safely get shadow root
def expand_shadow_element(element):
    return driver.execute_script('return arguments[0].shadowRoot', element)


# Wait for the initial shadow host
host1 = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-my-courses")))
shadow_root1 = expand_shadow_element(host1)

# Traverse through each nested shadow root
host2 = WebDriverWait(shadow_root1, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-my-courses-container")))
shadow_root2 = expand_shadow_element(host2)

host3 = WebDriverWait(shadow_root2, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-tabs")))
host3_5 = WebDriverWait(host3, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-tab-panel#panel-search-my-enrollments")))
host4 = WebDriverWait(host3_5, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-my-courses-content")))
shadow_root4 = expand_shadow_element(host4)

#Reroute to button
host5 = WebDriverWait(shadow_root4, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-link#viewAllCourses")))
driver.execute_script("arguments[0].click();", host5)


# Now get all of the actual courses
class_route_1 = WebDriverWait(shadow_root2, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-all-courses")))
class_route_1_shadow = expand_shadow_element(class_route_1)

class_route_2 = WebDriverWait(class_route_1_shadow, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-my-courses-card-grid")))
class_route_2_shadow = expand_shadow_element(class_route_2)

class_route_3 = WebDriverWait(class_route_2_shadow, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.course-card-grid")))
driver.execute_script("arguments[0].scrollIntoView(true);", class_route_3)

enrollment_cards = class_route_3.find_elements(By.XPATH, './/d2l-enrollment-card')
new_cards = []
while len(enrollment_cards) != len(new_cards):
    new_cards = enrollment_cards
    driver.execute_script("arguments[0].scrollIntoView(true);", enrollment_cards[-2])
    time.sleep(1)
    enrollment_cards = class_route_3.find_elements(By.XPATH, './/d2l-enrollment-card')

time.sleep(1)



print(class_route_3.text)






