import json
import logging
import os
import platform
import re
import shutil
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
    update_url = sysenv.environ["UPDATE_URL"]
if "UPDATE_BRANCH" in sysenv.environ:
    update_branch = sysenv.environ["UPDATE_BRANCH"]
if "UPDATE_ACCESS_TOKEN" in sysenv.environ:
    update_access_token = sysenv.environ["UPDATE_ACCESS_TOKEN"]


def recursive_chmod(path, mode):
    for root, dirs, files in os.walk(path):
        os.chmod(root, mode)
        for directory in dirs:
            os.chmod(os.path.join(root, directory), mode)
        for file in files:
            os.chmod(os.path.join(root, file), mode)


def send_email(subject, body_text, body_html):
    # Fetch SMTP credentials from environment variables
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = os.environ.get('SMTP_PORT')
    smtp_username = os.environ.get('SMTP_USERNAME')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    recipient_email = os.environ.get('RECIPIENT_EMAIL')

    if not (smtp_server and smtp_port and smtp_username and smtp_password):
        logging.info("SMTP environment variables not set.")

    # Create the email message
    message = MIMEMultipart("alternative")
    message["From"] = smtp_username
    message["To"] = recipient_email
    message["Subject"] = subject

    # Attach both plain text and HTML versions of the body
    message.attach(MIMEText(body_text, "plain"))
    message.attach(MIMEText(body_html, "html"))

    # Connect to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()

    # Log in to the SMTP server
    server.login(smtp_username, smtp_password)

    # Send the email
    server.sendmail(smtp_username, recipient_email, message.as_string())

    # Quit the SMTP server
    server.quit()


def remove_git_folder(path):
    git_folder = os.path.join(path, '.git')

    try:
        if os.path.exists(git_folder):
            if platform.system() == 'Windows':
                # On Windows, recursively remove the .git folder
                os.system(f'del /F /S /Q /A "{git_folder}"')
            elif platform.system() == 'Linux':
                # On Linux, use subprocess to execute shell command to remove the .git folder
                os.system(f'rm -rf {git_folder}')
            logging.info(f"Removed .git folder at '{git_folder}'")
        else:
            logging.info(f".git folder not found at '{git_folder}'")
    except Exception as e:
        logging.info(f"Error occurred: {str(e)}")


def clone_repository(repo_url, branch, dest_path, access_token):
    if os.path.exists(dest_path):
        remove_directory(dest_path)
    try:
        command = ['git', 'clone', '--branch', branch]
        if access_token:
            # Include the access token in the clone URL for authentication
            protocol = repo_url.split("://")[0]
            url = repo_url.split("://")[1]
            repository_url_with_token = f'{protocol}://{access_token}@{url}'
            command.append(repository_url_with_token)
        else:
            command.append(repo_url)

        command.append(dest_path)

        subprocess.check_output(command)
        remove_git_folder(dest_path)
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
            shutil.rmtree(os.path.abspath(dest_path), ignore_errors=True)

        elif platform.system() == 'Linux':
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
