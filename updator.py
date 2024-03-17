import json
import logging
import re
import time
from datetime import datetime
import database
import os

import sysenv
import utility

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

repo_url = sysenv.environ["GIT_URL"]
dest_path = "codebase"
if "DEST_PATH" in sysenv.environ:
    dest_path = sysenv.environ["DEST_PATH"]
branch = "master"
if "BRANCH_NAME" in sysenv.environ:
    branch = sysenv.environ["BRANCH_NAME"]
access_token = None
if "ACCESS_TOKEN" in sysenv.environ:
    access_token = sysenv.environ["ACCESS_TOKEN"]


# Clone the specific Git Repository
def clone_repository():
    return utility.clone_repository(repo_url, branch, dest_path, access_token)


# Removes the Cloned Repository
def remove_directory():
    return utility.remove_directory(dest_path)


# Reads the folder and extracts the metadata from source files
def read_repository():
    folders = utility.get_folder_names(dest_path + "/src")
    questions_map = {}
    for folder in folders:
        questions_map[folder] = extract_metadata_from_files(dest_path + "/src/" + folders[folder])
    return questions_map


# To fetch the platforms from platforms.json
def get_platforms():
    filepath = dest_path + "/platforms.json"
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    else:
        return None


# To save the platforms from platforms.json
def save_platforms(connector):
    filepath = dest_path + "/platforms.json"
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
            logging.info(f"Platforms Retrieved: {data}")
            for item in data:
                values = (
                    item["name"],
                    item["url"],
                    item["icon"]
                )
                database.insert_data(connector, "platforms", values)
            logging.info(f"Platforms Saved to SQlLite DB: {database.database}")
    else:
        logging.warning(f"Platforms Not Found: {filepath}")
        return None


# To fetch the trackers from trackers.json
def get_trackers():
    filepath = dest_path + "/trackers.json"
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    else:
        return None


# To save the trackers from trackers.json
def save_trackers(connector):
    filepath = dest_path + "/trackers.json"
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
            logging.info(f"Trackers Retrieved: {data}")
            for item in data:
                values = (
                    item["name"],
                    item["level"]
                )
                database.insert_data(connector, "trackers", values)
            logging.info(f"Trackers Saved to SQlLite DB: {database.database}")
    else:
        logging.warning(f"Trackers Not Found: {filepath}")
        return None


# To fetch the reminders from reminders.json
def get_reminders():
    filepath = dest_path + "/reminders.json"
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    else:
        return None


# To save the reminders from reminders.json
def save_reminders(connector):
    filepath = dest_path + "/reminders.json"
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
            logging.info(f"Reminders Retrieved: {data}")
            for item in data:
                values = (
                    item["name"],
                    item["desc"],
                    item["recurrence"],
                    item["start_time"] if "start_time" in item else None,
                    item["end_time"] if "end_time" in item else None,
                    item["date"] if "date" in item else None,
                )
                database.insert_data(connector, "reminders", values)
            logging.info(f"Reminders Saved to SQlLite DB: {database.database}")
    else:
        logging.warning(f"Reminders Not Found: {filepath}")
        return None


# To fetch the companies from problems
def get_companies(connector):
    distinct_companies = set()

    rows = database.fetch_data(connector, "SELECT companies FROM problems")
    for row in rows:
        companies_string = row[0]
        if companies_string is not None:
            companies = companies_string.split(":")
            for company in companies:
                distinct_companies.add(company.strip())

    return distinct_companies


# To save the companies
def save_companies(connector):
    data = get_companies(connector)
    logging.info(f"Companies Retrieved: {data}")
    for item in data:
        values = (
            item,
        )
        database.insert_data(connector, "companies", values)
    logging.info(f"Companies Saved to SQlLite DB: {database.database}")


def get_remarks(connector):
    distinct_remarks = set()

    rows = database.fetch_data(connector, "SELECT remarks FROM problems")
    for row in rows:
        remark_string = row[0]
        if remark_string is not None:
            remarks = remark_string.split(":")
            for remark in remarks:
                distinct_remarks.add(remark.strip())

    return distinct_remarks


def save_remarks(connector):
    data = get_remarks(connector)
    logging.info(f"Remarks Retrieved: {data}")
    for item in data:
        values = (
            item,
        )
        database.insert_data(connector, "remarks", values)
    logging.info(f"Remarks Saved to SQlLite DB: {database.database}")


# To fetch the settings from application.json
def get_settings():
    filepath = dest_path + "/application.json"
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    else:
        return None


# To save the settings from application.json
def save_settings(connector):
    filepath = dest_path + "/application.json"
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
            logging.info(f"Application Config Retrieved: {data}")
            values = (
                'darkTheme',
                json.dumps(data['dark'])
            )
            database.insert_data(connector, "settings", values)
            values = (
                'lightTheme',
                json.dumps(data['light'])
            )
            database.insert_data(connector, "settings", values)
            logging.info(f"Application Config Saved to SQlLite DB: {database.database}")
    else:
        logging.warning(f"Application Config Not Found: {filepath}")
        return None


