from nicegui import ui
# FRONTEND

# ------------------------------------------------------------------
# DATA
# ------------------------------------------------------------------
course_list = {
    1: {
        "course_name": "Course Name 1",
        "thumbnail_link": "https://s.brightspace.com/course-images/images/322cd582-6b20-4459-b7b9-1c92e9903c33/tile-low-density-max-size.jpg",
        "folders": {
            "folder_1_name": ["content_1_id", "content_2_id"],
            "folder_2_name": ["content_3_id", "content_4_id"]
        }
    },
    2: {
        "course_name": "Course Name 2",
        "thumbnail_link": "https://s.brightspace.com/course-images/images/bdcbbbed-ddab-4be9-8479-ee931512e3a0/tile-low-density-max-size.jpg",
        "folders": {
            "folder_1_name": ["content_5_id", "content_6_id"],
            "folder_2_name": ["content_7_id", "content_8_id"]
        }
    },
    # Add more courses as needed
}

# ------------------------------------------------------------------
# MEMORY
# ------------------------------------------------------------------
selected_courses = set()


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------
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


def toggle_selection(course_id, card_frame):
    if course_id in selected_courses:
        # Unselect
        selected_courses.remove(course_id)
        # Remove highlight styling
        card_frame.classes(remove="ring-4 ring-blue-500 shadow-xl")
    else:
        # Select
        selected_courses.add(course_id)
        # Add highlight styling
        card_frame.classes(add="ring-4 ring-blue-500 shadow-xl")
    update_status()


# ------------------------------------------------------------------
# UI SETUP
# ------------------------------------------------------------------
# Create a header label to display current selections:
with ui.header().classes('justify-between items-center bg-gray-100 px-4 py-2 shadow'):
    ui.label("MyCourses Downloads").classes('text-2xl font-semibold text-black')

# Status label for tracking which courses (and how many contents) are selected:
status_label = ui.label("Selected courses: None | Total selected content: 0") \
    .classes('text-lg font-medium')

# Container for the course cards
with ui.row().classes('flex flex-wrap justify-center gap-6 p-4'):
    for course_id, course_info in course_list.items():
        # Pre-calculate the total content in each course
        content_count = total_content_for_course(course_id)

        with ui.card().classes('w-64 p-0 hover:shadow-lg transition-shadow cursor-pointer') as card_frame:
            with ui.element('div').classes('relative w-full h-40 overflow-hidden'):
                ui.image(course_info['thumbnail_link']) \
                    .classes('object-cover w-full h-full')

                with ui.element('div').classes(
                        'absolute top-0 left-0 m-2 px-3 py-1 bg-gray-800 bg-opacity-70 '
                        'text-white text-sm rounded'
                ):
                    ui.label(f"{content_count} file{'s' if content_count != 1 else ''}")

            ui.label(course_info['course_name']) \
                .classes('text-center text-lg font-semibold size-auto truncate pb-[16px] ml-[5px]')

            card_frame.on('click', lambda e, cid=course_id, cf=card_frame: toggle_selection(cid, cf))

# Run the application
ui.run(title="MyCourses Downloads", reload=False)
