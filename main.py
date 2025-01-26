import os
import re
import shutil
import time
import zipfile
import platform

from nicegui import ui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import config
import MyCoursesScraper
# FRONTEND

# ------------------------------------------------------------------
# DATA
# ------------------------------------------------------------------
course_list = {}

# ------------------------------------------------------------------
# MEMORY
# ------------------------------------------------------------------
selected_courses = set()
card_frames = {}
is_all_selected = False
sel_driver = None

# ------------------------------------------------------------------
# UI ELEMENTS
# ------------------------------------------------------------------
status_label = None
download_button = None
select_all_btn = None
course_container = None

# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------
def setup_selenium_driver():
    tmp_dir = os.getcwd() + "\\tmp"

    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": tmp_dir,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "detach": True
    }
    options.add_experimental_option("prefs", prefs)  # Prevents the browser from closing automatically

    path = config.driverPath
    service = Service(path)
    driver = webdriver.Chrome(service=service, options=options)

    return driver

def total_content_for_course(course_id) -> int:
    course = course_list[course_id]
    return sum(len(folder_content) for folder_content in course["folders"].values())


def total_selected_content() -> int:
    return sum(total_content_for_course(cid) for cid in selected_courses)


def update_status():
    ids_str = ", ".join(str(cid) for cid in selected_courses) if selected_courses else "None"
    status_label.text = (
        f"Selected courses: {ids_str}  |  "
        f"Total selected content: {total_selected_content()}"
    )
    download_button.text = f"Download {total_selected_content()} file(s)"

    # Disable the download button if no content is selected
    if total_selected_content() == 0:
        download_button.disable()
    else:
        download_button.enable()


def toggle_selection(cid, cframe):
    if cid in selected_courses:
        # Unselect
        selected_courses.remove(cid)
        # Remove highlight styling
        cframe.classes(remove="ring-4 ring-blue-500 shadow-xl")
    else:
        # Select
        selected_courses.add(cid)
        # Add highlight styling
        cframe.classes(add="ring-4 ring-blue-500 shadow-xl")
    update_status()

# The new function that toggles ALL courses  (NEW)
def toggle_all_courses():
    global is_all_selected

    # If not all selected yet, then select them all
    if not is_all_selected:
        for cid, cf in card_frames.items():
            # Only add if it's not already selected
            if cid not in selected_courses:
                toggle_selection(cid, cf)
        select_all_btn.text = "Deselect All"
        is_all_selected = True

    # Otherwise, deselect them all
    else:
        for cid, cf in card_frames.items():
            if cid in selected_courses:
                toggle_selection(cid, cf)
        select_all_btn.text = "Select All"
        is_all_selected = False

    update_status()

