import logging
import os
import time
from io import BytesIO

import redis
import requests
from flask import Flask, jsonify, abort, send_from_directory, send_file
from flask_caching import Cache
from flask_cors import CORS
import pandas as pd
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config_manager import config_manager as appenv
import database_utility
from models import Sheet, Playlist

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

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

port = 5100
baseport = 5000
if "PORT" in appenv.environ:
    baseport = int(appenv.environ["PORT"])
    port = int(appenv.environ["PORT"]) + 100


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def home(path):
    current_folder = os.path.dirname(__file__)
    static_folder = os.path.join(current_folder, 'marketplace-ui')

    if os.path.exists(static_folder):
        if path != "" and os.path.exists(os.path.join(static_folder, path)):
            return send_from_directory(static_folder, path)
        else:
            return send_from_directory(static_folder, "index.html")
    else:
        return "Codebase-Marketplace is Active"


@app.route('/status')
def status():
    return jsonify({
        'status': 'active'
    })


@cache.cached(timeout=120)
@app.route('/sheets', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_sheets():
    # Query all sheets
    logging.info("get_sheets(): begin..")
    conn = database_utility.init_database()
    sheets = conn.query(Sheet.uid, Sheet.name, Sheet.image, Sheet.total_items_count).all()
    sheets_data = [{'uid': sheet[0], 'name': sheet[1], 'image': sheet[2], 'total_count': sheet[3]} for sheet in sheets]
    return jsonify({
        'sheets': sheets_data
    })


@app.route('/sheet/import/<string:uid>', methods=['GET'])
@limiter.limit(rate_limit_rule)
def import_sheet(uid):
    logging.info("import_sheet(" + uid + "): begin..")
    conn = database_utility.init_database()
    sheet = conn.query(Sheet).filter_by(uid=uid).first()
    if sheet is None:
        abort(404, description="Sheet not found")

    sheet_data = sheet.__response_json__()

    # Define the webhook endpoint URL
    webhook_url = f'http://localhost:{baseport}/cb/api/webhook'

    # Define the JSON payload to send
    payload = {
        "event": "import-sheet",
        "payload": sheet_data
    }

    # Send a POST request to the webhook endpoint with the JSON payload
    response = requests.post(webhook_url, json=payload)

    # Check the response status code and content
    if response.status_code == 200:
        logging.info(f"Webhook call successful for sheet {uid}")
    else:
        logging.info(f'Error while calling webhook for sheet {uid} \n {response.text}')

    return response.json(), response.status_code


@app.route('/sheet/download/<string:uid>', methods=['GET'])
@limiter.limit(rate_limit_rule)
def download_sheet(uid):
    sheet_csv = ['Name', 'URL', 'Description', 'Level', 'Category', 'Companies', 'Concepts', 'Frequency']
    # Query the sheet by uid
    logging.info("download_sheet_csv(" + uid + "): begin..")
    conn = database_utility.init_database()
    sheet = conn.query(Sheet).filter_by(uid=uid).first()
    if sheet is None:
        abort(404, description="Sheet not found")

    sheet_data = sheet.__response_json__()
    sheet_list = []
    for section in sheet_data['sections']:
        section_name = section['title']
        for item in section['items']:
            sheet_sub_list = [item['title'], item['url'], item['description'], item['level'], section_name,
                              ",".join(item['companies']), ",".join(item['concepts']), item['frequency']]
            sheet_list.append(sheet_sub_list)
    excel_file = generate_excel(sheet_csv, sheet_list)

    title = sheet_data['title']
    download_name = f'{title}.xlsx'
    # Send the Excel file as a response
    return send_file(excel_file, as_attachment=True, download_name=download_name,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


def generate_excel(headers, data):
    # Create a DataFrame from the headers and data
    df = pd.DataFrame(data, columns=headers)

    # Save the DataFrame to an Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)  # Rewind the buffer
    return output


@cache.cached(timeout=120)
@app.route('/sheet/<string:uid>', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_sheet_by_uid(uid):
    # Query the sheet by uid
    logging.info("get_sheet(" + uid + "): begin..")
    conn = database_utility.init_database()
    sheet = conn.query(Sheet).filter_by(uid=uid).first()
    if sheet is None:
        abort(404, description="Sheet not found")
    sheet_data = sheet.__response_json__()
    return jsonify({
        'sheet': sheet_data
    })


@cache.cached(timeout=120)
@app.route('/playlists', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_playlists():
    # Query all playlists
    logging.info("get_playlists(): begin..")
    conn = database_utility.init_database()
    playlists = conn.query(Playlist.uid, Playlist.title, Playlist.description, Playlist.total_items_count).all()
    playlists_data = [{'uid': playlist[0], 'name': playlist[1], 'desc': playlist[2], 'total_count': playlist[3]} for
                      playlist in playlists]
    return jsonify({
        'playlists': playlists_data
    })


@cache.cached(timeout=120)
@app.route('/playlist/<string:uid>', methods=['GET'])
@limiter.limit(rate_limit_rule)
def get_playlist_by_uid(uid):
    # Query the playlist by uid
    logging.info("get_playlist(" + uid + "): begin..")
    conn = database_utility.init_database()
    playlist = conn.query(Playlist).filter_by(uid=uid).first()
    if playlist is None:
        abort(404, description="Playlist not found")
    playlist_data = playlist.__response_json__()
    return jsonify({
        'playlist': playlist_data
    })


@app.route('/playlist/import/<string:uid>', methods=['GET'])
@limiter.limit(rate_limit_rule)
def import_playlist(uid):
    logging.info("import_playlist(" + uid + "): begin..")
    conn = database_utility.init_database()
    playlist = conn.query(Playlist).filter_by(uid=uid).first()
    if playlist is None:
        abort(404, description="Sheet not found")

    playlist_data = playlist.__response_json__()

    # Define the webhook endpoint URL
    webhook_url = f'http://localhost:{baseport}/cb/api/webhook'

    # Define the JSON payload to send
    payload = {
        "event": "import-playlist",
        "payload": playlist_data
    }

    # Send a POST request to the webhook endpoint with the JSON payload
    response = requests.post(webhook_url, json=payload)

    # Check the response status code and content
    if response.status_code == 200:
        logging.info(f"Webhook call successful for playlist {uid}")
    else:
        logging.info(f'Error while calling webhook for playlist {uid} \n {response.text}')

    return response.json(), response.status_code


@app.errorhandler(429)
def ratelimit_error(e):
    return jsonify({"error": "Too many requests..."}), 429