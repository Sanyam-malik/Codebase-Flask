import logging
import os

import redis
import shortuuid
from flask import Flask, jsonify, send_from_directory, request
from flask_caching import Cache
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models import VideoSolutions
from services import youtube_service, chatgpt_service, coderunner_service
import database_utility as database
from config_manager import config_manager as appenv

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

port = 5150
baseport = 5000
if "PORT" in appenv.environ:
    baseport = int(appenv.environ["PORT"])
    port = int(appenv.environ["PORT"]) + 150


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def home(path):
    current_folder = os.path.dirname(__file__)
    static_folder = os.path.join(current_folder, 'integration-ui')

    if os.path.exists(static_folder):
        if path != "" and os.path.exists(os.path.join(static_folder, path)):
            return send_from_directory(static_folder, path)
        else:
            return send_from_directory(static_folder, "index.html")
    else:
        return "Codebase-Integration is Active"


@app.route('/status')
def status():
    return jsonify({
        'status': 'active'
    })


@app.route('/run/code', methods=['POST'])
@limiter.limit(rate_limit_rule)
def run_code():
    params = request.json
    lang = params['language']
    code = params['code']
    if coderunner_service.is_available(lang):
        output = coderunner_service.compile_and_run(lang, code)
        output['message'] = 'success'
        return output, 200
    else:
        return {
            "message": "language-not-available"
        }, 503


@app.route('/chatgpt/solution', methods=['POST'])
@limiter.limit(rate_limit_rule)
def get_chat_solution():
    problem = request.json
    is_available = chatgpt_service.is_available()
    if is_available is False:
        return {"message": "service-unavailable"}, 503
    else:
        extension = problem['filename'].split('.')[-1]
        query = f"{extension} code for {problem['name']} with comments and nothing more "
        response = chatgpt_service.get_chatgpt_response(query)
        if response['message'] == "error":
            return {"message": "service-error"}, 500
        else:
            return response


@app.route('/youtube/solution', methods=['POST'])
@limiter.limit(rate_limit_rule)
def get_problem_solution():
    conn = database.create_connection()
    problem = request.json
    # Check if data is already present
    existing_solutions = conn.query(VideoSolutions).filter_by(problem_slug=problem['slug']).all()
    if existing_solutions:
        return {
            'message': "success",
            'content': [solution.__response_json__() for solution in existing_solutions]
        }
    else:
        is_available = youtube_service.is_available()
        if is_available is False:
            return {"message": "service-unavailable"}, 503
        else:
            query = f"{problem['name']} problem solution"
            response = youtube_service.get_top_youtube_videos(query)
            if response['message'] == "error":
                return {"message": "service-error"}, 500
            else:
                for item in response['content']:
                    uid = shortuuid.uuid()
                    result = VideoSolutions.from_json({
                        'id': uid,
                        'problem_slug': problem['slug'],
                        'title': item['title'],
                        'description': item['description'],
                        'image': item['thumbnail'],
                        'url': item['url'],
                        'channel': item['channelTitle']
                    })
                    conn.add(result)
                conn.commit()
                solutions = conn.query(VideoSolutions).filter_by(problem_slug=problem['slug']).all()
                conn.close()
            return {
                'message': "success",
                'content': [solution.__response_json__() for solution in solutions]
            }


@app.errorhandler(429)
def ratelimit_error(e):
    return jsonify({"error": "Too many requests..."}), 429
