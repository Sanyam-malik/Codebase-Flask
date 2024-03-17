import os

environ = {}


def set_environment():
    environ['AUTO_UPDATE'] = 'false'
    environ['DATABASE_NAME'] = 'codebase'
    environ['GIT_URL'] = 'https://github.com/Sanyam-malik/Codebase'
    environ['DEST_PATH'] = 'codebase'
    environ['BRANCH_NAME'] = 'new-journey'
    environ['ACCESS_TOKEN'] = ''
    environ['UPDATE_URL'] = 'https://github.com/Sanyam-malik/Codebase-Flask'
    environ['UPDATE_BRANCH'] = 'main'
    environ['UPDATE_ACCESS_TOKEN'] = ''
    environ['SMTP_ENABLE'] = 'false'
    environ['SMTP_ADDRESS'] = ''
    environ['SMTP_PORT'] = ''
    environ['SMTP_USERNAME'] = ''
    environ['SMTP_PASSWORD'] = ''


if 'GIT_URL' not in os.environ:
    set_environment()
else:
    environ = os.environ