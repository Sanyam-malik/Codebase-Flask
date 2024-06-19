import logging

from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker

from config_manager import config_manager as appenv
import os

import utility
from models import Base, Quote, Playlist, PlaylistSection, PlaylistItem, MailLog, Reminder, ProblemType, Tracker, Note, \
    Setting, Remark, Company, Platform, Problem, SheetSection, SheetSectionItem, Sheet, NoteItem, Status, Level, \
    SheetSectionItemResponse

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

database = 'codebase.db'
if "DATABASE_NAME" in appenv.environ:
    database = appenv.environ["DATABASE_NAME"] + ".db"

# Create the SQLAlchemy engine
engine = create_engine(f'sqlite:///{database}')
Session = sessionmaker(bind=engine)
metadata = Base.metadata

table_objects = {
    "quotes": Quote,
    "problems": Problem,
    "platforms": Platform,
    "companies": Company,
    "remarks": Remark,
    "settings": Setting,
    "reminders": Reminder,
    "problem_type": ProblemType,
    "trackers": Tracker,
    "levels": Level,
    "statuses": Status,
    "maillog": MailLog,
    "notes": Note,
    "note_item": NoteItem,
    "playlist": Playlist,
    "playlist_section": PlaylistSection,
    "playlist_item": PlaylistItem,
    'sheet': Sheet,
    'sheet_section': SheetSection,
    'sheet_section_item': SheetSectionItem,
    'sheet_section_item_response': SheetSectionItemResponse
}


def re_init():
    global database
    appenv.set_environment()

    if "DATABASE_NAME" in appenv.environ:
        database = appenv.environ["DATABASE_NAME"] + ".db"


# Function to initialize the database and tables
def init_database():
    global Session, engine, metadata
    if os.path.exists("codebase.lock"):
        # Create the SQLAlchemy engine again
        engine = create_engine(f'sqlite:///{database}')
        event.listen(engine, 'connect', register_custom_functions)
        Session = sessionmaker(bind=engine)
        metadata = Base.metadata

    # Create a session
    session = Session()

    # Create tables
    metadata.create_all(engine)

    # Retrieve backup data
    retrieve_backup(session)

    # Return the session
    return session


def retrieve_backup(session):
    backup_db = f"backup_{database}"
    if os.path.exists(backup_db):
        logging.info("Migration Started....")
        try:
            with session.begin():
                backup_engine = create_engine(f'sqlite:///{backup_db}')
                BackupSession = sessionmaker(bind=backup_engine)
                backup_session = BackupSession()

                # Importing the quotes table entries
                quotes_backup = backup_session.query(Quote).all()
                for quote in quotes_backup:
                    session.merge(quote)

                # Importing the maillogs table entries
                maillogs_backup = backup_session.query(MailLog).all()
                for maillog in maillogs_backup:
                    session.merge(maillog)

                # Importing the playlists table entries
                playlists_backup = backup_session.query(Playlist).all()
                for playlist in playlists_backup:
                    session.merge(playlist)

                # Importing the playlist_sections table entries
                playlist_sections_backup = backup_session.query(PlaylistSection).all()
                for section in playlist_sections_backup:
                    session.merge(section)

                # Importing the playlist_items table entries
                playlist_items_backup = backup_session.query(PlaylistItem).all()
                for item in playlist_items_backup:
                    session.merge(item)

                # Importing the sheet table entries
                sheets_backup = backup_session.query(Sheet).all()
                for sheet in sheets_backup:
                    session.merge(sheet)

                # Importing the sheet_sections table entries
                sheet_sections_backup = backup_session.query(SheetSection).all()
                for section in sheet_sections_backup:
                    session.merge(section)

                # Importing the sheet_section_items table entries
                sheet_section_items_backup = backup_session.query(SheetSectionItem).all()
                for item in sheet_section_items_backup:
                    session.merge(item)

                logging.info("Migration Completed Successfully!")
        except Exception as e:
            logging.error(f"Error occurred during migration: {str(e)}")
            session.rollback()
        finally:
            if backup_session:
                backup_session.close()
    else:
        logging.error("Backup database not found!")


def create_slug(text):
    if text is None:
        return None
    return utility.create_slug(text)


# Register the custom function with SQLite through SQLAlchemy
def register_custom_functions(connection, connection_record):
    connection.create_function('create_slug', 1, create_slug)


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
    if os.path.exists("codebase.lock") and os.path.exists(backup_db):
        backup_engine = create_engine(f'sqlite:///{backup_db}')
        event.listen(backup_engine, 'connect', register_custom_functions)
        BackupSession = sessionmaker(bind=backup_engine)
        metadata = Base.metadata
        return BackupSession()
    else:
        # Create the SQLAlchemy engine again
        engine = create_engine(f'sqlite:///{database}')
        event.listen(engine, 'connect', register_custom_functions)
        Session = sessionmaker(bind=engine)
        metadata = Base.metadata
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
