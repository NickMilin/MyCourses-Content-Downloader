import json
import re
from JSONParser import JSONParser

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time

def handle_login(driver):
    website = 'https://mycourses2.mcgill.ca/d2l/loginh/'
    driver.get(website)
    driver.maximize_window()

    # Auto click the sign-in button
    sign_in_button = driver.find_element(By.XPATH, '//a[@id="link1"]')
    sign_in_button.click()

    # Wait for the initial shadow host (d2l-my-courses-v2)
    # Give the user 100 seconds to log into mycourses before crashing (feature not a bug)
    return WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "d2l-my-courses-v2"))
    )

def fetch_json(driver, url, timeout=5):
    """Navigate to a D2L API URL and return parsed JSON, or None on failure."""
    try:
        driver.set_page_load_timeout(15)
        driver.get(url)
        time.sleep(0.3)
        WebDriverWait(driver, timeout).until(
            lambda d: d.find_element(By.TAG_NAME, "pre")
        )
        raw_json = driver.find_element(By.TAG_NAME, "pre").text
        data = json.loads(raw_json)
        # D2L returns {"Errors": [...]} for auth failures — treat as failure
        if isinstance(data, dict) and "Errors" in data:
            return None
        return data
    except Exception:
        return None
    finally:
        driver.set_page_load_timeout(300)

def get_user_id(driver):
    """Get the authenticated user's D2L user ID via the whoami API."""
    data = fetch_json(driver, "https://mycourses2.mcgill.ca/d2l/api/lp/unstable/users/whoami")
    return data.get("Identifier") if data else None

def fetch_assignments(driver, course_code):
    """Fetch assignment dropbox folders and their attachments for a course."""
    assignments = []

    dropbox_folders = fetch_json(
        driver, f"https://mycourses2.mcgill.ca/d2l/api/le/1.82/{course_code}/dropbox/folders/"
    )
    if not isinstance(dropbox_folders, list):
        return assignments

    for folder in dropbox_folders:
        folder_id = folder.get("Id")
        folder_name = folder.get("Name", f"Assignment {folder_id}")

        attachments = [
            {"file_id": att["FileId"], "file_name": att["FileName"]}
            for att in folder.get("Attachments", [])
        ]

        # Include every dropbox folder — we'll attempt submission download
        # during the download phase (the API won't let us check in advance)
        assignments.append({
            "folder_id": folder_id,
            "folder_name": folder_name,
            "attachments": attachments,
        })

    return assignments

# Runs inside the logged-in page. Lists every course offering via the enrollments API
# (names come back clean, no card scraping) and embeds each thumbnail as a data URI,
# because the image endpoint needs the McGill session cookie and the local UI page
# (127.0.0.1) does not have it.
FETCH_ENROLLMENTS_JS = """
const done = arguments[arguments.length - 1];
(async () => {
    const items = [];
    let bookmark = '';
    for (let page = 0; page < 50; page++) {
        const url = '/d2l/api/lp/1.47/enrollments/myenrollments/?orgUnitTypeId=3'
            + (bookmark ? '&bookmark=' + encodeURIComponent(bookmark) : '');
        const r = await fetch(url, {credentials: 'include'});
        if (!r.ok) break;
        const j = await r.json();
        items.push(...j.Items);
        if (!j.PagingInfo.HasMoreItems) break;
        bookmark = j.PagingInfo.Bookmark;
    }

    const toDataUri = blob => new Promise(resolve => {
        const fr = new FileReader();
        fr.onload = () => resolve(fr.result);
        fr.onerror = () => resolve('');
        fr.readAsDataURL(blob);
    });

    const results = await Promise.all(items.map(async item => {
        let imageUrl = '';
        try {
            const r = await fetch(
                '/d2l/api/lp/1.47/courses/' + item.OrgUnit.Id + '/image?autoSelectImage=true',
                {credentials: 'include'}
            );
            if (r.ok) imageUrl = await toDataUri(await r.blob());
        } catch (e) {}
        return {courseCode: String(item.OrgUnit.Id), courseName: item.OrgUnit.Name, imageUrl: imageUrl};
    }));
    done(results);
})().catch(e => done([]));
"""

def get_mycourses_data(driver):
    handle_login(driver)
    time.sleep(1)

    driver.set_script_timeout(120)
    cards_data = driver.execute_async_script(FETCH_ENROLLMENTS_JS)

    # Fetch user ID now (navigates away from the homepage, so it must come after the enrollments call)
    user_id = get_user_id(driver)

    courses_dict = {}
    for card in cards_data:
        course_code = card['courseCode']
        raw_name = card['courseName']
        image_url = card['imageUrl']

        # Collapse stray whitespace/newlines that appear in some course names
        course_name = re.sub(r'\s+', ' ', raw_name).strip()

        # Only real courses (as in the original version); skips orgs like "It Takes All of Us"
        if not any(term in course_name for term in ('Winter', 'Fall', 'Summer')):
            continue

        course_data = fetch_json(
            driver, f"https://mycourses2.mcgill.ca/d2l/api/le/unstable/{course_code}/content/toc?loadDescription=true"
        )
        if course_data is None:
            print(f"Failed to fetch content for {course_code}")
            continue

        parser = JSONParser(course_data)
        folder = parser.get_dict()

        assignments = fetch_assignments(driver, course_code)
        print(f"  {course_name}: {len(folder)} content folders, {len(assignments)} assignments")

        courses_dict[int(course_code)] = {
                "course_name": course_name,
                "thumbnail_link": image_url,
                "folders": folder,
                "assignments": assignments,
                "user_id": user_id,
            }

    driver.minimize_window()
    return courses_dict
