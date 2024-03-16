import os
import re
import threading
from datetime import datetime, timedelta

import sysenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS  # Import the CORS extension
import logging
import database
import updator
import schedule

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

port = 5000
if "PORT" in sysenv.environ:
    port = sysenv.environ["PORT"]


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


@app.route('/api/problems', methods=['GET'])
def get_problems():
    conn = database.create_connection()

    # Extract query parameters
    type_filter = request.args.get('type')
    status_filter = request.args.get('status')
    level_filter = request.args.get('level')

    # Build the base query
    base_query = "SELECT p.id, p.name, pt.name as typename, p.description, p.url, p.level, p.status, p.notes, p.date_added, p.filename, p.companies, p.remarks " \
                 "FROM problems p JOIN problem_type pt ON p.typeid = pt.id"

    # Add conditions based on query parameters
    conditions = []
    if type_filter:
        conditions.append(f"pt.name = '{type_filter}'")
    if level_filter:
        conditions.append(f"p.level = '{level_filter}'")
    if status_filter:
        conditions.append(f"p.status = '{status_filter}'")

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    # Fetch data
    data = database.fetch_data(conn, base_query)
    problems = []
    for item in data:
        id, name, type, description, url, level, status, notes, date, filename, companies, remarks = item

        if companies is not None:
            companies = str(companies).replace(":", ",")

        code = ''
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()
            f.close()

        problems.append(
            {'id': id, 'name': name, 'slug': create_slug(name), 'type': type, 'description': description, 'url': url, 'level': level,
             'status': status,
             'notes': notes, 'date': date, 'filename': filename, 'code': code, 'companies': companies,
             'remarks': remarks})
    database.close_connection(conn)
    return jsonify({'problems': problems})


@app.route('/api/problem/types', methods=['GET'])
def get_problem_types():
    conn = database.create_connection()
    data = database.fetch_data(conn, "SELECT name, description FROM problem_type")
    problem_types = [{'name': name, 'description': description, 'slug': create_slug(name)} for name, description in data]
    database.close_connection(conn)
    return jsonify({'problem_types': problem_types})


@app.route('/api/problem/levels', methods=['GET'])
def get_problem_levels():
    conn = database.create_connection()
    data = database.fetch_data(conn, "SELECT distinct(p.level) FROM problems p")
    problem_levels = [{'level': value[0], 'slug': create_slug(value[0])} for value in data]
    database.close_connection(conn)
    return jsonify({'problem_levels': problem_levels})


@app.route('/api/problem/statuses', methods=['GET'])
def get_problem_statuses():
    conn = database.create_connection()
    data = database.fetch_data(conn, "SELECT distinct(p.status) FROM problems p")
    problem_statuses = [{'status': value[0], 'slug': create_slug(value[0])} for value in data]
    database.close_connection(conn)
    return jsonify({'problem_statuses': problem_statuses})


@app.route('/api/platforms', methods=['GET'])
def get_platforms():
    conn = database.create_connection()
    data = database.fetch_data(conn, "SELECT name, url, icon FROM platforms")
    platforms = [{'name': name, 'url': url, 'icon': icon, 'slug': create_slug(name)} for name, url, icon in data]
    database.close_connection(conn)
    return jsonify({'platforms': platforms})


@app.route('/api/trackers', methods=['GET'])
def get_trackers():
    conn = database.create_connection()
    data = database.fetch_data(conn, "SELECT name, level FROM trackers")
    trackers = [{'name': name, 'level': level, 'slug': create_slug(name)} for name, level in data]
    database.close_connection(conn)
    return jsonify({'trackers': trackers})


@app.route('/api/companies', methods=['GET'])
def get_companies():
    conn = database.create_connection()
    data = database.fetch_data(conn, "SELECT name FROM companies")
    companies = [{'name': name[0], 'slug': create_slug(name[0])} for name in data]
    database.close_connection(conn)
    return jsonify({'companies': companies})


@app.route('/api/remarks', methods=['GET'])
def get_remarks():
    conn = database.create_connection()
    data = database.fetch_data(conn, "SELECT text from remarks")
    remarks = [{'remark': item[0], 'slug': create_slug(item[0])} for item in data]
    database.close_connection(conn)
    return jsonify({'remarks': remarks})


@app.route('/api/settings', methods=['GET'])
def get_settings():
    conn = database.create_connection()
    data = database.fetch_data(conn, "SELECT key, value FROM settings")
    settings = [{'name': key, 'config': value} for key, value in data]
    database.close_connection(conn)
    return jsonify({'settings': settings})


@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    conn = database.create_connection()
    data = database.fetch_data(conn, "SELECT name, description, recurrence, start_time, end_time, date FROM reminders")
    reminders = [{'name': name, 'description': description, 'recurrence': recurrence, 'start_time': start_time,
                  'end_time': end_time, 'date': date} for name, description, recurrence, start_time, end_time, date in
                 data]
    database.close_connection(conn)
    return jsonify({'reminders': reminders})


