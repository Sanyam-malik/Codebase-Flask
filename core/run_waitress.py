import logging
import sys
from waitress import serve
import application_updator
from codebase import app, port

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

flask_log_handler = logging.StreamHandler(sys.stdout)
flask_log_handler.setLevel(logging.INFO)
flask_log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(flask_log_handler)


def run_server():
    application_updator.init_system()
    serve(app, host='0.0.0.0', port=port, threads=10)


if __name__ == '__main__':
    run_server()
