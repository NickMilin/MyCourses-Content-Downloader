import re
import time
from concurrent.futures import ThreadPoolExecutor

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import d2l_http
from JSONParser import JSONParser

# How many courses to load at the same time. Kept modest to be polite to McGill's servers.
MAX_WORKERS = 6


def handle_login(driver):
    website = 'https://mycourses2.mcgill.ca/d2l/loginh/'
    driver.get(website)
    driver.maximize_window()

    # Auto click the sign-in button
    sign_in_button = driver.find_element(By.XPATH, '//a[@id="link1"]')
    sign_in_button.click()

    # Wait for the home page (d2l-my-courses-v2) which means the login finished
    # Give the user 100 seconds to log into mycourses before crashing (feature not a bug)
    return WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-my-courses-v2"))
    )


def login_and_get_session(driver):
    """Log in through the browser, then return a requests.Session holding the login cookies.

    The browser is only needed for the login itself. The caller can close it afterwards.
    """
    handle_login(driver)
    time.sleep(1)  # let the session cookies settle
    return d2l_http.build_session(driver.get_cookies())


def fetch_enrollments(session):
    """Return every course offering the user is enrolled in (pages through the API)."""
    items = []
    bookmark = None
    for _ in range(50):  # hard stop in case the API keeps reporting more pages
        params = {"orgUnitTypeId": 3}
        if bookmark:
            params["bookmark"] = bookmark
        data = d2l_http.get_json(session, "/d2l/api/lp/1.47/enrollments/myenrollments/", params=params)
        if not data:
            break
        items.extend(data.get("Items", []))
        paging = data.get("PagingInfo", {})
        if not paging.get("HasMoreItems"):
            break
        bookmark = paging.get("Bookmark")
    return items


def fetch_assignments(session, course_code):
    """Fetch assignment dropbox folders and their attachments for a course."""
    dropbox_folders = d2l_http.get_json(session, f"/d2l/api/le/1.82/{course_code}/dropbox/folders/")
    if not isinstance(dropbox_folders, list):
        return []

    assignments = []
    for folder in dropbox_folders:
        folder_id = folder.get("Id")
        assignments.append({
            "folder_id": folder_id,
            "folder_name": folder.get("Name", f"Assignment {folder_id}"),
            "attachments": [
                {"file_id": att["FileId"], "file_name": att["FileName"]}
                for att in folder.get("Attachments", [])
            ],
        })
    return assignments


def load_course(session, user_id, course_code, course_name):
    """Load everything we need for one course. Returns None if its content can't be read."""
    course_data = d2l_http.get_json(
        session, f"/d2l/api/le/unstable/{course_code}/content/toc", params={"loadDescription": "true"}
    )
    if course_data is None:
        print(f"Failed to fetch content for {course_code}")
        return None

    folders = JSONParser(course_data).get_dict()
    assignments = fetch_assignments(session, course_code)
    thumbnail = d2l_http.get_image_data_uri(
        session, f"/d2l/api/lp/1.47/courses/{course_code}/image?autoSelectImage=true"
    )
    print(f"  {course_name}: {len(folders)} content folders, {len(assignments)} assignments")

    return {
        "course_name": course_name,
        "thumbnail_link": thumbnail,
        "folders": folders,
        "assignments": assignments,
        "user_id": user_id,
    }


def get_mycourses_data(session):
    whoami = d2l_http.get_json(session, "/d2l/api/lp/unstable/users/whoami") or {}
    user_id = whoami.get("Identifier")

    courses = []
    for item in fetch_enrollments(session):
        org_unit = item["OrgUnit"]
        # Collapse stray whitespace/newlines that appear in some course names
        name = re.sub(r'\s+', ' ', org_unit["Name"]).strip()
        # Only real courses (as in the original version); skips orgs like "It Takes All of Us"
        if any(term in name for term in ('Winter', 'Fall', 'Summer')):
            courses.append((org_unit["Id"], name))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        loaded = list(pool.map(lambda c: load_course(session, user_id, c[0], c[1]), courses))

    return {
        course_id: data
        for (course_id, _), data in zip(courses, loaded)
        if data is not None
    }
