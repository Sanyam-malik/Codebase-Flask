import logging
import sys

from gunicorn.app.base import BaseApplication

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


class FlaskApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        application_updator.init_system()
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        return self.application


def run_server():
    options = {
        'bind': f'0.0.0.0:{port}',
        'workers': 10,  # Adjust the number of workers as needed
        'worker_class': 'sync',  # Use sync worker class for simplicity
        'loglevel': 'info',  # Set log level to info
        'accesslog': 'core.log',  # Path to access log file
        'errorlog': 'core.log',
    }

    FlaskApplication(app, options).run()


if __name__ == '__main__':
    run_server()