@app.route('/api/timeline', methods=['GET'])
def get_timeline():
    conn = database.create_connection()
    full_query__result = database.fetch_data(conn,
                                             "select DISTINCT(Date(date_added)) as problem_date from problems order by problem_date desc")
    full_timeline = {}
    prev_timeline = {}
    curr_timeline = {}

    for item in full_query__result:
        date_value = item[0]
        base_query = "SELECT p.id, p.name from problems p where DATE(p.date_added) == '" + date_value + "' order by DATE(p.date_added) ASC"
        # Fetch data
        data = database.fetch_data(conn, base_query)
        problems = []
        for value in data:
            id, name = value
            problems.append({'id': id, 'name': name, 'slug': create_slug(name)})

        if datetime.strptime(date_value, "%Y-%m-%d").month == datetime.now().month:
            curr_timeline[date_value] = problems

        if datetime.strptime(date_value, "%Y-%m-%d").month == (
                datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1).month:
            prev_timeline[date_value] = problems

        full_timeline[date_value] = problems
    database.close_connection(conn)
    return jsonify(
        {'full_timeline': full_timeline, 'current_timeline': curr_timeline, 'previous_timeline': prev_timeline})


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    analytics = {}
    conn = database.create_connection()
    total_count = database.fetch_data(conn, "SELECT count(*) from problems")
    today_count = database.fetch_data(conn,
                                      "SELECT COUNT(*) FROM problems p where date(p.date_added) = date('now', 'localtime')")
    month_count = database.fetch_data(conn,
                                      "SELECT COUNT(*) FROM problems p WHERE strftime('%m', p.date_added) = strftime('%m', 'now') AND strftime('%Y', p.date_added) = strftime('%Y', 'now')")
    prev_month = database.fetch_data(conn,
                                     "SELECT COUNT(*) FROM problems p WHERE strftime('%m', p.date_added) = strftime('%m', 'now', '-1 month') AND strftime('%Y', p.date_added) = strftime('%Y', 'now', '-1 month')")
    prev_month_focus = database.fetch_data(conn, '''
    SELECT name
        FROM (
            SELECT pt.name, COUNT(p.id) AS count_by_name
            FROM problem_type pt
            LEFT JOIN problems p ON p.typeid = pt.id
            WHERE strftime('%m', p.date_added) = strftime('%m', 'now', '-1 month')
            AND strftime('%Y', p.date_added) = strftime('%Y', 'now', '-1 month')
            GROUP BY pt.id
        ) AS subquery
        ORDER BY count_by_name DESC
        LIMIT 1;
    '''
                                           )

    month_focus = database.fetch_data(conn, '''
        SELECT name
            FROM (
                SELECT pt.name, COUNT(p.id) AS count_by_name
                FROM problem_type pt
                LEFT JOIN problems p ON p.typeid = pt.id
                WHERE strftime('%m', p.date_added) = strftime('%m', 'now')
                AND strftime('%Y', p.date_added) = strftime('%Y', 'now')
                GROUP BY pt.id
            ) AS subquery
            ORDER BY count_by_name DESC
            LIMIT 1;
        '''
                                      )
    levels_data = database.fetch_data(conn, "SELECT distinct(p.level), Count(*) from problems p group by p.level")
    status_data = database.fetch_data(conn, "SELECT distinct(p.status), Count(*) from problems p group by p.status")
    types_data = database.fetch_data(conn,
                                     "SELECT distinct(pt.name), Count(p.id) from problem_type pt left join problems p on p.typeid = pt.id group by pt.id")
    companies_data = database.fetch_data(conn, '''
    SELECT c.name AS company_name,
       COALESCE((
           SELECT COUNT(*)
           FROM problems p
           WHERE p.companies LIKE '%' || c.name || '%'
       ), 0) AS count_by_company
    FROM (SELECT DISTINCT name FROM companies) c;''')

    analytics['total_count'] = total_count[0][0]
    analytics['today_count'] = today_count[0][0]
    analytics['prev_month_focus'] = prev_month_focus[0][0] if prev_month_focus and len(
        prev_month_focus) > 0 else "No Information"
    analytics['month_focus'] = month_focus[0][0] if month_focus and len(month_focus) > 0 else "No Information"

    analytics['month_count'] = month_count[0][0]
    analytics['prev_month_count'] = prev_month[0][0]
    analytics['levels'] = [{'level': level, 'slug': create_slug(level), 'count': count} for level, count in levels_data]
    analytics['statuses'] = [{'status': status, 'slug': create_slug(status), 'count': count} for status, count in status_data]
    analytics['types'] = [{'type': type,'slug': create_slug(type), 'count': count} for type, count in types_data]
    analytics['companies'] = [{'company': name, 'slug': create_slug(name), 'count': count} for name, count in companies_data]
    database.close_connection(conn)
    return jsonify({'analytics': analytics})


@app.route('/api/update', methods=['POST'])
def update_system():
    if os.path.exists("codebase.lock"):
        return jsonify({'message': 'sys-update'})
    else:
        threading.Thread(target=updator.init_system, args=()).start()
    return jsonify({'message': 'success'})


@app.route('/api/status', methods=['GET'])
def system_status():
    status = 'success'
    if os.path.exists("codebase.lock"):
        status = 'sys-update'
    return jsonify({'message': status})


def create_slug(input_string):
    # Convert the string to lowercase and replace spaces with hyphens
    slug = input_string.lower().replace(' ', '-')
    # Remove any characters that are not alphanumeric or hyphens
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'\-+', '-', slug)
    # Remove leading and trailing hyphens
    slug = slug.strip('-')
    return slug


'''
def schedule_update():
    logging.info("Running Scheduled Update....")
    updator.init_parent_repo()
    logging.info("Scheduled Update Finished....")


# Schedule the function to run every 2 minutes
schedule.every(2).minutes.do(schedule_update)
'''
