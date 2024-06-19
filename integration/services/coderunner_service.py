import os
import re
import subprocess
import tempfile
import logging
import json

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

programs = {
    "python": "python --version",
    "java": "java -version",
    "cpp": "g++ --version",
    "javascript": "node --version"
}


def check_installation():
    installation_status = {}

    for program, command in programs.items():
        try:
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                installation_status[program] = True
            else:
                installation_status[program] = False
        except FileNotFoundError:
            installation_status[program] = False

    return installation_status


def is_available(program):
    installations = check_installation()
    return installations.get(program, False)


def create_temp_file(extension, content):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
    temp_file.write(content.encode())
    temp_file.close()
    return temp_file.name


def delete_temp_file(file_path):
    try:
        os.remove(file_path)
    except OSError as e:
        logging.info(f"Error: {file_path} : {e.strerror}")


def replace_class_name_with_temp_file(code, temp_file_name, language):
    if language == "Java":
        # Remove package declaration
        code = re.sub(r'package\s+[\w.]+;\s*', '', code)

        # Extract class name
        class_name_match = re.search(r'public\s+class\s+(\w+)', code)
        if class_name_match:
            class_name = class_name_match.group(1)
            # Replace class name with temp file name throughout the code
            code = code.replace(class_name, os.path.splitext(os.path.basename(temp_file_name))[0])

            # Replace constructor names (assumes constructors are in the form ClassName)
            code = re.sub(r'(\bnew\s+){}(\s*\()'.format(class_name),
                          r'\1{}\2'.format(os.path.splitext(os.path.basename(temp_file_name))[0]), code)

    return code


def compile_and_run(program, code):
    installations = check_installation()

    response = {
        'output': None,
        'error': None
    }

    if installations.get(program, False):
        # Create a temporary file with the appropriate extension and content
        if program == "Python":
            temp_file = create_temp_file('.py', code)
            run_command = f'python {temp_file}'
        elif program == "Java":
            temp_file = create_temp_file('.java', code)
            code = replace_class_name_with_temp_file(code, temp_file, "Java")

            # Write the modified code back to the temporary file
            with open(temp_file, 'w') as f:
                f.write(code)

            compile_command = f'javac {temp_file}'
            run_command = f'java -cp {os.path.dirname(temp_file)} {os.path.splitext(os.path.basename(temp_file))[0]}'
        elif program == "C++":
            temp_file = create_temp_file('.cpp', code)
            executable_file = temp_file.replace('.cpp', '')
            compile_command = f'g++ {temp_file} -o {executable_file}'
            run_command = executable_file
        elif program == "JavaScript":
            temp_file = create_temp_file('.js', code)
            run_command = f'node {temp_file}'

        # Compile the code if needed (Java and C++)
        if program in ["Java", "C++"]:
            compile_result = subprocess.run(compile_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            response[
                'compile_output'] = compile_result.stdout.decode() if compile_result.stdout.decode().strip() else None
            response[
                'compile_error'] = compile_result.stderr.decode() if compile_result.stderr.decode().strip() else None

            if compile_result.returncode != 0:
                logging.info(f"Compilation failed: {compile_result.stderr.decode()}")
                delete_temp_file(temp_file)
                response['error'] = f"Compilation failed: {compile_result.stderr.decode()}"
                return json.dumps(response)

        # Run the code
        run_result = subprocess.run(run_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        response['output'] = run_result.stdout.decode() if run_result.stdout.decode().strip() else None
        response['error'] = run_result.stderr.decode() if run_result.stderr.decode().strip() else None

        if run_result.returncode != 0:
            logging.info(f"Execution failed: {run_result.stderr.decode()}")
            response['error'] = f"Execution failed: {run_result.stderr.decode()}"

        # Clean up temporary files
        delete_temp_file(temp_file)
        if program == "Java":
            delete_temp_file(temp_file.replace('.java', '.class'))
        elif program == "C++":
            delete_temp_file(executable_file)
    else:
        response['error'] = f"{program} is not installed."

    return response
