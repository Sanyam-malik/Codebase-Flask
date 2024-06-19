import json
import logging
import time
from datetime import datetime

from flask import Flask, request, jsonify, Response, redirect
import requests
from flask_cors import CORS
from config_manager import config_manager as appenv


def load_config(config_path='../gateway-config.json'):
    with open(config_path, 'r') as config_file:
        return json.load(config_file)


app = Flask(__name__)
instance_name = load_config()['instance-name']
default_path = load_config()['default']
services = load_config()['services']
CORS(app)  # Enable CORS for all routes

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

port = 5000
if "PORT" in appenv.environ:
    port = int(appenv.environ["PORT"])

start_time = time.time()

@app.route('/', methods=['GET'])
def home():
    try:
        response = requests.request(
            method=request.method,
            url=default_path,
            headers={key: value for key, value in request.headers.items() if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)

        # Return the response content, status code, and headers as-is
        return Response(response.content, content_type=response.headers.get(
            'content-type')), response.status_code, response.headers.items()
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Return any exception as a JSON response with HTTP status code 500


@app.route('/status', methods=['GET'])
def status():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    uptime_seconds = time.time() - start_time
    uptime = str(datetime.utcfromtimestamp(uptime_seconds).strftime('%H:%M:%S'))
    
    app_status = {
        'Current Time': current_time,
        'Server Uptime': uptime
    }
    
    app_services = {}
    for service in services:
        service_name = service['name']
        service_url = service['service_url']
        try:
            response = requests.get(f"{service_url}/status")
            if response.status_code == 200:
                app_services[service_name] = "Healthy"
            else:
                app_services[service_name] = "Unhealthy"
        except requests.exceptions.RequestException:
            app_services[service_name] = "Unreachable"

    return {
        "name": instance_name,
        "status": app_status,
        "services": app_services
    }


@app.route('/<path:service>', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/<path:service>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(service, path):
    service_config = next((s for s in services if s.get('base_url').lstrip('/') == service), None)
    if not service_config:
        return jsonify({'error': 'Service not found'}), 404

    service_url = service_config['service_url']
    full_url = f"{service_url}/{path}" if path else service_url

    try:
        response = requests.request(
            method=request.method,
            url=full_url,
            headers={key: value for key, value in request.headers if key != 'Host'},
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False
        )

        # Create the Flask response
        flask_response = Response(response.content, status=response.status_code)
        for key, value in response.headers.items():
            if key.lower() != 'content-length':  # Let Flask handle content-length
                flask_response.headers[key] = value

        return flask_response

    except Exception as e:
        return jsonify({'error': str(e)}), 500
