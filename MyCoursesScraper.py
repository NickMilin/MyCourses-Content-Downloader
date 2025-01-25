from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import config
import time
import pandas as pd

website = 'https://mycourses2.mcgill.ca/d2l/loginh/'
path = config.driverPath
service = Service(path)
driver = webdriver.Chrome(service=service)
driver.get(website)
driver.maximize_window()


