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
    else:
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


def get_current_branch(repo_path):
    """
    Get the current branch of the given Git repository.

    :param repo_path: Path to the Git repository
    :return: Current branch name
    """
    try:
        # Run the git branch --show-current command
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            text=True,
            capture_output=True,
            check=True
        )
        # Strip leading/trailing whitespace from the branch name
        current_branch = result.stdout.strip()
        return current_branch
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None


def switch_branch(repo_path, branch_name):
    """
    Switch to a specified branch in the local git repository.

    Parameters:
    repo_path (str): The file path to the local git repository.
    branch_name (str): The name of the branch to switch to.

    Returns:
    bool: True if the command was successful, False otherwise.
    """
    try:
        # Run 'git switch' command to change branches
        result = subprocess.run(['git', 'switch', branch_name], cwd=repo_path,
                                text=True, capture_output=True, check=True)

        logging.info(f"Branch Switched to {branch_name}.....")
        # If the command is successful, return True
        return True

    except subprocess.CalledProcessError as e:
        # If an error occurs, print the error and return False
        logging.info(f"Cannot Switch Branch....\n{e}")
        return False


def pull_rebase(repo_path):
    """
    Pull the latest changes from the remote repository and rebase.

    Parameters:
    repo_path (str): The file path to the local git repository.

    Returns:
    bool: True if the command was successful, False otherwise.
    """
    try:
        # Run 'git pull --rebase' command
        result = subprocess.run(['git', 'pull', '--rebase'], cwd=repo_path,
                                text=True, capture_output=True, check=True)
        logging.info(f"Repository Rebase was Successful.....")
        # If the command is successful, return True
        return True

    except subprocess.CalledProcessError as e:
        # If an error occurs, print the error and return False
        logging.info(f"Repository Rebase was Unsuccessful.....{e}")
        return False


def get_branches(repo_path):
    """
    Get a list of all branches in the given Git repository.

    :param repo_path: Path to the Git repository
    :return: List of unique branch names
    """
    try:
        # Run the git branch -a command
        result = subprocess.run(
            ["git", "branch", "-a"],
            cwd=repo_path,
            text=True,
            capture_output=True,
            check=True
        )
        # Split the output into lines
        branches = result.stdout.strip().split('\n')
        # Use a set to avoid redundancy
        cleaned_branches = set()
        for branch in branches:
            branch = branch.strip()
            if 'HEAD' in branch:
                continue
            # Remove leading '*' if present and get the last part of the branch name
            if branch.startswith('*'):
                branch = branch[1:].strip()
            branch = branch.split('/')[-1]
            cleaned_branches.add(branch)
        return list(cleaned_branches)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return []


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
