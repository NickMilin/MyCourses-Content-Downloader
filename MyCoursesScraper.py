import json
import re
from JSONParser import JSONParser

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time

# JS helper to find elements across nested shadow DOM boundaries
FIND_IN_SHADOW_JS = """
function findInShadow(root, selector, depth) {
    if (depth > 10) return [];
    let results = Array.from(root.querySelectorAll(selector));
    for (const el of root.querySelectorAll('*')) {
        if (el.shadowRoot) {
            results = results.concat(findInShadow(el.shadowRoot, selector, depth + 1));
        }
    }
    return results;
}
"""

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

def get_mycourses_data(driver):
    handle_login(driver)
    time.sleep(3)

    # Click all semester tabs to trigger lazy loading of enrollment cards
    driver.execute_script(FIND_IN_SHADOW_JS + """
        const tabs = findInShadow(document, 'd2l-tab', 0);
        for (const tab of tabs) {
            tab.click();
        }
    """)

    time.sleep(3)

    # Extract enrollment card data via JS traversal of shadow DOMs
    cards_data = driver.execute_script(FIND_IN_SHADOW_JS + """
        const cards = findInShadow(document, 'd2l-my-courses-enrollment-card', 0);
        const results = [];
        const seenIds = new Set();

        for (const card of cards) {
            const sr = card.shadowRoot;
            if (!sr) continue;

            const d2lCard = sr.querySelector('d2l-card');
            if (!d2lCard) continue;

            const href = d2lCard.getAttribute('href') || '';
            const courseCode = href.split('/').pop();

            if (!courseCode || seenIds.has(courseCode)) continue;
            seenIds.add(courseCode);

            // Prefer the 'text' attribute (clean), fall back to normalized textContent
            const courseName = d2lCard.getAttribute('text')
                || d2lCard.textContent.replace(/\\s+/g, ' ').trim();

            const img = sr.querySelector('img');
            const imgSrc = img ? img.getAttribute('src') : '';

            results.push({
                courseCode: courseCode,
                courseName: courseName,
                imageUrl: imgSrc
            });
        }

        return results;
    """)

    courses_dict = {}
    for card in cards_data:
        course_code = card['courseCode']
        raw_name = card['courseName']
        image_url = card['imageUrl']

        # Clean up course name: "Closed, Winter 2026 - MATH-340 - Title, 3216.202601, ..."
        # → "Winter 2026 - MATH-340 - Title"
        cleaned = re.sub(r'^Closed,\s*', '', raw_name)
        match = re.match(r'(.+?),?\s+\d+\.\d+', cleaned)
        course_name = match.group(1) if match else cleaned

        if image_url and not image_url.startswith('http'):
            image_url = 'https://mycourses2.mcgill.ca' + image_url

        course_data = fetch_json(
            driver, f"https://mycourses2.mcgill.ca/d2l/api/le/unstable/{course_code}/content/toc?loadDescription=true"
        )
        if course_data is None:
            print(f"Failed to fetch content for {course_code}")
            continue

        parser = JSONParser(course_data)
        folder = parser.get_dict()

        print(f"  {course_name}: {len(folder)} content folders")

        courses_dict[int(course_code)] = {
                "course_name": course_name,
                "thumbnail_link": image_url,
                "folders": folder,
            }

    driver.minimize_window()
    return courses_dict
