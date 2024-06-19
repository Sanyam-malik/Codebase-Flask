import logging

import shortuuid
from sqlalchemy import or_

import database_utility
from models import Problem, SheetSectionItem, Sheet, Playlist

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


def run_intellisense(connector):
    logging.info("Running Intellisense...........")
    problems = connector.query(Problem).filter(Problem.include_count == True).all()
    values_list = []
    status_change_list = []
    for problem in problems:
        name = problem.name
        url = problem.url
        sheet_items = connector.query(SheetSectionItem).filter(
            or_(SheetSectionItem.name == name, SheetSectionItem.url.like(f"%{url}%"))
        ).all()
        for item in sheet_items:
            values = (
                shortuuid.uuid(),
                item.uid,
                problem.uid
            )

            # For Explicit Status Assignment
            if problem.sheet_item_status is not None:
                status_change_list.append({
                    'id': item.uid,
                    'status': problem.sheet_item_status
                })
            else:
                status_precompute = str(problem.status).lower()
                status = 'TODO'
                if "pending" in status_precompute or "to be done" in status_precompute or "working on it" in status_precompute:
                    status = 'INPROGRESS'
                elif "complete" in status_precompute or "done" in status_precompute:
                    status = 'COMPLETED'

                status_change_list.append({
                    'id': item.uid,
                    'status': status
                })
            values_list.append(values)

    if len(values_list) > 0:
        logging.info(f"{len(values_list)} Problems Found...........")
        save_intellisense_response(connector, values_list)
        update_relevant_status(connector, status_change_list)
        run_sheet_update(connector)


def save_intellisense_response(connector, values_list):
    logging.info(f"Saving Intellisense Responses...........")
    # Insert if Problems Similarity is Detected
    for value in values_list:
        database_utility.insert_data(connector, 'sheet_section_item_response', value)


def update_relevant_status(connector, status_list):
    logging.info(f"Updating Item Statuses...........")
    # Iterate and change the sheet item status for each problem that has been detected
    for status in status_list:
        sheet_uid = status['id']
        sheet_status = status['status']
        sheet_item = connector.query(SheetSectionItem).filter(SheetSectionItem.uid == sheet_uid).first()
        if sheet_item:
            sheet_item.status = sheet_status
            connector.commit()


def run_sheet_update(connector, uid=None):
    # Check if items are completed for sheets
    logging.info(f"Running Sheet Completion Update...........")
    if uid is not None:
        sheets = connector.query(Sheet).filter(Sheet.uid == uid).all()
    else:
        sheets = connector.query(Sheet).all()

    for sheet in sheets:
        completion_count = 0
        for section in sheet.sections:
            completed_in_section = 0
            for item in section.items:
                if item.status == 'COMPLETED':
                    completion_count += 1
                    completed_in_section += 1

            if completed_in_section > 0 and completed_in_section == len(section.items):
                section.status = 'COMPLETED'
                connector.commit()
            elif completed_in_section > 0 and completed_in_section < len(section.items):
                section.status = 'INPROGRESS'
                connector.commit()

        sheet.completed_items_count = completion_count
        connector.commit()


def run_playlist_update(connector, uid=None):
    # Check if items are completed for playlists
    logging.info(f"Running Playlist Completion Update...........")
    if uid is not None:
        playlists = connector.query(Playlist).filter(Playlist.uid == uid).all()
    else:
        playlists = connector.query(Playlist).all()

    for playlist in playlists:
        completion_count = 0
        for section in playlist.sections:
            completed_in_section = 0
            for item in section.items:
                if item.status == 'COMPLETED':
                    completion_count += 1
                    completed_in_section += 1

            if completed_in_section > 0 and completed_in_section == len(section.items):
                section.status = 'COMPLETED'
                connector.commit()
            elif completed_in_section > 0 and completed_in_section < len(section.items):
                section.status = 'INPROGRESS'
                connector.commit()

        playlist.completed_items_count = completion_count
        connector.commit()
        
        
def reset_playlist_progress(connector, uid=None):
    # Check if items are completed for playlists
    logging.info(f"Resetting Playlists Progress...........")
    if uid is not None:
        playlists = connector.query(Playlist).filter(Playlist.uid == uid).all()
    else:
        playlists = connector.query(Playlist).all()
        
    for playlist in playlists:
        for section in playlist.sections:
            for item in section.items:
                item.status = 'TODO'
            section.status = 'TODO'
        playlist.completed_items_count = 0
    connector.commit()


def reset_sheet_progress(connector, uid=None):
    # Check if items are completed for sheets
    logging.info(f"Resetting Sheets Progress...........")
    if uid is not None:
        sheets = connector.query(Sheet).filter(Sheet.uid == uid).all()
    else:
        sheets = connector.query(Sheet).all()

    for sheet in sheets:
        for section in sheet.sections:
            for item in section.items:
                item.status = 'TODO'
            section.status = 'TODO'
        sheet.completed_items_count = 0
    connector.commit()

