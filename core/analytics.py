from datetime import timedelta

from sqlalchemy import func
from models import *
import database_utility as database


def get_analytics():
    analytics = {}

    # Get current month's date
    current_month_date = datetime.now().replace(day=1)
    # Get previous month's date
    prev_month_date = (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1)

    # Connect to the database
    conn = database.create_connection()

    # Total problem count
    total_count = conn.query(func.count(Problem.id)).filter(Problem.include_count == True).scalar()

    # Problem count for today
    today_count = today_count_query(conn)

    # Problem count for current month
    month_count = month_count_query(conn, current_month_date)

    # Problem count for previous month
    prev_month_count = month_count_query(conn, prev_month_date)

    # Problem type with maximum count for previous month
    prev_month_focus = month_focus_query(conn, prev_month_date)

    # Problem type with maximum count for current month
    month_focus = month_focus_query(conn, current_month_date)

    # Problem count by level
    levels_data = level_count_query(conn)

    # Problem count by status
    status_data = status_count_query(conn)

    # Problem count by type
    types_data = types_count_query(conn)

    # Problem count by company
    companies_data = company_count_query(conn)

    # Problem count by relevance
    relevance_data = relevance_query(conn)

    # Populate the analytics dictionary
    analytics['total_count'] = total_count
    analytics['today_count'] = today_count
    analytics['prev_month_focus'] = prev_month_focus or "No Information"
    analytics['month_focus'] = month_focus or "No Information"
    analytics['month_count'] = month_count
    analytics['prev_month_count'] = prev_month_count
    analytics['levels'] = [{'level': level, 'slug': utility.create_slug(level), 'count': count} for level, count in
                           levels_data]
    analytics['statuses'] = [{'status': status, 'slug': utility.create_slug(status), 'count': count} for status, count
                             in status_data]
    analytics['types'] = [{'type': type, 'slug': utility.create_slug(type), 'count': count} for type, count in
                          types_data]
    analytics['companies'] = [{'company': name, 'slug': utility.create_slug(name), 'count': count} for name, count in
                              companies_data]
    analytics['relevance'] = [{'name': name, 'slug': utility.create_slug(name), 'count': count} for name, count in
                              relevance_data]
    analytics['trackers'] = get_trackers_count_query(conn)

    analytics['playlists'] = get_playlist_data(conn)

    analytics['sheets'] = get_sheet_data(conn)
    # Close the database connection
    database.close_connection(conn)

    # Return the analytics dictionary as JSON response
    return analytics


def get_playlist_data(conn):
    running_playlists = []
    completed_playlists = []

    playlists = conn.query(Playlist.uid, Playlist.title, Playlist.completed_items_count, Playlist.total_items_count).all()
    for playlist in playlists:
        uid, name, completed_items, total_items = playlist
        percent = int((completed_items / total_items) * 100)
        if 0 < percent < 100:
            running_playlists.append({
                'id': uid,
                'name': name,
                'percent': percent
            })
        if percent == 100:
            completed_playlists.append({
                'id': uid,
                'name': name,
                'percent': percent
            })

    return {
        'in-progress': running_playlists,
        'completed': completed_playlists
    }


def get_sheet_data(conn):
    running_sheets = []
    completed_sheets = []

    sheets = conn.query(Sheet.uid, Sheet.name, Sheet.completed_items_count, Sheet.total_items_count).all()
    for sheet in sheets:
        uid, name, completed_items, total_items = sheet
        percent = int((completed_items / total_items) * 100)
        if 0 < percent < 100:
            running_sheets.append({
                'id': uid,
                'name': name,
                'percent': percent
            })
        if percent == 100:
            completed_sheets.append({
                'id': uid,
                'name': name,
                'percent': percent
            })

    return {
        'in-progress': running_sheets,
        'completed': completed_sheets
    }


def get_trackers_count_query(conn):
    trackers_count = []
    all_trackers = conn.query(Tracker.name, Tracker.level).all()
    for tracker in all_trackers:
        total_count = 0
        level_array = []
        name = tracker[0]
        levels = str(tracker[1]).split(",")

        for level in levels:
            count = (conn.query(func.count(Problem.id)).filter(
                Problem.include_count == True, Problem.type.has(name=name), Problem.level == level.strip()).all())[0][0]
            level_array.append({
                'name': level,
                'count': count
            })
            total_count += int(count)
        if total_count > 0:
            level_array.append({
                'name': 'Total',
                'count': total_count
            })

        trackers_count.append({
            'name': tracker[0],
            'counts': level_array if total_count > 0 else []
        })
    return trackers_count


def relevance_query(conn):
    relevance_data = []
    all_problems = conn.query(Problem.name, Problem.companies).filter(Problem.include_count == True).all()
    for name, companies in all_problems:
        company_array = str(companies).split(":")
        if len(company_array) > 5:
            relevance_data.append((name, len(company_array)))
    # Sort relevance data by count in descending order
    relevance_data = sorted(relevance_data, key=lambda x: x[1], reverse=True)
    return relevance_data


def company_count_query(conn):
    return conn.query(Company.name, func.coalesce(func.count(Problem.id), 0)).outerjoin(Problem,
                                                                                        Problem.companies.like(
                                                                                            '%' + Company.name + '%')).filter(
        Problem.include_count == True).group_by(
        Company.name).all()


def types_count_query(conn):
    return conn.query(ProblemType.name, func.count(Problem.id)).outerjoin(Problem).filter(
        Problem.include_count == True).group_by(ProblemType.id).all()


def status_count_query(conn):
    return conn.query(Problem.status, func.count(Problem.id)).filter(Problem.include_count == True).group_by(
        Problem.status).all()


def level_count_query(conn):
    return conn.query(Problem.level, func.count(Problem.id)).filter(Problem.include_count == True).group_by(
        Problem.level).all()


def month_focus_query(conn, prev_month_date):
    return conn.query(ProblemType.name).join(Problem).filter(
        Problem.include_count == True,
        func.strftime('%m', Problem.date_added) == prev_month_date.strftime('%m'),
        func.strftime('%Y', Problem.date_added) == prev_month_date.strftime('%Y')).group_by(Problem.typeid).order_by(
        func.count(Problem.id).desc()).limit(1).scalar()


def month_count_query(conn, current_month_date):
    return conn.query(func.count(Problem.id)).filter(
        func.strftime('%m', Problem.date_added) == current_month_date.strftime('%m'),
        func.strftime('%Y', Problem.date_added) == current_month_date.strftime('%Y'),
        Problem.include_count == True
    ).scalar()


def today_count_query(conn):
    return conn.query(func.count(Problem.id)).filter(
        func.date(Problem.date_added) == func.date('now', 'localtime'),
        Problem.include_count == True
    ).scalar()
