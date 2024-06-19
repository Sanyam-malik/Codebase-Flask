import logging

from pydantic import BaseModel

import database_utility as database
from core import intellisense
from core.models import Sheet, SheetSection, SheetSectionItem, Playlist, PlaylistSection, PlaylistItem

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


class WebhookData(BaseModel):
    event: str
    payload: dict


def performAction(data):
    try:
        webhook_data = WebhookData(**data)
        if webhook_data.event == 'import-playlist':
            conn = database.create_connection()
            playlist = Playlist.from_json(webhook_data.payload)
            # Delete the playlist, and its related sections and items will be deleted due to cascading
            playlist_to_delete = conn.query(Playlist).filter(Playlist.uid == playlist.uid).first()
            if playlist_to_delete:
                conn.delete(playlist_to_delete)
                conn.commit()

            sections = webhook_data.payload['sections']
            conn.add(playlist)
            for section_json in sections:
                section = PlaylistSection.from_json(section_json)
                section.playlist_uid = playlist.uid
                conn.add(section)
                for item_json in section_json['items']:
                    item = PlaylistItem.from_json(item_json)
                    item.section_uid = section.uid
                    conn.add(item)
            conn.commit()
            conn.close()

        if webhook_data.event == 'import-sheet':
            conn = database.create_connection()
            sheet = Sheet.from_json(webhook_data.payload)

            # Delete the sheet, and its related sections and items will be deleted due to cascading
            sheet_to_delete = conn.query(Sheet).filter(Sheet.uid == sheet.uid).first()
            if sheet_to_delete:
                conn.delete(sheet_to_delete)
                conn.commit()

            sections = webhook_data.payload['sections']
            conn.add(sheet)
            for section_json in sections:
                section = SheetSection.from_json(section_json)
                section.sheet_uid = sheet.uid
                conn.add(section)
                for item_json in section_json['items']:
                    item = SheetSectionItem.from_json(item_json)
                    item.sheet_section_uid = section.uid
                    item.companies = ":".join(item.companies)
                    item.concepts = ":".join(item.concepts)
                    conn.add(item)
            conn.commit()
            intellisense.run_intellisense(conn)
            conn.close()

    except Exception as e:
        # Return an error response if the data doesn't match the expected format
        logging.info(f"Error parsing webhook data: {str(e)}")
