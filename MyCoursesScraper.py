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


# Function to get shadow roots
def get_shadow_root(element):
    return driver.execute_script('return arguments[0].shadowRoot', element)

products = WebDriverWait(driver,5).until(EC.presence_of_all_elements_located((By.XPATH, '//d2l-my-courses[@class="d2l-my-courses-widget d2l-token-receiver"]')))

shadow_root_1 = driver.find_element(By.XPATH, '//d2l-my-courses[@class="d2l-my-courses-widget d2l-token-receiver"]').shadow_root
shadow_root_2 = shadow_root_1.find_element(By.XPATH, "//d2l-my-courses-container").shadow_root
print(shadow_root_2)





