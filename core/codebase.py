import json
import os
import random
import shutil
import tempfile
import time
from datetime import datetime, timedelta
import re

import redis
from flask_caching import Cache
from sqlalchemy import func, and_, desc
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import analytics
from config_manager import config_manager as appenv
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import logging
import database_utility as database
import application_updator as updator
import utility
from core import intellisense
from core.webhook import performAction
from models import Quote, Problem, ProblemType, Note, Platform, Tracker, Company, Remark, Setting, Reminder, Playlist, \
    PlaylistItem, Sheet, SheetSectionItem, Level, Status

app = Flask(__name__)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
CORS(app)  # Enable CORS for all routes

# Set up Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Set up Flask-Limiter with Redis
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    app=app
)

# Define rate limit rules
rate_limit_rule = "10 per second"
dos_detection_rule = "100 per second"  # Threshold for DoS attack detection

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

port = 5050
baseport = 5000
if "PORT" in appenv.environ:
    baseport = int(appenv.environ["PORT"])
    port = int(appenv.environ["PORT"]) + 50


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def home(path):
    current_folder = os.path.dirname(__file__)
    static_folder = os.path.join(current_folder, 'core-ui')

    if os.path.exists(static_folder):
        if path != "" and os.path.exists(os.path.join(static_folder, path)):
            return send_from_directory(static_folder, path)
        else:
            return send_from_directory(static_folder, "index.html")
    else:
        return "Codebase-Flask is Active"


@app.route('/file/<path:file_path>')
@limiter.limit(rate_limit_rule)
def serve_file(file_path):
    file_path = file_path.replace("<repo_path>", utility.get_running_repo(updator.dest_path))
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path)
    else:
        return "File not found", 404


@app.route('/code/<path:file_path>')
@limiter.limit(rate_limit_rule)
def serve_code(file_path):
    file_path = file_path.replace("<repo_path>", utility.get_running_repo(updator.dest_path))
    code = ''
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
        code = re.sub(r'<metadata>.*?</metadata>',
                      file_path.replace(utility.get_running_repo(updator.dest_path), "File: ").replace('\\', '/'),
                      code,
                      flags=re.DOTALL)
        f.close()
    return jsonify({'content': code})


@cache.cached(timeout=120)
@app.route('/api/quote', methods=['GET'])
@limiter.limit(rate_limit_rule)
def random_quote():
    conn = database.create_connection()
    max_id = conn.query(func.max(Quote.id)).scalar()
    # Generate a random ID within the range of available IDs
    random_id = random.randint(1, max_id)
    # Query the quote with the random ID
    rquote = conn.query(Quote).filter(Quote.id == random_id).first()
    return jsonify(rquote.__response_json__()), 200


