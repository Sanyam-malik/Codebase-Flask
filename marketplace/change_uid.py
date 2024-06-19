import shortuuid
import database_utility as database
from models import Playlist, Sheet  # Assuming your models are in models.py


def change_playlist(uid):
    # Create a session
    session = database.create_connection()
    try:
        # Query the playlist by the given uid
        playlist = session.query(Playlist).filter(Playlist.uid == uid).first()

        if playlist:
            # Generate a new uid for the playlist
            new_playlist_uid = shortuuid.uuid()

            # Iterate over the sections of the playlist and update their uids and playlist_uids
            for section in playlist.sections:
                new_section_uid = shortuuid.uuid()

                # Iterate over the items of the section and update their uids and section_uids
                for item in section.items:
                    new_item_uid = shortuuid.uuid()
                    item.uid = new_item_uid
                    item.section_uid = new_section_uid
                    session.commit()

                section.uid = new_section_uid
                section.playlist_uid = new_playlist_uid
                session.commit()

            playlist.uid = new_playlist_uid
            session.commit()
        else:
            print(f"Playlist with uid {uid} not found.")

    except Exception as e:
        # Rollback the transaction if any error occurs
        session.rollback()
        raise e
    finally:
        # Close the session
        session.close()


def change_sheet(uid):
    # Create a session
    session = database.create_connection()
    try:
        # Query the sheet by the given uid
        sheet = session.query(Sheet).filter(Sheet.uid == uid).first()

        if sheet:
            # Generate a new uid for the sheet
            new_sheet_uid = shortuuid.uuid()

            # Iterate over the sections of the sheet and update their uids and sheet_uids
            for section in sheet.sections:
                new_section_uid = shortuuid.uuid()

                # Iterate over the items of the section and update their uids and section_uids
                for item in section.items:
                    new_item_uid = shortuuid.uuid()
                    item.uid = new_item_uid
                    item.section_uid = new_section_uid
                    session.commit()

                section.uid = new_section_uid
                section.sheet_uid = new_sheet_uid
                session.commit()

            sheet.uid = new_sheet_uid
            session.commit()
        else:
            print(f"Sheet with uid {uid} not found.")

    except Exception as e:
        # Rollback the transaction if any error occurs
        session.rollback()
        raise e
    finally:
        # Close the session
        session.close()


if __name__ == "__main__":
    change_playlist('1')
