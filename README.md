# McHacks12 MyCourses Content Downloader
A tool developed during McHacks 12 to download course materials from McGill University's MyCourses (Brightspace/D2L) in one go.

You log in to MyCourses in a browser window, pick your courses in a local web page, and get one ZIP with every file, organised by course and folder.

## Table of Contents
- [Features](#features)
- [Quick start (no setup)](#quick-start-no-setup)
- [Run from source](#run-from-source)
- [How it works](#how-it-works)
- [Building the executable](#building-the-executable)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features
- **All your courses at once**: lists every Fall, Winter and Summer course you have been enrolled in, with its thumbnail and full name.
- **Course content**: every file from each course's Content section, kept in its original folder structure.
- **Assignments**: instructor attachments and your own submissions, saved under `Assignments/<assignment name>`.
- **Fast**: loading the course list takes a few seconds, and files download several at a time.
- **One ZIP**: the result is saved to your Downloads folder as `combined_files.zip`.
- **Failures are reported**: if the server refuses a file, it is listed when the download finishes.

## Quick start (no setup)
1. Install [Google Chrome](https://www.google.com/chrome/) if you don't have it.
2. Download the file for your system from the [Releases](../../releases) page.
   - **Windows**: unzip and run `MyCoursesDownloader.exe`.
   - **macOS / Linux**: extract with `tar -xzf MyCoursesDownloader-*.tar.gz`, then run `./MyCoursesDownloader` in a terminal.
3. Log in to MyCourses in the Chrome window that opens (you have 100 seconds).
4. Your browser opens the course list at `http://localhost:8080`. Click the courses you want, then press **Download**.

The app is not code-signed, so your system may warn you the first time:
- **Windows**: SmartScreen shows "Windows protected your PC". Click **More info**, then **Run anyway**.
- **macOS**: if you see "cannot be opened because the developer cannot be verified", run `xattr -d com.apple.quarantine MyCoursesDownloader` once in the terminal, then start it again.

## Run from source
Requires Python 3.9 or newer and Google Chrome.
```bash
git clone https://github.com/NickMilin/MyCourses-Content-Downloader.git
cd MyCourses-Content-Downloader
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Selenium downloads a matching ChromeDriver automatically the first time, so no driver setup is needed. If you prefer to use your own, set `driverPath` in `config.py`.

## How it works
1. Chrome opens only for the login. When the login finishes, the session cookies are copied into a plain HTTP session and Chrome is closed.
2. Course data, thumbnails and files are fetched directly from McGill's D2L API over HTTP, several at a time.
3. Files are saved with the name the server gives them, collected in a temporary folder, zipped into your Downloads folder, and the temporary folder is deleted.

Your password is never seen or stored by this tool. The login cookies stay in memory and are discarded when you close the app. The web page only listens on `localhost`, so other devices on your network cannot reach it.

## Building the executable
The executable is built with [PyInstaller](https://pyinstaller.org). A build only works for the system it is built on, so each release is built for Windows, macOS and Linux by GitHub Actions (`.github/workflows/build.yml`).

- **Publish a release**: push a version tag (`git tag v1.0.0 && git push origin v1.0.0`). The workflow builds all three and attaches them to a GitHub Release.
- **Build locally**:
  ```bash
  pip install nicegui==2.10.1 selenium==4.28.1 requests==2.32.3 pyinstaller
  pyinstaller MyCoursesDownloader.spec
  ```
  The result is `dist/MyCoursesDownloader`.

The original McHacks 12 submission is preserved as the git tag `mchacks12-submission`.

## Troubleshooting
- **Chrome opens but the page never loads or the app exits after 100 seconds**: you need to finish logging in within 100 seconds. Start the app again and log in faster.
- **Downloads fail or the file list says files could not be downloaded**: your login may have timed out (MyCourses logs you out after 180 minutes of inactivity). If it expired before you pressed Download, the app reopens Chrome so you can log in again. Otherwise restart the app and try again.
- **A course shows 0 files**: the course may be empty, or your account may not have access to its content.
- **Port 8080 already in use**: close the other program using it, or the previous copy of this app.

## Contributing
Contributions are welcome:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes with clear messages.
4. Submit a pull request describing your changes.

Thanks to [@turukano26](https://github.com/turukano26) for the fixes for MyCourses' updated page and the assignment downloads.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---
*Note: This tool is intended for personal use by McGill University students to manage their own course materials. Users are responsible for ensuring they comply with McGill's policies and terms of service when using this tool.*