# Utility function to extract the metadata and convert into map
# key = folder_names(converted) and value = (map with key = filename and value = metadata)
def extract_metadata_from_files(directory):
    metadata_map = {}

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r+', encoding='utf-8') as f:
                    content = f.read()
                    # Use regular expressions to extract content between <metadata> and </metadata> tags
                    match = re.search(r'<metadata>(.*?)</metadata>', content, re.DOTALL)

                    if match:
                        metadata_content = match.group(1).replace("*", "").replace("\n", "").strip().split(
                            ",")
                        metadata_map[file.split(".")[0]] = convert_metadata_list(metadata_content)
                        metadata_map[file.split(".")[0]]['Path'] = file_path.replace('\\', '/')
                        # Rewind the file pointer to the beginning of the file
                        f.seek(0)
                        # Replace metadata tags with file path
                        new_content = re.sub(r'<metadata>.*?</metadata>',
                                             file_path.replace(dest_path, "File: ").replace('\\', '/'), content,
                                             flags=re.DOTALL)
                        # Write back the new content
                        f.write(new_content)
                        # Truncate the file to remove any remaining content after the end of the new content
                        f.truncate()
                f.close()

            except Exception as e:
                logging.warning(f"Cannot Extract Metadata from Repository {file_path}: {e}")

    return metadata_map


# Utility function to convert extracted metadata from list to map
def convert_metadata_list(list):
    metadata = {}
    for item in list:
        if ":-" in item:
            key = item.split(":-")[0].strip()
            value = item.split(":-")[1].strip()
            metadata[key] = value
    return metadata


# Saves MetaData In Tables
def save_metadata(connector):
    if clone_repository():
        metadata_response = read_repository()
        logging.info(f"Metadata Retrieved: {metadata_response}")
        for metadata in metadata_response:
            typeid = database.insert_data(connector, 'problem_type', (metadata, None))
            for name in metadata_response[metadata]:
                filename = metadata_response.get(metadata, {}).get(name, {}).get('Path', None)
                problem_name = metadata_response.get(metadata, {}).get(name, {}).get('Name', name)
                desp = metadata_response.get(metadata, {}).get(name, {}).get('Description', None)
                status = metadata_response.get(metadata, {}).get(name, {}).get('Status', None)
                url = metadata_response.get(metadata, {}).get(name, {}).get('URL', None)
                notes = metadata_response.get(metadata, {}).get(name, {}).get('Notes', None)
                date_added = metadata_response.get(metadata, {}).get(name, {}).get('Date', None)
                level = metadata_response.get(metadata, {}).get(name, {}).get('Level', None)
                companies = metadata_response.get(metadata, {}).get(name, {}).get('Companies', None)
                remarks = metadata_response.get(metadata, {}).get(name, {}).get('Remarks', None)
                if date_added is not None:
                    date_added = datetime.strptime(date_added, '%Y-%m-%d')
                database.insert_data(connector, "problems",
                                     (problem_name, desp, typeid, url, status, notes, date_added, level, filename,
                                      companies, remarks))
        logging.info(f"Metadata Saved to SQlLite DB: {database.database}")


def init_parent_repo():
    create_lock_file("codebase.lock")
    # Init Database
    database.remove_database()
    connector = database.init_database()
    save_metadata(connector)
    save_trackers(connector)
    save_reminders(connector)
    save_platforms(connector)
    save_companies(connector)
    save_remarks(connector)
    save_settings(connector)
    database.close_connection(connector)
    remove_lock_file("codebase.lock")


def init_system():
    init_parent_repo()
    # Check Update
    current_meta = utility.get_current_application_metadata()
    new_meta = utility.get_updated_application_metadata()
    if utility.update_available(current_meta, new_meta):
        utility.prepare_updates()


def create_lock_file(lock_file_path):
    # Check if lock file already exists
    if os.path.exists(lock_file_path):
        logging.warning("Lock file already exists. Another instance might be running.")
        return False

    # Create lock file
    with open(lock_file_path, 'w') as lock_file:
        lock_file.write("Lock file created at: " + time.ctime())
    logging.info("Lock file created successfully.")
    return True


def remove_lock_file(lock_file_path):
    # Check if lock file exists
    if os.path.exists(lock_file_path):
        os.remove(lock_file_path)
        logging.info("Lock file removed successfully.")
    else:
        logging.warning("Lock file doesn't exist.")


def send_inactivity_reminder():
    conn = database.create_connection()
    last_date_added = database.fetch_data(conn, "SELECT DATE(date_added) FROM problems ORDER BY date_added DESC LIMIT "
                                                "1;")
    if len(last_date_added) > 0:
        last_date_added = datetime.strptime(last_date_added[0][0], "%Y-%m-%d").date()
        current_datetime = datetime.now().date()
        difference = current_datetime - last_date_added
        # Extract hours and days from the timedelta object
        hours_difference = int(difference.total_seconds()//3600)
        if hours_difference > 24:
            print(hours_difference)
            #utility.send_email("", "", "")


def send_reminder_email():
    conn = database.create_connection()
    reminders = database.fetch_data(conn, "select * from reminders")
    for reminder in reminders:
        print(reminder)


if __name__ == "__main__":
    init_system()
