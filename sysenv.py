import os

environ = {}


def set_environment():
    environ['AUTO_UPDATE'] = 'false'
    environ['DATABASE_NAME'] = 'codebase'
    environ['GIT_URL'] = 'http://lordmaximus.duckdns.org:85/data-structures/codebase.git'
    environ['DEST_PATH'] = 'codebase'
    environ['BRANCH_NAME'] = 'new-journey'
    environ['ACCESS_TOKEN'] = 'sammy:glpat-nXyy3Tz5JxDHrcovpLV7'
    environ['UPDATE_URL'] = 'http://lordmaximus.duckdns.org:85/data-structures/codebase-flask'
    environ['UPDATE_BRANCH'] = 'main'
    environ['UPDATE_ACCESS_TOKEN'] = 'sammy:glpat-nXyy3Tz5JxDHrcovpLV7'


if 'GIT_URL' not in os.environ:
    set_environment()
else:
    environ = os.environ