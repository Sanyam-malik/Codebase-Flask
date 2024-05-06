import json
import logging
import multiprocessing
import re
import time
from datetime import datetime
import requests
from sqlalchemy import desc, func

import application_utility
import database_utility
import os

import email_utility
import git_utility
import appenv
import utility
from models import Problem, Reminder, Quote

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

repo_url = appenv.environ["GIT_URL"]

dest_path = "codebase"
if "DEST_PATH" in appenv.environ:
    dest_path = appenv.environ["DEST_PATH"]

branch = "master"
if "BRANCH_NAME" in appenv.environ:
    branch = appenv.environ["BRANCH_NAME"]

access_token = None
if "ACCESS_TOKEN" in appenv.environ:
    access_token = appenv.environ["ACCESS_TOKEN"]


# Clone the specific Git Repository
def clone_repository():
    return git_utility.clone_repository(repo_url, branch, dest_path, access_token)


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


# To fetch the notes from notes folder
def get_notes():
    folders = []
    if os.path.exists(dest_path + "/notes"):
        folders = utility.get_folder_names(dest_path + "/notes")
    return folders


# To save the quotes from api
def save_quotes(connector):
    try:
        response = requests.get('https://zenquotes.io/api/quotes')
        for item in response.json():
            author = item['a']
            content = item['q']
            dots = content.count('.')
            if dots == 1:
                content = content[:-1]
            result = connector.query(func.count(Quote.id)).filter(Quote.content == content).scalar()
            if result == 0:
                database_utility.insert_data(connector, "quotes", (author, content))
            else:
                continue
    except Exception as e:
        logging.warning("Cannot Call Quotes API.....", e)