@cache.cached(timeout=120)
@app.route('/api/songs', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_songs():
    songs = updator.get_songs()
    if songs is not None:
        return jsonify({'songs': songs})
    else:
        return jsonify({'songs': []})


@cache.cached(timeout=120)
@app.route('/api/problems', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_problems():
    conn = database.create_connection()
    problems = []
    conditions = []

    # Extract query parameters
    type_filter = request.args.get('type')
    status_filter = request.args.get('status')
    level_filter = request.args.get('level')
    remark_filter = request.args.get('remark')
    company_filter = request.args.get('company')
    res = request.args.get('res')

    # Add conditions based on query parameters
    if type_filter:
        conditions.append(func.create_slug(ProblemType.name) == type_filter)
    if level_filter:
        conditions.append(func.create_slug(Problem.level) == level_filter)
    if status_filter:
        conditions.append(func.create_slug(Problem.status) == status_filter)
    if remark_filter:
        conditions.append(func.create_slug(Problem.remarks).like(f'%{remark_filter}%'))
    if company_filter:
        conditions.append(func.create_slug(Problem.companies).like(f'%{company_filter}%'))

    # Apply conditions to the query

    if res is not None and res == 'detail':
        base_query = conn.query(Problem).join(ProblemType, Problem.typeid == ProblemType.id)
        if conditions:
            base_query = base_query.filter(and_(*conditions))
        # Execute the query and fetch the results
        results = [problem.__response_json__() for problem in base_query.all()]
        for item in results:
            companies = item['companies']
            if companies is not None:
                companies = str(companies).replace(":", ",")
                temp = []
                for company_str in companies.split(","):
                    q = conn.query(Company).filter(
                        Company.name == company_str)
                    # Assuming you're using SQLAlchemy, you can execute the query to get the results
                    company_result = q.first()  # Retrieves the first result
                    if company_result:
                        temp.append(company_result.__response_json__())
                companies = temp
            else:
                companies = []
            item['companies'] = companies
            problems.append(item)
    else:
        base_query = conn.query(Problem.uid, Problem.name, ProblemType.name, Problem.level, Problem.status,
                                Problem.remarks,
                                Problem.companies, Problem.subdirectory).join(ProblemType,
                                                                              Problem.typeid == ProblemType.id)
        if conditions:
            base_query = base_query.filter(and_(*conditions))

        results = base_query.all()
        for item in results:
            uid, name, type, level, status, remarks, companies_str, subdirectory = item
            companies = []
            if companies_str is not None:
                companies_str = str(companies_str).replace(":", ",")
                temp = []
                for company_str in companies_str.split(","):
                    q = conn.query(Company).filter(
                        Company.name == company_str)
                    # Assuming you're using SQLAlchemy, you can execute the query to get the results
                    company_result = q.first()  # Retrieves the first result
                    if company_result:
                        temp.append(company_result.__response_json__())
                companies = temp
            problems.append({
                'id': uid,
                'name': name,
                'type': {
                    'name': type,
                    'slug': utility.create_slug(type)
                },
                'remarks': remarks,
                'subdirectory': subdirectory,
                'slug': utility.create_slug(name),
                'level': level,
                'status': status,
                'companies': companies
            })

    database.close_connection(conn)
    return jsonify({'problems': problems})


@cache.cached(timeout=120)
@app.route('/api/problems/<string:id>', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_problem_by_id(id):
    conn = database.create_connection()
    problem = conn.query(Problem).filter(func.create_slug(Problem.name) == id).first()
    if problem:
        problem = problem.__response_json__()
        companies = problem['companies']
        if companies is not None:
            companies = str(companies).replace(":", ",")
            temp = []
            for company_str in companies.split(","):
                q = conn.query(Company).filter(
                    Company.name == company_str)
                # Assuming you're using SQLAlchemy, you can execute the query to get the results
                company_result = q.first()  # Retrieves the first result
                if company_result:
                    temp.append(company_result.__response_json__())
            companies = temp
        else:
            companies = []
        problem['companies'] = companies
        database.close_connection(conn)
        return jsonify({'problem': problem})
    else:
        # If the problem is not found, return a 404 error
        database.close_connection(conn)
        return jsonify({'error': 'Problem not found'}), 404


@cache.cached(timeout=120)
@app.route('/api/notes', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_notes():
    notes = []
    type = request.args.get('type')
    conn = database.create_connection()
    if type is not None and type == "detail":
        notes_query = conn.query(Note).order_by(Note.title).all()
        notes = [note.__response_json__() for note in notes_query]
    else:
        notes_query = conn.query(Note.uid, Note.title).order_by(Note.title).all()
        notes = [{'id': note[0], 'title': note[1]} for note in notes_query]
    database.close_connection(conn)
    return jsonify({'notes': notes})


@cache.cached(timeout=120)
@app.route('/api/note/<string:id>', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_note_by_id(id):
    conn = database.create_connection()
    note_query = conn.query(Note).filter(Note.uid == id).first()
    if note_query:
        note = note_query.__response_json__()
        database.close_connection(conn)
        return jsonify({'note': note})
    else:
        return jsonify({'error': 'Note not found'}), 404


@app.route('/api/note/operations', methods=['POST'])
@limiter.limit(rate_limit_rule)
def operation_on_note():
    conn = database.create_connection()
    type = request.args.get('type')
    note = json.loads(request.args.get('note'))
    any_operation = False
    try:
        if 'delete' == type:
            delete_query = conn.query(Note).filter(Note.uid == note['id']).first()
            folder_path = f"{updator.dest_path}/notes/{delete_query.title}"
            if delete_query:
                conn.delete(delete_query)
                any_operation = True

            else:
                return jsonify({'error': 'Note not found'}), 404
        else:
            return jsonify({'error': 'Invalid Type'}), 400

        if any_operation:
            utility.delete_folder(folder_path)
            updator.commit_and_push(folder_path)
            conn.commit()
            cache.clear()
        return jsonify({'message': 'success'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@cache.cached(timeout=120)
@app.route('/api/problem/types', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_problem_types():
    conn = database.create_connection()
    query_result = conn.query(ProblemType).order_by(ProblemType.name).all()
    problem_types = [problem.__response_json__(False) for problem in query_result]
    database.close_connection(conn)
    return jsonify({'types': problem_types})


@cache.cached(timeout=120)
@app.route('/api/problem/levels', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_problem_levels():
    conn = database.create_connection()
    query_result = conn.query(Level).all()
    problem_levels = [problem.__response_json__() for problem in query_result]
    database.close_connection(conn)
    return jsonify({'levels': problem_levels})


@cache.cached(timeout=120)
@app.route('/api/problem/statuses', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_problem_statuses():
    conn = database.create_connection()
    query_result = conn.query(Status).all()
    problem_statuses = [problem.__response_json__() for problem in query_result]

    database.close_connection(conn)
    return jsonify({'statuses': problem_statuses})


@cache.cached(timeout=120)
@app.route('/api/platforms', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_platforms():
    conn = database.create_connection()
    platforms_query = conn.query(Platform).all()
    platforms = [platform.__response_json__() for platform in platforms_query]
    database.close_connection(conn)
    return jsonify({'platforms': platforms})


@app.route('/api/platform/operations', methods=['POST'])
@limiter.limit(rate_limit_rule)
def operation_on_platform():
    conn = database.create_connection()
    type = request.args.get('type')
    platform = json.loads(request.args.get('platform'))
    file_path = f"{updator.dest_path}/platforms.json"
    any_performed = False
    try:
        if 'delete' == type:
            delete_query = conn.query(Platform).filter(Platform.uid == platform['id']).first()
            if delete_query:
                conn.delete(delete_query)
                any_performed = True
            else:
                return jsonify({'error': 'Platform not found'}), 404
        elif 'update' == type:
            update_query = conn.query(Platform).filter(Platform.uid == platform['id']).first()
            if update_query:
                update_query.name = platform['name']
                update_query.url = platform['url']
                update_query.icon = platform['icon']
                any_performed = True
            else:
                return jsonify({'error': 'Platform not found'}), 404
        else:
            return jsonify({'error': 'Invalid type'}), 400

        if any_performed:
            data = [platform.__data_store__() for platform in conn.query(Platform).all()]
            updator.save_json_file(data, file_path)
            updator.commit_and_push(file_path)

            conn.commit()
            cache.clear()
        return jsonify({'message': 'success'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@cache.cached(timeout=120)
@app.route('/api/trackers', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_trackers():
    conn = database.create_connection()
    trackers_query = conn.query(Tracker).all()
    trackers = [tracker.__response_json__() for tracker in trackers_query]
    database.close_connection(conn)
    return jsonify({'trackers': trackers})


@app.route('/api/tracker/operations', methods=['POST'])
@limiter.limit(rate_limit_rule)
def operation_on_tracker():
    conn = database.create_connection()
    type = request.args.get('type')
    tracker = json.loads(request.args.get('tracker'))
    file_path = f"{updator.dest_path}/trackers.json"
    any_performed = False

    try:
        if 'delete' == type:
            delete_query = conn.query(Tracker).filter(Tracker.uid == tracker['id']).first()
            if delete_query:
                conn.delete(delete_query)
                any_performed = True
            else:
                return jsonify({'error': 'Tracker not found'}), 404
        elif 'update' == type:
            update_query = conn.query(Tracker).filter(Tracker.uid == tracker['id']).first()
            if update_query:
                update_query.name = tracker['name']
                update_query.level = tracker['level']
                any_performed = True
                # Add any other fields that need to be updated here
            else:
                return jsonify({'error': 'Tracker not found'}), 404
        else:
            return jsonify({'error': 'Invalid type'}), 400

        if any_performed:
            data = [tracker.__data_store__() for tracker in conn.query(Tracker).all()]
            updator.save_json_file(data, file_path)
            updator.commit_and_push(file_path)

            conn.commit()
            cache.clear()
        return jsonify({'message': 'success'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@cache.cached(timeout=120)
@app.route('/api/companies', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_companies():
    conn = database.create_connection()
    companies_query = conn.query(Company).all()
    companies = [companies.__response_json__() for companies in companies_query]
    database.close_connection(conn)
    return jsonify({'companies': companies})


@cache.cached(timeout=120)
@app.route('/api/remarks', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_remarks():
    conn = database.create_connection()
    remarks_query = conn.query(Remark).all()
    remarks = [remarks.__response_json__() for remarks in remarks_query]
    database.close_connection(conn)
    return jsonify({'remarks': remarks})


@cache.cached(timeout=120)
@app.route('/api/playlists', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_playlists():
    playlists = []
    res = request.args.get('res')
    conn = database.create_connection()
    if res is not None and res == 'detail':
        playlist_query = conn.query(Playlist).all()
        playlists = [playlist.__response_json__() for playlist in playlist_query]
    else:
        playlist_query = conn.query(Playlist.uid, Playlist.title).all()
        playlists = [{'id': playlist[0], 'title': playlist[1]} for playlist in playlist_query]
    database.close_connection(conn)
    return jsonify({'playlists': playlists})


@cache.cached(timeout=120)
@app.route('/api/playlist/<string:id>', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_playlist_by_id(id):
    conn = database.create_connection()
    playlist_query = conn.query(Playlist).filter(Playlist.uid == id).first()
    if playlist_query:
        playlist = playlist_query.__response_json__()
        database.close_connection(conn)
        return jsonify({'playlist': playlist})
    else:
        return jsonify({'error': 'Playlist not found'}), 404


@app.route('/api/playlist/operations', methods=['POST'])
@limiter.limit(rate_limit_rule)
def operation_on_playlist():
    conn = database.create_connection()
    type = request.args.get('type')
    playlist_uid = request.args.get('playlist')

    try:
        if 'delete' == type:
            # Delete the playlist, and its related sections and items will be deleted due to cascading
            playlist_to_delete = conn.query(Playlist).filter(Playlist.uid == playlist_uid).first()
            if playlist_to_delete:
                conn.delete(playlist_to_delete)
            else:
                conn.close()
                return jsonify({'error': 'Playlist not found'}), 404

        elif 'status-complete' == type:
            playlist_to_update = conn.query(Playlist).filter(Playlist.uid == playlist_uid).first()
            if playlist_to_update:
                for section in playlist_to_update.sections:
                    section.status = 'COMPLETED'
                    for item in section.items:
                        item.status = 'COMPLETED'
            else:
                conn.close()
                return jsonify({'error': 'Playlist not found'}), 404

        elif 'status-todo' == type:
            playlist_to_update = conn.query(Playlist).filter(Playlist.uid == playlist_uid).first()
            if playlist_to_update:
                intellisense.reset_playlist_progress(conn, playlist_uid)
            else:
                conn.close()
                return jsonify({'error': 'Playlist not found'}), 404

        else:
            conn.close()
            return jsonify({'error': 'Invalid type'}), 400

        conn.commit()
        intellisense.run_playlist_update(conn)
        cache.clear()
        return jsonify({'message': 'success'})

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        conn.close()


@app.route('/api/playlist/item/status', methods=['POST'])
@limiter.limit(rate_limit_rule)
def update_playlist_item_status():
    conn = database.create_connection()
    item_id = request.args.get('item')
    item_status = request.args.get('status', 'INPROGRESS')
    item = conn.query(PlaylistItem).filter_by(uid=item_id).first()
    if item is not None:
        item.status = item_status
        # Commit the changes to the database
        conn.commit()
        intellisense.run_playlist_update(conn)
    else:
        conn.close()
        return jsonify({'message': 'not-found'}), 404
    conn.close()
    cache.clear()
    return jsonify({'message': 'success'})


@cache.cached(timeout=120)
@app.route('/api/sheets', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_sheets():
    sheets = []
    res = request.args.get('res')
    conn = database.create_connection()

    if res is not None and res == 'detail':
        sheet_query = conn.query(Sheet).all()
        sheets = [sheet.__response_json__() for sheet in sheet_query]
    else:
        sheet_query = conn.query(Sheet.uid, Sheet.name).all()
        sheets = [{'id': sheet[0], 'title': sheet[1]} for sheet in sheet_query]
    database.close_connection(conn)
    return jsonify({'sheets': sheets})


@cache.cached(timeout=120)
@app.route('/api/sheet/<string:id>', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_sheet_by_id(id):
    conn = database.create_connection()
    sheet_query = conn.query(Sheet).filter(Sheet.uid == id).first()
    if sheet_query:
        sheet = sheet_query.__response_json__()
        database.close_connection(conn)
        return jsonify({'sheet': sheet})
    else:
        return jsonify({'error': 'Sheet not found'}), 404


@app.route('/api/sheet/operations', methods=['POST'])
@limiter.limit(rate_limit_rule)
def operation_on_sheet():
    conn = database.create_connection()
    type = request.args.get('type')
    sheet_uid = request.args.get('sheet')

    try:
        if 'delete' == type:
            # Delete the sheet, and its related sections and items will be deleted due to cascading
            sheet_to_delete = conn.query(Sheet).filter(Sheet.uid == sheet_uid).first()
            if sheet_to_delete:
                conn.delete(sheet_to_delete)
            else:
                conn.close()
                return jsonify({'error': 'Sheet not found'}), 404

        elif 'status-complete' == type:
            sheet_to_update = conn.query(Sheet).filter(Sheet.uid == sheet_uid).first()
            if sheet_to_update:
                for section in sheet_to_update.sections:
                    section.status = 'COMPLETED'
                    for item in section.items:
                        item.status = 'COMPLETED'
            else:
                conn.close()
                return jsonify({'error': 'Sheet not found'}), 404

        elif 'status-todo' == type:
            sheet_to_update = conn.query(Sheet).filter(Sheet.uid == sheet_uid).first()
            if sheet_to_update:
                intellisense.reset_sheet_progress(conn, sheet_uid)
            else:
                conn.close()
                return jsonify({'error': 'Sheet not found'}), 404

        else:
            conn.close()
            return jsonify({'error': 'Invalid type'}), 400

        conn.commit()
        intellisense.run_sheet_update(conn)
        cache.clear()
        return jsonify({'message': 'success'})

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        conn.close()


@app.route('/api/sheet/item/status', methods=['POST'])
@limiter.limit(rate_limit_rule)
def update_sheet_item_status():
    conn = database.create_connection()
    item_id = request.args.get('item')
    item_status = request.args.get('status', 'INPROGRESS')
    item = conn.query(SheetSectionItem).filter_by(uid=item_id).first()
    if item is not None:
        item.status = item_status
        # Commit the changes to the database
        conn.commit()
        intellisense.run_sheet_update(conn)

    else:
        conn.close()
        return jsonify({'message': 'not-found'}), 404
    conn.close()
    cache.clear()
    return jsonify({'message': 'success'})


@cache.cached(timeout=120)
@app.route('/api/settings', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_settings():
    conn = database.create_connection()
    settings_query = conn.query(Setting).all()
    settings = [setting.__response_json__() for setting in settings_query]
    database.close_connection(conn)
    return jsonify({'settings': settings})


@cache.cached(timeout=120)
@app.route('/api/reminders', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_reminders():
    conn = database.create_connection()
    reminders_query = conn.query(Reminder).all()
    reminders = [reminder.__response_json__() for reminder in reminders_query]
    database.close_connection(conn)
    return jsonify({'reminders': reminders})


@app.route('/api/upcoming/reminders', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_upcoming_reminders():
    conn = database.create_connection()
    reminders_query = conn.query(Reminder)

    once_upcoming_query = reminders_query.filter(Reminder.recurrence == 'ONCE').filter(Reminder.date > datetime.now(),
                                                                                       Reminder.start_time > datetime.now().time()).all()
    monthly_upcoming_query = reminders_query.filter(Reminder.recurrence == 'MONTHLY').all()

    everyday_upcoming_query = reminders_query.filter(Reminder.recurrence == 'DAILY').filter(
        Reminder.start_time > datetime.now().time()).all()

    every_recurrence_query = reminders_query.filter(Reminder.recurrence.like('%EVERY%')).all()

    # Convert query results to dictionaries
    reminders = []

    reminders.extend([reminder.__response_json__() for reminder in once_upcoming_query])
    reminders.extend([reminder.__response_json__() for reminder in monthly_upcoming_query])
    reminders.extend([reminder.__response_json__() for reminder in everyday_upcoming_query])
    reminders.extend([reminder.__response_json__() for reminder in every_recurrence_query])
    database.close_connection(conn)
    return jsonify({'reminders': reminders})


@app.route('/api/reminder/operations', methods=['POST'])
@limiter.limit(rate_limit_rule)
def operation_on_reminder():
    conn = database.create_connection()
    type = request.args.get('type')
    reminder = json.loads(request.args.get('reminder'))
    file_path = f"{updator.dest_path}/reminders.json"
    any_performed = False

    try:
        if 'delete' == type:
            delete_query = conn.query(Reminder).filter(Reminder.uid == reminder['id']).first()
            print(delete_query)
            if delete_query:
                conn.delete(delete_query)
                any_performed = True
        elif 'update' == type:
            update_query = conn.query(Reminder).filter(Reminder.uid == reminder['id']).first()
            if update_query:
                update_query.name = reminder['name']
                update_query.description = reminder['description']
                update_query.recurrence = reminder['recurrence']
                update_query.start_time = reminder['start_time']
                update_query.end_time = reminder['end_time']
                update_query.date = reminder['date']
                any_performed = True
                # Add any other fields that need to be updated here
            else:
                return jsonify({'error': 'Reminder not found'}), 404
        else:
            return jsonify({'error': 'Invalid type'}), 400

        if any_performed:
            data = [reminder.__data_store__() for reminder in conn.query(Reminder).all()]
            updator.save_json_file(data, file_path)
            updator.commit_and_push(file_path)

            conn.commit()
            cache.clear()
        return jsonify({'message': 'success'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@cache.cached(timeout=120)
@app.route('/api/timeline', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_timeline():
    conn = database.create_connection()
    # Query distinct problem dates
    distinct_dates_query = conn.query(
        func.distinct(func.date(Problem.date_added)).label("problem_date")
    ).order_by(desc("problem_date")).all()

    # Initialize timelines
    full_timeline = {}
    prev_timeline = {}
    curr_timeline = {}

    # Iterate over distinct dates
    for item in distinct_dates_query:
        date_value = datetime.strptime(item.problem_date, "%Y-%m-%d").date()

        # Build base query
        base_query = conn.query(
            Problem.id,
            Problem.name
        ).filter(func.date(Problem.date_added) == date_value).order_by(Problem.name)

        # Execute query
        data = base_query.all()

        # Convert query results to dictionaries
        problems = [
            {'id': id, 'name': name, 'slug': utility.create_slug(name)}
            for id, name in data
        ]

        # Determine current and previous timelines
        if date_value.month == datetime.now().month:
            curr_timeline[item.problem_date] = problems

        if date_value.month == (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1).month:
            prev_timeline[item.problem_date] = problems

        full_timeline[item.problem_date] = problems

    # Close the database connection
    database.close_connection(conn)

    timeline = {
        'full_timeline': full_timeline,
        'current_timeline': curr_timeline,
        'previous_timeline': prev_timeline
    }

    # Return JSON response
    return jsonify({'timeline': timeline})


@cache.cached(timeout=120)
@app.route('/api/analytics', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_analytics():
    # Return the analytics dictionary as JSON response
    return jsonify({'analytics': analytics.get_analytics()})


@app.route('/api/update', methods=['POST'])
def update_system():
    if os.path.exists("codebase.lock"):
        return jsonify({'message': 'sys-update'})
    else:
        utility.copy_file("codebase.db", "readonly_codebase.db")
        updator.init_system(True)
    return jsonify({'message': 'success'})


@app.route('/api/upload', methods=['POST'])
@limiter.limit(rate_limit_rule)
def upload_file():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files are added'}), 400

    files = request.files.getlist('files[]')
    additional_params = request.form.to_dict()

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    uploaded_files = []
    for file in files:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Save the file to the temporary directory
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)
        uploaded_files.append(file_path)

    response, code = updator.upload_conditions(additional_params, uploaded_files)
    # Remove temporary directory and its contents
    shutil.rmtree(temp_dir)
    cache.clear()
    if code != 200:
        return jsonify(response), 200

    return jsonify({'message': 'Files uploaded successfully'}), 200


@app.route('/api/webhook', methods=['POST'])
@limiter.limit(rate_limit_rule)
def webhook_api():
    performAction(request.json)
    response = {'message': 'success'}
    return jsonify(response), 200


@app.route('/api/branch', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_branch():
    branch = updator.get_branch()
    branches = updator.get_branches()
    if branch is None:
        return jsonify({'message': 'server-error'}), 500
    return jsonify({
        'message': 'success',
        'branch': {
            'current': branch,
            'branches': branches
        }
    })


@app.route('/api/switch/branch', methods=['POST'])
def switch_branch():
    branch = request.args.get('branch')
    if branch is None and branch not in updator.get_branches():
        return jsonify({'message': 'bad request'}), 400
    else:
        appenv.environ['BRANCH_NAME'] = branch
        utility.write_text_to_file('../config.yaml', appenv.environ)
        conn = database.create_connection()
        updator.reset_progress(conn)
        conn.close()
        updator.init_system()
    return jsonify({
        'message': 'success'
    })


@app.route('/api/status', methods=['GET'])
def system_status():
    status = 'success'
    if os.path.exists("codebase.lock"):
        status = 'sys-update'
    return jsonify({'message': status})


@app.route('/api/clear', methods=['GET'])
@limiter.limit(rate_limit_rule)
def system_cache_clear():
    cache.clear()
    return jsonify({'message': 'success'})


@app.errorhandler(429)
def ratelimit_error(e):
    return jsonify({"error": "Too many requests..."}), 429
