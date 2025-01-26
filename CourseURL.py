import re


class CourseURL:
    def __init__(self, course_code: str):
        self.course_code = course_code

    def course_content_url(self):
        return f'https://mycourses2.mcgill.ca/d2l/le/lessons/{self.course_code}'

    def course_content_api(self):
        return f'https://mycourses2.mcgill.ca/d2l/api/le/unstable/{self.course_code}/content/toc?loadDescription=true'
