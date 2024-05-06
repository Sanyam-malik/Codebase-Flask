import json
import logging

import yaml

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

environ = {}
system_params = ['AUTO_UPDATE', 'DATABASE_NAME', 'GIT_URL', 'DEST_PATH', 'BRANCH_NAME', 'ACCESS_TOKEN', 'UPDATE_URL'
    , 'UPDATE_BRANCH', 'UPDATE_ACCESS_TOKEN', 'SMTP_ENABLE', 'SMTP_ADDRESS', 'SMTP_PORT', 'SMTP_USERNAME'
    , 'SMTP_PASSWORD', 'RECIPIENT_EMAIL', 'EXTERNAL_URL']

metadata_params = ['Name', 'Description', "URL", "Status", "Remarks", "Date", "Level", "Notes", "Companies", "Concepts",
                   "CountInclusion", "SheetItem"]

common_statuses = ['TODO', 'INPROGRESS', 'COMPLETED']


def set_environment():
    global environ
    environ = read_text_from_file("config.yaml")


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
    except yaml.YAMLError as e:
        logging.warning(f"YAML {file_path} is Invalid.")
        return None
    except json.JSONDecodeError:
        logging.warning(f"JSON {file_path} is Invalid.")
        return None
    return file_content


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
    except FileNotFoundError as e:
        logging.warning(f"File '{file_path}' not found.")
        return False


set_environment()
