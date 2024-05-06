import logging
import os
import shutil
import subprocess

import appenv

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

auto_update = "yes"
if "AUTO_UPDATE" in appenv.environ:
    auto_update = appenv.environ["AUTO_UPDATE"]


def get_files_in_folder(folder_path):
    try:
        # Get a list of all files in the folder
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        return files
    except OSError as e:
        logging.warning(f"Error reading files in folder: {e}")
        return []


def copy_file(source_path, destination_path):
    try:
        shutil.copy2(source_path, destination_path)
    except Exception as e:
        logging.warning(f"Error copying file: {e}")


def remove_directory(dest_path):
    try:
        # Use shutil.rmtree to remove most of the directory contents
        shutil.rmtree(dest_path, ignore_errors=True)

        # Use subprocess to run the 'rmdir' command for any remaining files/folders
        subprocess.run(['rmdir', '/s', '/q', dest_path], shell=True, check=True)
    except Exception as e:
        logging.warning(f"Error while removing repository: {e}")
        return False
    return True


def run_codebase(script_path):
    try:
        with open(script_path, 'r') as script_file:
            script_code = script_file.read()
            exec(script_code)
    except Exception as e:
        logging.warning(f"Error running the script: {e}")


def install_updates():
    try:
        files = get_files_in_folder("updates")
        for file in files:
            copy_file("updates/" + file, file)
        remove_directory("updates")
        remove_directory("temp_app")
    except Exception as e:
        logging.warning(f"Error in installing updates..{e}")


if __name__ == "__main__":
    if auto_update == "yes":
        install_updates()
    run_codebase("run.py")
