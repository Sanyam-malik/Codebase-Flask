import logging

from sqlalchemy import create_engine, text, event, inspect
from sqlalchemy.orm import sessionmaker

import os
from models import Base, Chats, VideoSolutions

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

database = 'integration.db'

# Create the SQLAlchemy engine
engine = create_engine(f'sqlite:///{database}')
Session = sessionmaker(bind=engine)
metadata = Base.metadata

table_objects = {
    "chats": Chats,
    "video_solutions": VideoSolutions
}


# Function to initialize the database and tables
def init_database():
    global Session, engine, metadata
    if os.path.exists("integration.lock"):
        # Create the SQLAlchemy engine again
        engine = create_engine(f'sqlite:///{database}')
        Session = sessionmaker(bind=engine)
        metadata = Base.metadata

    # Create a session
    session = Session()

    # Check if tables exist
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Check if tables exist in metadata
    if not set(Base.metadata.tables.keys()).issubset(existing_tables):
        # Create tables
        Base.metadata.create_all(engine)

    # Return the session
    return session


# Function to remove the main database
def remove_database():
    backup_database = f"backup_{database}"
    try:
        if os.path.exists(database):
            if os.path.exists(backup_database):
                os.remove(backup_database)
            os.rename(database, backup_database)
            logging.info(f"Database Backup '{database}' created successfully.")
        else:
            logging.info(f"Database file '{database}' not found.")
    except Exception as e:
        logging.warning(f"Error deleting database file '{database}': {e}")


def fetch_all_columns(table_name, include_primary_key=True):
    table = Base.metadata.tables[table_name]

    if include_primary_key:
        return [column.name for column in table.columns]
    else:
        primary_key_name = table.primary_key.columns.keys()[0]
        return [column.name for column in table.columns if column.name != primary_key_name]


# Function to create a connection to the SQLite database
def create_connection():
    backup_db = f"readonly_{database}"
    if os.path.exists("integration.lock") and os.path.exists(backup_db):
        backup_engine = create_engine(f'sqlite:///{backup_db}')
        BackupSession = sessionmaker(bind=backup_engine)
        return BackupSession()
    else:
        init_database()
        return Session()


def insert_data(session, table_name, data, include_primary=False):
    columns = fetch_all_columns(table_name, include_primary)
    table = table_objects[table_name]
    data_dict = {col: value for col, value in zip(columns, data)}
    model_instance = table(**data_dict)
    session.add(model_instance)
    session.commit()
    return model_instance.id


# Function to execute a custom SQL query
def execute_query(connection, query):
    connection.execute(text(query))
    connection.commit()


# Function to fetch data from the SQLite database
def fetch_data(connection, query):
    result = connection.execute(text(query))
    return result.fetchall()


# Function to close the SQLite database connection
def close_connection(connection):
    connection.close()
