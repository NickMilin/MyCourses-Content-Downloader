# McHacks12 MyCourses Content Downloader

Welcome to the MyCourses Content Downloader, a tool developed during McHacks 12 to streamline the process of downloading course materials from McGill University's MyCourses platform.

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

The MyCourses Content Downloader is designed to automate the retrieval of course content from McGill's MyCourses system. By leveraging web scraping techniques, this tool allows students to efficiently download all their course materials in a structured manner.

## Features

- **Automated Downloading**: Fetches all available course materials from MyCourses.
- **Organized Storage**: Saves files in a structured directory format for easy access.
- **Configurable Settings**: Allows users to specify which courses and materials to download.

## Installation

To set up the MyCourses Content Downloader, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/NickMilin/MyCourses-Content-Downloader.git
   cd MyCourses-Content-Downloader
   ```

2. **Create a Virtual Environment** (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Configure the Tool**: Before running the downloader, ensure you've set up the necessary configurations (see [Configuration](#configuration) below).

2. **Run the Downloader**:
   ```bash
   python main.py
   ```

   The tool will prompt you for your MyCourses credentials and proceed to download the specified course materials.

## Configuration

The downloader uses a configuration file named `config.py` to manage settings:

- **Username and Password**: Your MyCourses login credentials.
- **Courses**: A list of course identifiers to specify which courses to download materials from.
- **Download Path**: The directory where the downloaded materials will be stored.

Ensure that `config.py` is updated with your specific details before running the tool.

## Contributing

We welcome contributions to enhance the MyCourses Content Downloader. To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes with clear messages.
4. Submit a pull request detailing your changes.

Please adhere to the coding standards and guidelines outlined in the repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

*Note: This tool is intended for personal use by McGill University students to manage their course materials. Users are responsible for ensuring they comply with McGill's policies and terms of service when using this tool.* 
