import logging
import sqlite3
import sysenv
import os

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

database = 'codebase.db'
if "DATABASE_NAME" in sysenv.environ:
    database = sysenv.environ["DATABASE_NAME"] + ".db"

problems_table = '''
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NULL,
            typeid INTEGER NOT NULL,
            url TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT NULL,
            date_added TIMESTAMP NULL,
            level TEXT NULL,
            filename TEXT NULL,
            companies TEXT NULL,
            remarks TEXT NULL
        )
    '''

platforms_table = '''
        CREATE TABLE IF NOT EXISTS platforms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            icon TEXT NOT NULL
        );
    '''

companies_table = '''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );
'''

remarks_table = '''
        CREATE TABLE IF NOT EXISTS remarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL
        );
'''

settings_table = '''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            value TEXT NOT NULL
        );
'''

reminders_table = '''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            recurrence TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            date TEXT
        );
    '''

problems_type_table = '''
        CREATE TABLE IF NOT EXISTS problem_type (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NULL
        )
'''

trackers_table = '''
        CREATE TABLE IF NOT EXISTS trackers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level TEXT NOT NULL
        );
'''

maillog_table = '''
        CREATE TABLE IF NOT EXISTS maillog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            recipient TEXT NOT NULL,
            date TEXT
        );
'''


def init_database():
    connector = create_connection()
    create_table(connector, problems_type_table)
    create_table(connector, problems_table)
    create_table(connector, reminders_table)
    create_table(connector, platforms_table)
    create_table(connector, trackers_table)
    create_table(connector, companies_table)
    create_table(connector, remarks_table)
    create_table(connector, settings_table)
    create_table(connector, maillog_table)
    retrieve_backup()
    return connector


def retrieve_backup():
    backup_db = "backup_" + database
    conn = create_connection()
    if os.path.exists(backup_db):
        logging.info("Migration Started....")
        # Importing the maillog table entries
        backup_conn = create_connection(backup_db)
        result = fetch_data(backup_conn, "SELECT subject, body, recipient, date from maillog")
        if len(result) > 0:
            logging.info('Migrating the maillogs....')
            for item in result:
                insert_data(conn, "maillog", item)


def remove_database():
    try:
        # Check if the file exists before attempting to delete
        if os.path.exists(database):
            if os.path.exists("backup_" + database):
                os.remove("backup_" + database)
            os.rename(database, "backup_" + database)
            logging.info(f"Database Backup '{database}' created successfully.")
        else:
            logging.info(f"Database file '{database}' not found.")
    except Exception as e:
        logging.warning(f"Error deleting database file '{database}': {e}")


def create_connection(db=None):
    """Create a connection to the SQLite database."""
    if db is not None:
        connector = sqlite3.connect(db)
    else:
        connector = sqlite3.connect(database)
    return connector


def create_table(connection, table_query):
    """Create a table in the SQLite database."""
    cursor = connection.cursor()
    cursor.execute(table_query)
    connection.commit()


def fetch_column_names(connection, table_name):
    cursor = connection.cursor()

    # Query to fetch column names from the specified table
    query = f"PRAGMA table_info({table_name})"
    cursor.execute(query)

    # Fetch all rows from the result set
    columns = cursor.fetchall()

    # Extract column names from the result set
    column_names = [column[1] for column in columns]
    column_names = column_names[1:]
    return column_names


def insert_data(connection, table_name, data):
    columns = fetch_column_names(connection, table_name)
    # Convert the list of column names to a comma-separated string
    columns_str = ', '.join(columns)
    """Insert data into the specified table."""
    cursor = connection.cursor()
    placeholders = ', '.join(['?'] * len(data))
    insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    cursor.execute(insert_query, data)
    last_inserted_id = cursor.lastrowid
    connection.commit()
    return last_inserted_id


def execute_query(connection, query):
    """Execute a custom SQL query."""
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()


def fetch_data(connection, query):
    """Fetch data from the SQLite database."""
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    return result


def close_connection(connection):
    """Close the SQLite database connection."""
    connection.close()