def download_files(driver):
    if not selected_courses:
        print("No courses selected for download.")
        return

    os.makedirs("tmp", exist_ok=True)
    tmp_dir = os.getcwd()+"\\tmp"

    for cid in selected_courses:  # Use selected_courses instead of course_list
        cinfo = course_list[cid]
        cdir = tmp_dir+"\\"+re.sub(r"[\\/:*?\"<>|.]", "", cinfo["course_name"])
        os.makedirs(cdir, exist_ok=True)
        for folder_name, folder_info in cinfo["folders"].items():
            fdir = cdir+"\\"+re.sub(r"[\\/:*?\"<>|.]", "", folder_name)
            os.makedirs(fdir, exist_ok=True)
            for file_id in folder_info:
                driver.get("https://mycourses2.mcgill.ca/d2l/le/content/"+str(cid)+"/topics/files/download/"+file_id+"/DirectFileTopicDownload")

                while any([(filename.endswith(".crdownload") or filename.endswith(".tmp")) for filename in
                           os.listdir(tmp_dir)]):
                    time.sleep(0.01)
                move_latest_file(tmp_dir, fdir)

    downloads_folder = get_downloads_folder()
    zip_path = downloads_folder+"/combined_files.zip"  # Replace with the desired zip file path
    file_counter = 1

    while os.path.isfile(zip_path):
        zip_path = downloads_folder+"/combined_files ("+str(file_counter)+").zip"
        file_counter += 1

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(tmp_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                arcname = os.path.relpath(file_path, start=tmp_dir)
                zipf.write(file_path, arcname)

    shutil.rmtree(tmp_dir)
    print(f"Files have been downloaded and zipped at {zip_path}")

def move_latest_file(download_dir, target_dir):
    # Find the newest file in the directory
    files = [os.path.join(download_dir, f) for f in os.listdir(download_dir)]
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        return  # No file found

    newest_file = max(files, key=os.path.getctime)

    # Move it
    shutil.move(newest_file, target_dir)

def get_downloads_folder():
    if platform.system() == "Windows":
        return os.path.join(os.environ['USERPROFILE'], "Downloads")
    elif platform.system() == "Darwin":  # macOS
        return os.path.join(os.environ['HOME'], "Downloads")
    elif platform.system() == "Linux":
        return os.path.join(os.environ['HOME'], "Downloads")
    else:
        raise OSError("Unsupported Operating System")

def extract_course_code(course_name):
    # Extracts the "XXXX-000" portion from the course name.
    match = re.search(r'\b([A-Z]{4}-\d{3})\b', course_name)
    return match.group(1) if match else ""

# ------------------------------------------------------------------
# UI SETUP
# ------------------------------------------------------------------
def setup_ui():
    global status_label, download_button, select_all_btn, course_container

    # Create a header label to display current selections:
    with ui.header().classes('justify-between items-center bg-gray-100 px-4 py-2 shadow'):
        ui.label("MyCourses Downloads").classes('text-2xl font-semibold text-black')

    # Status label for tracking which courses (and how many contents) are selected:
    status_label = ui.label("Selected courses: None | Total selected content: 0") \
        .classes('text-lg font-medium')

    # Container for the course cards
    with ui.row().classes('flex flex-wrap justify-center gap-6 p-4'):
        sorted_courses = sorted(course_list.items(), key=lambda x: extract_course_code(x[1]['course_name']))

        for course_id, course_info in sorted_courses:
            # Pre-calculate the total content in each course
            content_count = total_content_for_course(course_id)

            with ui.card().classes('w-64 p-0 hover:shadow-lg transition-shadow cursor-pointer') as card_frame:
                card_frames[course_id] = card_frame
                with ui.element('div').classes('relative w-full h-40 overflow-hidden'):
                    ui.image(course_info['thumbnail_link']) \
                        .classes('object-cover w-full h-full')

                    with ui.element('div').classes(
                            'absolute top-0 left-0 m-2 px-3 py-1 bg-gray-800 bg-opacity-70 '
                            'text-white text-sm rounded'
                    ):
                        ui.label(f"{content_count} file{'s' if content_count != 1 else ''}")

                ui.label(course_info['course_name']) \
                    .classes(
                    'text-lg font-semibold truncate overflow-hidden whitespace-nowrap w-[256px] pb-[16px] pl-[8px] pr-[8px]') \
                    .style('text-overflow: ellipsis;')

                card_frame.on('click', lambda e, cid=course_id, cf=card_frame: toggle_selection(cid, cf))


    # Footer with download button:
    with ui.footer().classes('p-4'):
        download_button = ui.button(
            f"Download {total_selected_content()} file(s)",
            on_click=lambda:download_files(sel_driver)
        ).props('color=secondary')
        select_all_btn = ui.button("Select All", on_click=toggle_all_courses) \
            .props('color=primary')

if __name__ == "__main__":
    sel_driver = setup_selenium_driver()
    course_list = MyCoursesScraper.get_mycourses_data(sel_driver)

    print(course_list)

    setup_ui()

    update_status()  # Make sure initial text is correct
    ui.run(title="MyCourses Downloads", reload=False)
