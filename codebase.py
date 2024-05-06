import json
import os
import random
import shutil
import tempfile
import threading
from datetime import datetime, timedelta
import re

from flask_caching import Cache
from sqlalchemy import func, and_, distinct, desc

import analytics
import appenv
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import logging
import database_utility as database
import application_updator as updator
import utility
from models import Quote, Problem, ProblemType, Note, Platform, Tracker, Company, Remark, Setting, Reminder, Playlist, \
    PlaylistItem

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
CORS(app)  # Enable CORS for all routes

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

port = 5000
if "PORT" in appenv.environ:
    port = appenv.environ["PORT"]


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def home(path):
    if os.path.exists("static"):
        if path != "" and os.path.exists("static/" + path):
            return send_from_directory("static", path)
        else:
            return send_from_directory("static", "index.html")
    else:
        return "Codebase-Flask is Active"


@app.route('/file/<path:file_path>')
def serve_file(file_path):
    file_path = file_path.replace("<repo_path>", utility.get_running_repo(updator.dest_path))
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path)
    else:
        return "File not found", 404


@app.route('/code/<path:file_path>')
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
def random_quote():
    conn = database.create_connection()
    max_id = conn.query(func.max(Quote.id)).scalar()
    # Generate a random ID within the range of available IDs
    random_id = random.randint(1, max_id)
    # Query the quote with the random ID
    rquote = conn.query(Quote.author, Quote.content).filter(Quote.id == random_id).first()
    return jsonify({'content': rquote[1], 'author': rquote[0]}), 200


@cache.cached(timeout=120)
@app.route('/api/songs', methods=['GET'])
def get_songs():
    songs = updator.get_songs()
    if songs is not None:
        return jsonify({'songs': songs})
    else:
        return jsonify({'songs': []})


@cache.cached(timeout=120)
@app.route('/api/problems', methods=['GET'])
def get_problems():
    conn = database.create_connection()

    # Extract query parameters
    type_filter = request.args.get('type')
    status_filter = request.args.get('status')
    level_filter = request.args.get('level')

    base_query = conn.query(
        Problem.id, Problem.name, ProblemType.name.label('typename'),
        Problem.description, Problem.url, Problem.level, Problem.status,
        Problem.notes, Problem.date_added, Problem.filename,
        Problem.companies, Problem.remarks, Problem.subdirectory
    ).join(ProblemType, Problem.typeid == ProblemType.id)

    # Add conditions based on query parameters
    conditions = []

    if type_filter:
        conditions.append(ProblemType.name == type_filter)
    if level_filter:
        conditions.append(Problem.level == level_filter)
    if status_filter:
        conditions.append(Problem.status == status_filter)

    # Apply conditions to the query
    if conditions:
        base_query = base_query.filter(and_(*conditions))

    # Execute the query and fetch the results
    results = base_query.all()
    problems = []
    for item in results:
        id, name, type, description, url, level, status, notes, date, filename, companies, remarks, subdirectory = item

        if companies is not None:
            companies = str(companies).replace(":", ",")
            temp = []
            for company_str in companies.split(","):
                q = conn.query(Company.name, Company.logo, Company.color_light, Company.color_dark).filter(
                    Company.name == company_str)
                # Assuming you're using SQLAlchemy, you can execute the query to get the results
                company_result = q.first()  # Retrieves the first result
                if company_result:
                    company_info = {
                        "name": company_result[0],
                        "logo": company_result[1],
                        "color_light": company_result[2],
                        "color_dark": company_result[3]
                    }
                    temp.append(company_info)
            companies = temp
        else:
            companies = []
        problems.append(
            {'id': id, 'name': name, 'slug': utility.create_slug(name), 'type': type, 'description': description,
             'url': url, 'level': level,
             'status': status,
             'notes': notes, 'date': date, 'filename': filename, 'companies': companies,
             'remarks': remarks, 'subdirectory': subdirectory})
    database.close_connection(conn)
    return jsonify({'problems': problems})


@cache.cached(timeout=120)
@app.route('/api/notes', methods=['GET'])
def get_notes():
    conn = database.create_connection()

    base_query = conn.query(distinct(Note.title)).order_by(Note.title)

    # Fetch data
    data = base_query.all()
    notes = []
    for item in data:
        slug = utility.create_slug(item[0])
        notes.append(
            {
                "title": item[0],
                "slug": slug
            }
        )

    for note in notes:
        # Fetch filenames and extensions for the current note
        filenames_and_extensions = conn.query(Note.filename, Note.extension).filter(
            Note.title == note['title']).order_by(Note.filename).all()

        # Extract filenames and extensions
        urls = [filename for filename, _ in filenames_and_extensions]
        extensions = [extension for _, extension in filenames_and_extensions]

        # Update the note dictionary with the fetched data
        note['urls'] = urls
        note['extensions'] = extensions
    database.close_connection(conn)
    return jsonify({'notes': notes})


