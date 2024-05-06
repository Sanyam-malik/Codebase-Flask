import logging
import ssl

import application_updator
from waitress import serve
from codebase import app, port

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

if __name__ == '__main__':
    application_updator.init_system()
    serve(app, host="0.0.0.0", port=port, url_scheme='https')