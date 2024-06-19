import json
import logging
import os

import yaml

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


def write_text_to_file(file_path, text):
    try:
        with open(file_path, 'w') as file:
            if ".json" in file_path:
                text = json.dumps(text, indent=4)
                file.write(text)
            elif ".yaml" in file_path:
                yaml.dump(text, file)
            else:
                file.write(text)
        logging.info(f"Data Successfully Written to '{file_path}'.")
        return True
    except FileNotFoundError:
        logging.warning(f"File '{file_path}' not found.")
        return False


def read_text_from_file(file_path):
    file_content = ""
    try:
        with open(file_path, 'r') as file:
            if ".json" in file_path:
                file_content = json.load(file)
            elif ".yaml" in file_path:
                file_content = yaml.safe_load(file)
            else:
                file_content = file.read()
    except FileNotFoundError:
        logging.warning(f"File '{file_path}' not found.")
        return None
    except yaml.YAMLError:
        logging.warning(f"YAML {file_path} is Invalid.")
        return None
    except json.JSONDecodeError:
        logging.warning(f"JSON {file_path} is Invalid.")
        return None
    return file_content


class ConfigManager:

    system_params = [
        'AUTO_UPDATE', 'DATABASE_NAME', 'GIT_URL', 'DEST_PATH', 'BRANCH_NAME', 'ACCESS_TOKEN', 'UPDATE_URL',
        'UPDATE_BRANCH', 'UPDATE_ACCESS_TOKEN', 'SMTP_ENABLE', 'SMTP_ADDRESS', 'SMTP_PORT', 'SMTP_USERNAME',
        'SMTP_PASSWORD', 'RECIPIENT_EMAIL', 'EXTERNAL_URL', 'OPEN_AI_KEY'
    ]
    metadata_params = [
        'Name', 'Description', "URL", "Status", "Remarks", "Date", "Level", "Notes", "Companies", "Concepts",
        "CountInclusion", "SheetItemStatus"
    ]
    common_statuses = ['TODO', 'INPROGRESS', 'COMPLETED']
    status_mapper = {
        'To Do': 'TODO',
        'In Progress': 'INPROGRESS',
        'Completed': 'COMPLETED'
    }
    days = [
        {'MONDAY', 0},
        {'TUESDAY', 1},
        {'WEDNESDAY', 2},
        {'THURSDAY', 3},
        {'FRIDAY', 4},
        {'SATURDAY', 5},
        {'SUNDAY', 5}
    ]
    recurrence_types = ['ONCE', 'EVERY', "DAILY", "MONTHLY", "WEEKLY"]

    def __init__(self):
        self.environ = {}
        self.set_environment()

    def set_environment(self):
        self.environ = read_text_from_file("../config.yaml")


# Instantiate the ConfigManager class to set up the environment
config_manager = ConfigManager()