@app.route('/api/note/operations', methods=['POST'])
def operation_on_note():
    conn = database.create_connection()
    type = request.args.get('type')
    note = json.loads(request.args.get('note'))

    if 'delete' == type:
        delete_query = conn.delete(Note).where(Note.id == note.id)
        print(type)
    elif 'update' == type:
        print(type)
    else:
        print(type)
    conn.commit()
    conn.close()
    return jsonify({'message': 'success'})


@cache.cached(timeout=120)
@app.route('/api/problem/types', methods=['GET'])
def get_problem_types():
    conn = database.create_connection()
    query_result = conn.query(ProblemType.name, ProblemType.description).order_by(ProblemType.name).all()
    problem_types = [{'name': name, 'description': description, 'slug': utility.create_slug(name)} for name, description
                     in query_result]
    database.close_connection(conn)
    return jsonify({'types': problem_types})


@cache.cached(timeout=120)
@app.route('/api/problem/levels', methods=['GET'])
def get_problem_levels():
    conn = database.create_connection()
    query_result = conn.query(Problem.level).distinct().all()
    problem_levels = [{'level': value[0], 'slug': utility.create_slug(value[0])} for value in query_result]
    database.close_connection(conn)
    return jsonify({'levels': problem_levels})


@cache.cached(timeout=120)
@app.route('/api/problem/statuses', methods=['GET'])
def get_problem_statuses():
    conn = database.create_connection()
    query_result = conn.query(Problem.status).distinct().all()
    problem_statuses = [{'status': value[0], 'slug': utility.create_slug(value[0])} for value in query_result]

    database.close_connection(conn)
    return jsonify({'statuses': problem_statuses})


@cache.cached(timeout=120)
@app.route('/api/platforms', methods=['GET'])
def get_platforms():
    conn = database.create_connection()
    platforms_query = conn.query(Platform.name, Platform.url, Platform.icon).all()
    platforms = [
        {'name': name, 'url': url, 'icon': icon, 'slug': utility.create_slug(name)}
        for name, url, icon in platforms_query
    ]
    database.close_connection(conn)
    return jsonify({'platforms': platforms})


@app.route('/api/platform/operations', methods=['POST'])
def operation_on_platform():
    conn = database.create_connection()
    type = request.args.get('type')
    platform = json.loads(request.args.get('platform'))

    if 'delete' == type:
        delete_query = conn.delete(Platform).where(Platform.id == platform.id)
        print(type)
    elif 'update' == type:
        print(type)
    else:
        print(type)
    conn.commit()
    conn.close()
    return jsonify({'message': 'success'})


@cache.cached(timeout=120)
@app.route('/api/trackers', methods=['GET'])
def get_trackers():
    conn = database.create_connection()
    trackers_query = conn.query(Tracker.name, Tracker.level).all()
    trackers = [
        {'name': name, 'level': level, 'slug': utility.create_slug(name)}
        for name, level in trackers_query
    ]
    database.close_connection(conn)
    return jsonify({'trackers': trackers})


@app.route('/api/tracker/operations', methods=['POST'])
def operation_on_tracker():
    conn = database.create_connection()
    type = request.args.get('type')
    tracker = json.loads(request.args.get('tracker'))

    if 'delete' == type:
        delete_query = conn.delete(Tracker).where(Tracker.id == tracker.id)
        print(type)
    elif 'update' == type:
        print(type)
    else:
        print(type)
    conn.commit()
    conn.close()
    return jsonify({'message': 'success'})


@cache.cached(timeout=120)
@app.route('/api/companies', methods=['GET'])
def get_companies():
    conn = database.create_connection()
    companies_query = conn.query(Company.name, Company.color_light, Company.color_dark).all()
    companies = [
        {'name': company[0], 'color_light': company[1], 'color_dark': company[2],
         'slug': utility.create_slug(company[0])}
        for company in companies_query
    ]
    database.close_connection(conn)
    return jsonify({'companies': companies})


@cache.cached(timeout=120)
@app.route('/api/remarks', methods=['GET'])
def get_remarks():
    conn = database.create_connection()
    remarks_query = conn.query(Remark.text).all()
    remarks = [
        {'remark': item[0], 'slug': utility.create_slug(item[0])}
        for item in remarks_query
    ]
    database.close_connection(conn)
    return jsonify({'remarks': remarks})


