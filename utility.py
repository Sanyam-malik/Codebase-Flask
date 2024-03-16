import json
import logging
import os
import platform
import shutil
import subprocess

import sysenv

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

update_url = ''
update_branch = ''
update_access_token = ''
if "UPDATE_URL" in sysenv.environ:
    update_url = sysenv.environ["UPDATE_URL"] + ".git"
if "UPDATE_BRANCH" in sysenv.environ:
    update_branch = sysenv.environ["UPDATE_BRANCH"]
if "UPDATE_ACCESS_TOKEN" in sysenv.environ:
    update_access_token = sysenv.environ["UPDATE_ACCESS_TOKEN"]


def clone_repository(repo_url, branch, dest_path, access_token):
    if os.path.exists(dest_path):
        remove_directory(dest_path)
    try:

        command = ['git', 'clone', '--branch', branch]

        if access_token:
            # Include the access token in the clone URL for authentication
            protocol = repo_url.split("://")[0]
            repository_url_with_token = f'{protocol}://{access_token}@{repo_url.split("://")[1]}'
            command.append(repository_url_with_token)
        else:
            command.append(repo_url)

        command.append(dest_path)

        subprocess.check_output(command)
        os.chmod(dest_path, 0o777)
        logging.info(f"Repository cloned successfully: {dest_path}")
    except subprocess.CalledProcessError as e:
        logging.warning(f"Error while cloning repository: {e}")
        return False
    return True


# Removes the Cloned Repository
def remove_directory(dest_path):
    try:
        if platform.system() == 'Windows':
            # Use shutil.rmtree to remove most of the directory contents
            shutil.rmtree(dest_path, ignore_errors=True)

            # Use subprocess to run the 'rmdir' command for any remaining files/folders
            subprocess.run(['rmdir', '/s', '/q', dest_path], check=True)
        elif platform.system() == 'Linux':
            # Use shutil.rmtree to remove most of the directory contents
            shutil.rmtree(dest_path, ignore_errors=True)

            # Use subprocess to run the 'rm' command recursively
            subprocess.run(['rm', '-rf', dest_path], check=True)
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

    except OSError as e:
        logging.warning(f"Error creating folder: {e}")


def copy_file(source_path, destination_path):
    try:
        shutil.copy2(source_path, destination_path)
        logging.info(f"File copied successfully from {source_path} to {destination_path}")
    except Exception as e:
        logging.warning(f"Error copying file: {e}")


def get_updated_application_metadata():
    try:
        clone_repository(update_url, update_branch, "temp_app", update_access_token)
        files = get_files_in_folder("temp_app")
        if "app.json" in files:
            with open("temp_app/app.json", 'r') as file:
                data = json.load(file)
            return data
        remove_directory("temp_app")
    except Exception as e:
        logging.warning(f"Error occured while fetching updates..{e}")
    return {}


def get_current_application_metadata():
    if os.path.exists("app.json"):
        with open("app.json", 'r') as file:
            data = json.load(file)
        return data
    return {}


def update_available(current_meta, new_meta):
    try:
        current_version = current_meta["version"]
        new_version = new_meta["version"]
        if current_version < new_version:
            return True
        else:
            return False
    except Exception as e:
        logging.warning(f"Error while fetching comparing versions..{e}")


def prepare_updates():
    try:
        files = get_files_in_folder("temp_app")
        create_folder("updates")
        for file in files:
            copy_file("temp_app/" + file, "updates/" + file)
    except Exception as e:
        logging.warning(f"Error while preparing system for update..{e}")