# To save the notes from notes folder
def save_notes(connector):
    try:
        directories = get_notes()
        logging.info(f"Notes Retrieved: {directories.values()}")
        for directory in directories:
            for root, dirs, files in os.walk(dest_path + "/notes/" + directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    values = (
                        directory,
                        file_path.replace('\\', '/').replace(dest_path, "<repo_path>"),
                        os.path.splitext(file_path)[1]
                    )
                    database_utility.insert_data(connector, "notes", values)
        logging.info(f"Notes Saved to SQlLite DB: {database_utility.database}")
    except Exception as e:
        logging.warning("Exception while retrieving notes... \n", e)


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
                database_utility.insert_data(connector, "platforms", values)
            logging.info(f"Platforms Saved to SQlLite DB: {database_utility.database}")
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
                database_utility.insert_data(connector, "trackers", values)
            logging.info(f"Trackers Saved to SQlLite DB: {database_utility.database}")
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
                database_utility.insert_data(connector, "reminders", values)
            logging.info(f"Reminders Saved to SQlLite DB: {database_utility.database}")
    else:
        logging.warning(f"Reminders Not Found: {filepath}")
        return None


# To fetch the companies from problems
def get_companies(connector):
    distinct_companies = set()

    rows = connector.query(Problem.companies).all()
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
        logo = company_logo(item)
        values = (
            item, logo, utility.get_random_light_color(), utility.get_random_dark_color()
        )
        database_utility.insert_data(connector, "companies", values)
    logging.info(f"Companies Saved to SQlLite DB: {database_utility.database}")


def company_logo(company):
    logo = None
    """
    headers = {'X-Api-Key': 'TBJpqy2pxTX33CWjVzG90Q==onYKhXL1Q9pSWirc'}
    api_url = 'https://api.api-ninjas.com/v1/logo?name={}'.format(company)
    response = requests.get(api_url, headers=headers)
    if response.status_code == requests.codes.ok:
        json_response = response.json()
        if len(json_response) > 0:
            logo = json_response[0]["image"]
    else:
        logging.info("Cannot Fetch Company Logo Using Name")

    if logo is None:
        api_url = 'https://api.api-ninjas.com/v1/logo?ticker={}'.format(company)
        response = requests.get(api_url, headers=headers)
        if response.status_code == requests.codes.ok:
            json_response = response.json()
            if len(json_response) > 0:
                logo = json_response[0]["image"]
        else:
            logging.info("Cannot Fetch Company Logo Using Ticker")
    """
    return logo


def get_remarks(connector):
    distinct_remarks = set()

    rows = connector.query(Problem.remarks).all()
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
        database_utility.insert_data(connector, "remarks", values)
    logging.info(f"Remarks Saved to SQlLite DB: {database_utility.database}")


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

            for item in data.keys():
                if item == 'theme':
                    if 'dark' in data['theme']:
                        values = (
                            'darkTheme',
                            json.dumps(data['theme']['dark'])
                        )
                        database_utility.insert_data(connector, "settings", values)
                    if 'light' in data['theme']:
                        values = (
                            'lightTheme',
                            json.dumps(data['theme']['light'])
                        )
                        database_utility.insert_data(connector, "settings", values)
                else:
                    values = (
                        "app"+str(item).title(),
                        data[item]
                    )
                    database_utility.insert_data(connector, "settings", values)
            logging.info(f"Application Config Saved to SQlLite DB: {database_utility.database}")
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
                with (open(file_path, 'r+', encoding='utf-8') as f):
                    content = f.read()
                    # Use regular expressions to extract content between <metadata> and </metadata> tags
                    match = re.search(r'<metadata>(.*?)</metadata>', content, re.DOTALL)

                    if match:
                        sub_dir = root.replace('\\', '/').replace(directory, '').replace('/', ':').strip()
                        if len(sub_dir) > 0 and sub_dir[0] == ':':
                            sub_dir = sub_dir[1:len(sub_dir)]
                        metadata_content = match.group(1).replace("*", "").replace("\n", "").strip().split(
                            ",")
                        metadata_map[file.split(".")[0]] = convert_metadata_list(metadata_content)
                        metadata_map[file.split(".")[0]]['Path'] = file_path.replace('\\', '/').replace(dest_path,
                                                                                                        "<repo_path>")
                        if len(sub_dir) > 0:
                            metadata_map[file.split(".")[0]]['SubDirectory'] = sub_dir
                f.close()

            except Exception as e:
                logging.warning(f"Cannot Extract Metadata from Repository {file_path}: {e}")

    return metadata_map


# Utility function to convert extracted metadata from list to map
def convert_metadata_list(list):
    metadata = {}
    for item in list:
        for param in appenv.metadata_params:
            start_tag = '<{}>'.format(param.lower())
            end_tag = '</{}>'.format(param.lower())
            start_index = item.find(start_tag) + len(start_tag)
            end_index = item.find(end_tag)
            if start_index != -1 and end_index != -1:
                metadata[param] = item[start_index:end_index].strip()
            else:
                metadata[param] = None
    return metadata


# Saves MetaData In Tables
def save_metadata(connector):
    if clone_repository():
        metadata_response = read_repository()
        logging.info(f"Metadata Retrieved: {metadata_response}")
        for metadata in metadata_response:
            typeid = database_utility.insert_data(connector, 'problem_type', (metadata, None))
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
                concepts = metadata_response.get(metadata, {}).get(name, {}).get('Concepts', None)
                subdirectory = metadata_response.get(metadata, {}).get(name, {}).get('SubDirectory', None)
                include_count = metadata_response.get(metadata, {}).get(name, {}).get('CountInclusion', True)
                if isinstance(include_count, str):
                    if "yes" == include_count or "true" == include_count:
                        include_count = True
                    else:
                        include_count = False

                if date_added is not None:
                    date_added = datetime.strptime(date_added, '%Y-%m-%d')
                database_utility.insert_data(connector, "problems",
                                             (problem_name, desp, typeid, url, status, notes, level, companies, remarks
                                              , concepts, date_added, filename, subdirectory, None, include_count))
        logging.info(f"Metadata Saved to SQlLite DB: {database_utility.database}")


def get_songs():
    filepath = dest_path + "/songs.json"
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    else:
        return None


def init_parent_repo():
    create_lock_file("codebase.lock")
    # Init Database
    database_utility.remove_database()
    connector = database_utility.init_database()
    save_quotes(connector)
    save_metadata(connector)
    save_trackers(connector)
    save_reminders(connector)
    save_platforms(connector)
    save_companies(connector)
    save_remarks(connector)
    save_settings(connector)
    save_notes(connector)
    database_utility.close_connection(connector)
    remove_lock_file("codebase.lock")


def init_system(manual_update=False):
    if manual_update is True:
        utility.copy_folder(dest_path, "readonly_" + dest_path)
        git_utility.remove_git_folder("readonly_" + dest_path, False)

    init_parent_repo()
    multiprocessing.Process(target=send_mail, args=()).start()

    if manual_update is True:
        utility.delete_file("readonly_" + database_utility.database)
        utility.remove_directory("readonly_" + dest_path)
    # Check Update
    get_app_updates()


def get_app_updates():
    if appenv.environ['AUTO_UPDATE'] == 'true':
        current_meta = application_utility.get_current_application_metadata()
        new_meta = application_utility.get_updated_application_metadata()
        if application_utility.update_available(current_meta, new_meta):
            application_utility.prepare_updates()


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


def send_mail():
    send_inactivity_reminder()
    # send_reminder_email()


def send_inactivity_reminder():
    subject = "Regarding your Inactivity"
    current_datetime = datetime.now().date()

    conn = database_utility.create_connection()
    last_date_added = conn.query(Problem.date_added).order_by(desc(Problem.date_added)).first()
    is_mail_send = email_utility.check_if_email_send(subject, str(current_datetime))

    last_date_added = last_date_added[0] if last_date_added else None
    if last_date_added is not None and is_mail_send is False:
        last_date_added = last_date_added.date()

        difference = current_datetime - last_date_added
        # Extract hours and days from the timedelta object
        hours_difference = int(difference.total_seconds() // 3600)
        if hours_difference > 24:
            replacements = {
                "{{HOURS}}": str(hours_difference),
                "{{URL}}": appenv.environ['EXTERNAL_URL']
            }
            template = email_utility.fetch_template('no-activity', replacements)
            email_utility.send_email(subject, template["plain_content"], template["html_content"])


def send_reminder_email():
    conn = database_utility.create_connection()
    reminders = conn.query(Reminder).all()
    for reminder in reminders:
        replacements = {
            "{{EVENTNAME}}": str(reminder["name"]),
            "{{URL}}": ""
        }
        template = email_utility.fetch_template('no-activity', replacements)
        subject = "You have a Upcoming event"
        email_utility.send_email(subject, template["plain_content"], template["html_content"])


def upload_conditions(additional_params, uploaded_files=None):
    invalid_files = []
    if uploaded_files is None:
        uploaded_files = []

    if "parse" in additional_params.keys() and additional_params['parse'] == "true":
        for file_path in uploaded_files:
            response, code = application_utility.validate_json_from_file(file_path, additional_params['type'])
            if code != 200:
                invalid_files.append(file_path)
            else:
                save_data(additional_params['type'], file_path)

    if len(invalid_files) > 0:
        return {"message": "Invalid Files", "files": invalid_files}, 400
    else:
        return {"message": "Success"}, 200


def save_data(dt_type, uploaded_file_path):
    file_paths = []
    file_data = utility.read_text_from_file(uploaded_file_path)

    if dt_type == "event":
        file_paths = save_json_file(get_reminders(), file_data, f"{dest_path}/reminders.json")
    elif dt_type == "tracker":
        file_paths = save_json_file(get_trackers(), file_data, f"{dest_path}/trackers.json")
    elif dt_type == "link":
        file_paths = save_json_file(get_platforms(), file_data, f"{dest_path}/platforms.json")
    elif dt_type == "note":
        file_paths = save_new_note(file_data)
    if len(file_paths) > 0:
        for file_path in file_paths:
            git_utility.commit_file(file_path, access_token)
        git_utility.push_to_repo(repo_url, branch, dest_path, access_token)
        init_system()


def save_json_file(data, file_data, file_path):
    file_paths = []
    data.append(file_data)
    response = utility.write_text_to_file(file_path, data)
    if response is True:
        file_paths.append(file_path)
    return file_paths


def save_new_note(file_data):
    file_paths = []

    folder_name = file_data["name"]
    folder_path = dest_path + "/notes/" + folder_name
    files = file_data["content"]
    if os.path.exists(folder_path):
        return file_paths
    else:
        os.mkdir(folder_path)
        for file in files:
            file_name = file['name']
            file_path = f"{dest_path}/notes/{folder_name}/{file_name}"
            if "url" in file:
                response = utility.download_file_from_url(file['url'], file_path)
                if response is True:
                    file_paths.append(file_path)
            else:
                content = ''
                if "content" in file:
                    content = file['content']
                response = utility.write_text_to_file(file_path, content)
                if response is True:
                    file_paths.append(file_path)
        utility.delete_empty_folder(folder_path)
    return file_paths


if __name__ == "__main__":
    init_system()
