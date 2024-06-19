import json
import logging
import os
import random
import re
import shutil
from datetime import datetime

import requests
import yaml

from config_manager import config_manager as appenv

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

update_url = ''
update_branch = ''
update_access_token = ''
if "UPDATE_URL" in appenv.environ:
    update_url = appenv.environ["UPDATE_URL"]
if "UPDATE_BRANCH" in appenv.environ:
    update_branch = appenv.environ["UPDATE_BRANCH"]
if "UPDATE_ACCESS_TOKEN" in appenv.environ:
    update_access_token = appenv.environ["UPDATE_ACCESS_TOKEN"]


def re_init():
    global update_url, update_branch, update_access_token
    appenv.set_environment()

    if "UPDATE_URL" in appenv.environ:
        update_url = appenv.environ["UPDATE_URL"]
    if "UPDATE_BRANCH" in appenv.environ:
        update_branch = appenv.environ["UPDATE_BRANCH"]
    if "UPDATE_ACCESS_TOKEN" in appenv.environ:
        update_access_token = appenv.environ["UPDATE_ACCESS_TOKEN"]


def download_file_from_url(url, file_path):
    response = True
    try:
        response = requests.get(url)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        response = True
    except Exception as e:
        logging.info("Exception occured while attempting download... \n", e)
        response = False
    return response


def delete_empty_folder(folder_path):
    if os.path.exists(folder_path):
        if len(os.listdir(folder_path)) == 0:
            os.rmdir(folder_path)
            logging.info(f"Folder '{folder_path}' deleted successfully.")
    else:
        logging.warning(f"Folder '{folder_path}' does not exist.")


def delete_folder(folder_path):
    try:
        # Use shutil.rmtree to remove most of the directory contents
        shutil.rmtree(os.path.abspath(folder_path), ignore_errors=True)

        logging.info(f"Folder '{folder_path}' deleted successfully.")
    except Exception as e:
        logging.warning(f"Folder '{folder_path}' does not exist.")
        return False
    return True


# Removes the Cloned Repository
def remove_directory(dest_path):
    try:
        # Use shutil.rmtree to remove most of the directory contents
        shutil.rmtree(os.path.abspath(dest_path), ignore_errors=True)

        logging.info(f"Repository deleted successfully: {dest_path}")
    except Exception as e:
        logging.warning(f"error while removing repository: {e}")
        return False
    return True


# Utility function to fetch the folder names and convert into map
# key = folder_names(converted) and value = folder_names(original)
def get_folder_names(dest_path):
    # Get a list of all entries in the directory
    folder_names = [f for f in os.listdir(dest_path) if os.path.isdir(os.path.join(dest_path, f))]
    folderMap = {}
    for folder in folder_names:
        folder_name = folder.replace("__", "/").replace("_", " ")
        folderMap[folder_name] = folder

    return folderMap


# Utility function to fetch the file names
def get_files_in_folder(folder_path):
    try:
        # Get a list of all files in the folder
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        return files
    except OSError as e:
        logging.warning(f"Error reading files in folder: {e}")
        return []


def create_folder(folder_path):
    try:
        # Check if the folder exists
        if not os.path.exists(folder_path):
            # Create the folder if it does not exist
            os.makedirs(folder_path)
            logging.info(f"Folder '{folder_path}' created.")
        else:
            logging.info(f"Folder '{folder_path}' already exists.")

    except Exception as e:
        logging.warning(f"Error creating folder: {e}")


def copy_folder(source, destination):
    try:
        shutil.copytree(source, destination)
        logging.info(f"Folder '{source}' successfully copied to '{destination}'.")
    except FileExistsError:
        logging.warning(f"Folder '{destination}' already exists.")
    except Exception as e:
        logging.warning(f"Error copying folder: {e}")


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


def copy_file(source_path, destination_path):
    try:
        shutil.copy2(source_path, destination_path)
        logging.info(f"File copied successfully from {source_path} to {destination_path}")
    except Exception as e:
        logging.warning(f"Error copying file: {e}")


def delete_file(file_path):
    try:
        os.remove(file_path)
        logging.info(f"File '{file_path}' deleted successfully.")
    except OSError as e:
        logging.warning(f"Error deleting the file '{file_path}': {e}")


def create_slug(input_string):
    # Convert the string to lowercase and replace spaces with hyphens
    slug = input_string.lower().replace(' ', '-')
    # Remove any characters that are not alphanumeric or hyphens
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'\-+', '-', slug)
    # Remove leading and trailing hyphens
    slug = slug.strip('-')
    return slug


def get_random_dark_color():
    red = random.randint(30, 157)  # Random value between 30 and 157
    green = random.randint(30, 157)  # Random value between 30 and 157
    blue = random.randint(30, 157)  # Random value between 30 and 157

    # Construct the color string in hexadecimal format
    color = '#{0:02x}{1:02x}{2:02x}'.format(red, green, blue)

    return color


def get_random_light_color():
    red = random.randint(158, 255)  # Random value between 158 and 255
    green = random.randint(158, 255)  # Random value between 158 and 255
    blue = random.randint(158, 255)  # Random value between 158 and 255

    # Construct the color string in hexadecimal format
    color = '#{0:02x}{1:02x}{2:02x}'.format(red, green, blue)

    return color


def get_running_repo(dest_path):
    backup_repo = f"readonly_{dest_path}"
    if os.path.exists("codebase.lock") and os.path.exists(backup_repo):
        return backup_repo
    else:
        return dest_path


def parse_date(date_str):
    if date_str and len(str(date_str).strip()) > 0:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    return None


def parse_time(time_str):
    if time_str and len(str(time_str).strip()) > 0:
        return datetime.strptime(time_str, "%H:%M").time()
    return None
