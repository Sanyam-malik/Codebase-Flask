import json
import logging
import os
import git_utility
import utility

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


def get_updated_application_metadata():
    try:
        git_utility.clone_repository(utility.update_url, utility.update_branch, "temp_app", utility.update_access_token)
        files = utility.get_files_in_folder("temp_app")
        if "app.json" in files:
            with open("temp_app/app.json", 'r') as file:
                data = json.load(file)
            return data
        utility.remove_directory("temp_app")
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
        files = utility.get_files_in_folder("temp_app")
        utility.create_folder("updates")
        for file in files:
            utility.copy_file("temp_app/" + file, "updates/" + file)
    except Exception as e:
        logging.warning(f"Error while preparing system for update..{e}")


def validate_json_from_file(file_path, val_type):
    optional_keys = []
    required_keys = []
    missing_required_keys = []
    missing_optional_keys = []
    depends = {}

    validation_object = utility.read_text_from_file("validate.json")
    json_data = utility.read_text_from_file(file_path)

    if json_data is None or validation_object is None:
        return {"error": "Cannot Validate Json File.."}, 400

    required_keys = validation_object[val_type]['required']
    optional_keys = validation_object[val_type]['optional']
    if "depends" in validation_object[val_type]:
        depends = validation_object[val_type]['depends']

    # Check for required keys
    missing_required_keys = [key for key in required_keys if key not in json_data or len(json_data[key]) == 0]

    # Check for optional keys
    missing_optional_keys = [key for key in optional_keys if key not in json_data]

    if len(depends) > 0:
        depends_keys = depends.keys()
        dept_required_keys = [key for key in required_keys if key in depends_keys]
        dept_optional_keys = [key for key in optional_keys if key in depends_keys]

        for key in dept_required_keys:
            parent = key
            dep_val_data = depends[key]
            dep_file_data = json_data[key]

            type = "object"
            req_keys = []
            opt_keys = []

            if "type" in dep_val_data:
                type = dep_val_data["type"]
            if "required" in dep_val_data:
                req_keys = dep_val_data["required"]
            if "optional" in dep_val_data:
                opt_keys = dep_val_data["optional"]

            if type == 'list':
                missing_req = []
                missing_opt = []

                for item in dep_file_data:
                    missing_req = missing_req + [parent + "->" + key for key in req_keys if
                                                 key not in item or len(item[key]) == 0]
                    missing_opt = missing_opt + [parent + "->" + key for key in opt_keys if key not in item]

                if len(missing_req) > 0:
                    missing_required_keys = missing_required_keys + list(set(missing_req))
                if len(missing_opt) > 0:
                    missing_optional_keys = missing_optional_keys + list(set(missing_opt))
            else:
                missing_req = [parent + "->" + key for key in req_keys if
                               key not in dep_file_data or len(dep_file_data[key]) == 0]
                missing_opt = [parent + "->" + key for key in opt_keys if key not in dep_file_data]
                if len(missing_req) > 0:
                    missing_required_keys = missing_required_keys + missing_req
                if len(missing_opt) > 0:
                    missing_optional_keys = missing_optional_keys + missing_opt

        for key in dept_optional_keys:
            parent = key
            dep_val_data = depends[key]
            dep_file_data = json_data[key]

            type = "object"
            req_keys = []
            opt_keys = []

            if "type" in dep_val_data:
                type = dep_val_data["type"]
            if "required" in dep_val_data:
                req_keys = dep_val_data["required"]
            if "optional" in dep_val_data:
                opt_keys = dep_val_data["optional"]

            if type == 'list':
                missing_req = []
                missing_opt = []
                for item in dep_file_data:
                    missing_req = missing_req + [parent + "->" + key for key in req_keys if
                                                 key not in item or len(item[key]) == 0]
                    missing_opt = missing_opt + [parent + "->" + key for key in opt_keys if key not in item]

                if len(missing_req) > 0:
                    missing_required_keys = missing_required_keys + list(set(missing_req))
                if len(missing_opt) > 0:
                    missing_optional_keys = missing_optional_keys + list(set(missing_opt))
            else:
                missing_req = [parent + "->" + key for key in req_keys if
                               key not in dep_file_data or len(dep_file_data[key]) == 0]
                missing_opt = [parent + "->" + key for key in opt_keys if key not in dep_file_data]

                if len(missing_req) > 0:
                    missing_required_keys = missing_required_keys + missing_req
                if len(missing_opt) > 0:
                    missing_optional_keys = missing_optional_keys + missing_opt

    if missing_required_keys:
        return {"error": f"Missing required keys: {', '.join(missing_required_keys)}"}, 400

    if missing_optional_keys:
        return {"warning": f"Missing optional keys: {', '.join(missing_optional_keys)}"}, 200

    return {"message": "All required keys are present in the JSON file"}, 200
