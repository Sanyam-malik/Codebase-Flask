import platform
import subprocess
import os
import sys

# Get the current working directory
cwd = os.path.dirname(os.path.abspath(__file__))

# Get the current Python executable
python_executable = sys.executable

if platform.system() == 'Windows':
    subprocess.run([python_executable, os.path.join(cwd, "run_waitress.py")])
else:
    subprocess.run([python_executable, os.path.join(cwd, "run_gunicorn.py")])