@cache.cached(timeout=120)
@app.route('/api/playlists', methods=['GET'])
def get_playlists():
    conn = database.create_connection()
    playlist_query = conn.query(Playlist).all()
    playlists = []
    for playlist in playlist_query:
        playlist_info = {
            'id': playlist.uid,
            'title': playlist.title,
            'status': playlist.status,
            'description': playlist.description,
            'sections': [
                {
                    'id': section.uid,
                    'title': section.title,
                    'description': section.description,
                    'status': section.status,
                    'items': [
                        {
                            'id': item.uid,
                            'title': item.title,
                            'description': item.description,
                            'status': item.status,
                            'url': item.url,
                            'image': item.image,
                            'content': item.content,
                            'type': item.content_type
                        }
                        for item in section.items
                    ]
                }
                for section in playlist.sections
            ]
        }
        playlists.append(playlist_info)
    database.close_connection(conn)
    return jsonify({'playlists': playlists})


@app.route('/api/playlist/operations', methods=['POST'])
def operation_on_playlist():
    conn = database.create_connection()
    type = request.args.get('type')
    playlist = json.loads(request.args.get('playlist'))

    if 'delete' == type:
        delete_query = conn.delete(Playlist).where(Playlist.uid == playlist.id)
        print(type)
    elif 'update' == type:
        print(type)
    else:
        print(type)
    conn.commit()
    conn.close()
    return jsonify({'message': 'success'})


@app.route('/api/playlist/item/status', methods=['POST'])
def update_playlist_item_status():
    conn = database.create_connection()
    item_id = request.args.get('item')
    item_status = request.args.get('status', 'INPROGRESS')
    item = conn.query(PlaylistItem).filter_by(uid=item_id).first()
    if item is not None:
        item.status = item_status

        # Check if all items in the section are completed
        section = item.section

        section_completed = all(item.status == 'COMPLETED' for item in section.items)

        # If all items in the section are completed, update the section status
        if section_completed:
            section.status = 'COMPLETED'

            # Check if all sections in the playlist are completed
            playlist = section.playlist
            playlist_completed = all(section.status == 'COMPLETED' for section in playlist.sections)

            # If all sections in the playlist are completed, update the playlist status
            if playlist_completed:
                playlist.status = 'COMPLETED'
        else:
            section_any_completed = any(item.status == 'COMPLETED' for item in section.items)
            if section_any_completed:
                section.status = 'INPROGRESS'
                playlist = section.playlist
                playlist.status = 'INPROGRESS'

    else:
        conn.close()
        return jsonify({'message': 'not-found'}), 404
    # Commit the changes to the database
    conn.commit()
    conn.close()
    return jsonify({'message': 'success'})


@cache.cached(timeout=120)
@app.route('/api/settings', methods=['GET'])
def get_settings():
    conn = database.create_connection()
    settings_query = conn.query(Setting.key, Setting.value).all()
    settings = [{'name': key, 'config': value} for key, value in settings_query]
    database.close_connection(conn)
    return jsonify({'settings': settings})


@cache.cached(timeout=120)
@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    conn = database.create_connection()
    reminders_query = conn.query(
        Reminder.name,
        Reminder.description,
        Reminder.recurrence,
        Reminder.start_time,
        Reminder.end_time,
        Reminder.date
    ).all()

    # Convert query results to dictionaries
    reminders = [
        {
            'name': name,
            'description': description,
            'recurrence': recurrence,
            'start_time': start_time,
            'end_time': end_time,
            'date': date
        }
        for name, description, recurrence, start_time, end_time, date in reminders_query
    ]
    database.close_connection(conn)
    return jsonify({'reminders': reminders})


@app.route('/api/reminder/operations', methods=['POST'])
def operation_on_reminder():
    conn = database.create_connection()
    type = request.args.get('type')
    reminder = json.loads(request.args.get('reminder'))

    if 'delete' == type:
        delete_query = conn.delete(Reminder).where(Reminder.id == reminder.id)
    elif 'update' == type:
        update_query = conn.delete(Reminder).where(Reminder.id == reminder.id)
    else:
        print(type)
    conn.commit()
    conn.close()
    return jsonify({'message': 'success'})


@cache.cached(timeout=120)
@app.route('/api/timeline', methods=['GET'])
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
def get_analytics():
    # Return the analytics dictionary as JSON response
    return jsonify({'analytics': analytics.get_analytics()})


@app.route('/api/update', methods=['POST'])
def update_system():
    if os.path.exists("codebase.lock"):
        return jsonify({'message': 'sys-update'})
    else:
        utility.copy_file("codebase.db", "readonly_codebase.db")
        cache.clear()
        threading.Thread(target=updator.init_system, args=(True,)).start()
    return jsonify({'message': 'success'})


@app.route('/api/upload', methods=['POST'])
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
    if code != 200:
        return jsonify(response), 200

    return jsonify({'message': 'Files uploaded successfully'}), 200


@app.route('/api/status', methods=['GET'])
def system_status():
    status = 'success'
    if os.path.exists("codebase.lock"):
        status = 'sys-update'
    return jsonify({'message': status})
