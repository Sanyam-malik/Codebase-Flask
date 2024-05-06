import logging
import os
import platform
import subprocess

import utility

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


def add_folder_to_gitignore(folder_path):
    gitignore_path = ".gitignore"

    # Check if .gitignore file exists
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w') as f:
            f.write("")  # Create an empty .gitignore file if it doesn't exist

    # Read existing contents of .gitignore
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()

    # Check if the folder_path already exists in .gitignore
    if folder_path not in gitignore_content:
        # Append the folder_path to .gitignore
        with open(gitignore_path, 'a') as f:
            f.write("\n" + folder_path + "/\n")
        logging.info(f"Added '{folder_path}' to .gitignore")
    else:
        logging.info(f"'{folder_path}' already exists in .gitignore")


def remove_git_folder(path, delete_repo=True):
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
        if delete_repo is True:
            utility.remove_directory(path)
    except Exception as e:
        logging.info(f"Error occurred: {str(e)}")


def clone_repository(repo_url, branch, dest_path, access_token):
    add_folder_to_gitignore(dest_path)
    if os.path.exists(dest_path):
        remove_git_folder(dest_path)
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
        logging.info(f"Repository cloned successfully: {dest_path}")
    except subprocess.CalledProcessError as e:
        logging.warning(f"Error while cloning repository: {e}")
        return False
    return True


def commit_file(file_path, access_token):
    if len(access_token) > 0:
        file_path_array = file_path.split("/")
        dest_path = file_path_array[0]
        file_name = '/'.join(file_path_array[1:])

        commit_message = "Updated " + file_name

        try:
            # Add the file to the staging area
            subprocess.run(['git', 'add', file_name], cwd=dest_path)

            # Commit the changes
            subprocess.run(['git', 'commit', '-m', commit_message], cwd=dest_path)

            logging.info(f"File {file_name} committed successfully.")
        except Exception as e:
            logging.warning(f"Error while committing to repository: {e}")
    else:
        logging.warning(f"Access Code is not Present")


def push_to_repo(repo_url, branch, dest_path, access_token):
    if len(access_token) > 0:
        username = access_token.split(":")[0]
        password = access_token.split(":")[1]

        protocol = repo_url.split("://")[0]
        url = repo_url.split("://")[1]

        try:
            # Push to the remote repository using the access token
            subprocess.run(['git', 'push', protocol + '://oauth2:' + password + '@' + url, branch], cwd=dest_path)

            logging.info("Changes Pushed successfully.")
        except Exception as e:
            logging.warning(f"Error while pushing to repository: {e}")
    else:
        logging.warning(f"Access Code is not Present")
