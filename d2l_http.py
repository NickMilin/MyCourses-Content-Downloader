"""Plain-HTTP access to McGill's D2L (myCourses) API.

Selenium is only needed to log in. Its session cookies are copied into a
requests.Session, and every API call and file download after that is a normal
HTTP request that can run in parallel.
"""
import base64
import os
import re
from urllib.parse import unquote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://mycourses2.mcgill.ca"
REQUEST_TIMEOUT = 60  # seconds


def build_session(cookies, pool_size=12):
    """Create a requests.Session from the cookies returned by driver.get_cookies()."""
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(
            cookie["name"], cookie["value"],
            domain=cookie.get("domain"), path=cookie.get("path", "/"),
        )

    # Retry throttling and transient server errors with a short back-off.
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=pool_size, pool_maxsize=pool_size)
    session.mount("https://", adapter)
    return session


def get_json(session, path, params=None):
    """GET a D2L API path and return parsed JSON, or None on any failure."""
    try:
        response = session.get(BASE_URL + path, params=params, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            return None
        data = response.json()
    except (requests.RequestException, ValueError):
        return None
    # D2L can return {"Errors": [...]} instead of an HTTP error status
    if isinstance(data, dict) and "Errors" in data:
        return None
    return data


def session_is_valid(session):
    """True if the login cookies are still accepted by the server."""
    return get_json(session, "/d2l/api/lp/unstable/users/whoami") is not None


def get_image_data_uri(session, path):
    """Download an image and return it as a data: URI ('' on failure).

    A data URI lets the local web UI show the image without needing a McGill login.
    """
    try:
        response = session.get(BASE_URL + path, timeout=REQUEST_TIMEOUT)
    except requests.RequestException:
        return ""
    content_type = response.headers.get("Content-Type", "")
    if response.status_code != 200 or not content_type.startswith("image/"):
        return ""
    encoded = base64.b64encode(response.content).decode("ascii")
    return f"data:{content_type.split(';')[0]};base64,{encoded}"


def safe_name(name, fallback="untitled"):
    """Remove characters that are not allowed in file or folder names."""
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "", name or "").strip().strip(".")
    return cleaned or fallback


def _filename_from_headers(response):
    disposition = response.headers.get("Content-Disposition", "")
    match = re.search(r"filename\*\s*=\s*UTF-8''([^;]+)", disposition, re.IGNORECASE)
    if match:
        return unquote(match.group(1).strip())
    match = re.search(r'filename\s*=\s*"([^"]+)"', disposition) or re.search(r"filename\s*=\s*([^;]+)", disposition)
    return match.group(1).strip() if match else None


def _reserve_path(directory, filename):
    """Atomically create an empty file with a unique name and return its path.

    O_EXCL makes this safe when several threads write into the same folder.
    """
    base, ext = os.path.splitext(filename)
    counter = 0
    while True:
        candidate = filename if counter == 0 else f"{base} ({counter}){ext}"
        path = os.path.join(directory, candidate)
        try:
            os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            return path
        except FileExistsError:
            counter += 1


def download_file(session, path, dest_dir, fallback_name):
    """Stream a file from the server into dest_dir using the server-provided filename.

    Returns the saved path, or None if the server refused or returned something
    that is not a file (for example a login page after the session expired).
    """
    try:
        with session.get(BASE_URL + path, stream=True, timeout=REQUEST_TIMEOUT) as response:
            if response.status_code != 200:
                return None
            filename = _filename_from_headers(response)
            # An HTML page with no attachment name is an error or login page, not a file
            if filename is None and response.headers.get("Content-Type", "").startswith("text/html"):
                return None

            os.makedirs(dest_dir, exist_ok=True)
            target = _reserve_path(dest_dir, safe_name(filename, fallback_name))
            try:
                with open(target, "wb") as out:
                    for chunk in response.iter_content(chunk_size=64 * 1024):
                        out.write(chunk)
            except (requests.RequestException, OSError):
                os.remove(target)
                return None
            return target
    except requests.RequestException:
        return None
