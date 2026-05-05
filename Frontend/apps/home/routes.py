# -*- encoding: utf-8 -*-

from collections import Counter
from datetime import date, datetime, timedelta

from apps import api_client
from apps.home import blueprint
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import login_required

SHIFT_TYPES = ('Shift A', 'Shift B', 'Shift C', 'Shift D')
AREA_TYPES = ('Yard', 'Quay Side', 'PMTT', 'Pinning', 'Lash', 'Vessel')
STATUS_TYPES = ('Done', 'On going', 'Not Yet')
USER_ROLES = ('user', 'admin', 'superuser')
OVERDUE_AFTER_DAYS = 7
DASHBOARD_COLORS = (
    '#2563eb',
    '#16a34a',
    '#f59e0b',
    '#dc2626',
    '#7c3aed',
    '#0f766e',
    '#64748b',
)


# Authentication/session helpers
def _access_token():
    token = session.get('access_token')
    if not token:
        flash('Please sign in again.', 'danger')
    return token


# Shared form option loaders
def _deviation_type_options():
    access_token = _access_token()
    if not access_token:
        return []

    try:
        return api_client.list_deviation_types(access_token)
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')
        return []


def _form_options():
    access_token = _access_token()
    if not access_token:
        return [], [], []

    deviation_type_options = _deviation_type_options()

    try:
        qc_options = api_client.list_qcs(access_token)
    except api_client.BackendAPIError as error:
        qc_options = []
        flash(str(error), 'danger')

    try:
        vessel_options = api_client.list_vessels(access_token)
    except api_client.BackendAPIError as error:
        vessel_options = []
        flash(str(error), 'danger')

    return deviation_type_options, qc_options, vessel_options


# Dashboard data helpers
def _chart_rows(counter, total):
    rows = []
    for label, count in counter.most_common():
        rows.append({
            'label': label,
            'count': count,
            'percent': round((count / total) * 100) if total else 0,
        })
    return rows


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def _selected_dashboard_filters():
    return {
        'date_from': request.args.get('date_from', '').strip(),
        'date_to': request.args.get('date_to', '').strip(),
        'vessel_id': request.args.get('vessel_id', '').strip(),
        'area': request.args.get('area', '').strip(),
        'deviation_type_id': request.args.get('deviation_type_id', '').strip(),
        'status': request.args.get('status', '').strip(),
        'shift': request.args.get('shift', '').strip(),
    }


def _matches_int_filter(value, selected):
    if not selected:
        return True
    try:
        return int(selected) == value
    except (TypeError, ValueError):
        return False


def _filter_dashboard_rows(rows, selected):
    date_from = _parse_date(selected.get('date_from'))
    date_to = _parse_date(selected.get('date_to'))
    filtered = []

    for row in rows:
        row_date = _parse_date(row.get('date'))
        if date_from and (not row_date or row_date < date_from):
            continue
        if date_to and (not row_date or row_date > date_to):
            continue
        if selected.get('area') and row.get('area') != selected['area']:
            continue
        if selected.get('status') and row.get('status') != selected['status']:
            continue
        if selected.get('shift') and row.get('shiftType') != selected['shift']:
            continue
        if not _matches_int_filter(row.get('deviation_type_id'), selected.get('deviation_type_id')):
            continue
        if selected.get('vessel_id'):
            try:
                vessel_id = int(selected['vessel_id'])
            except ValueError:
                continue
            if vessel_id not in (row.get('vessel_ids') or []):
                continue
        filtered.append(row)

    return filtered


def _dashboard_datasets(rows, deviation_type_map, qc_map, vessel_map):
    total = len(rows)
    status_counter = Counter(row.get('status') or 'Unknown' for row in rows)
    area_counter = Counter(row.get('area') or 'Unknown' for row in rows)
    shift_counter = Counter(row.get('shiftType') or 'Unknown' for row in rows)
    qc_counter = Counter(qc_map.get(row.get('qc_id'), row.get('qc_id') or 'Unknown') for row in rows)
    type_counter = Counter(
        deviation_type_map.get(row.get('deviation_type_id'), row.get('deviation_type_id') or 'Unknown')
        for row in rows
    )
    vessel_counter = Counter()

    for row in rows:
        vessel_ids = row.get('vessel_ids') or []
        if not vessel_ids:
            vessel_counter['No vessel'] += 1
            continue
        for vessel_id in vessel_ids:
            vessel_counter[vessel_map.get(vessel_id, vessel_id)] += 1

    return {
        'status': _chart_rows(status_counter, total),
        'area': _chart_rows(area_counter, total),
        'shift': _chart_rows(shift_counter, total),
        'qc': _chart_rows(qc_counter, total),
        'vessel': _chart_rows(vessel_counter, max(sum(vessel_counter.values()), 1)),
        'deviation_type': _chart_rows(type_counter, total),
    }


def _dashboard_pie(rows):
    if not rows:
        return {
            'total': 0,
            'gradient': '#e5e7eb 0 100%',
            'rows': [],
        }

    total = sum(row['count'] for row in rows)
    display_rows = rows[:6]
    other_count = sum(row['count'] for row in rows[6:])
    if other_count:
        display_rows = [*display_rows, {'label': 'Other', 'count': other_count}]

    cursor = 0
    gradient_parts = []
    pie_rows = []

    for index, row in enumerate(display_rows):
        percent = round((row['count'] / total) * 100, 1) if total else 0
        start = cursor
        end = 100 if index == len(display_rows) - 1 else cursor + percent
        color = DASHBOARD_COLORS[index % len(DASHBOARD_COLORS)]
        gradient_parts.append(f'{color} {start}% {end}%')
        pie_rows.append({**row, 'color': color, 'percent': percent})
        cursor = end

    return {
        'total': total,
        'gradient': ', '.join(gradient_parts) if gradient_parts else '#e5e7eb 0 100%',
        'rows': pie_rows,
    }


def _dashboard_pareto(rows):
    if not rows:
        return {'total': 0, 'rows': []}

    total = sum(row['count'] for row in rows)
    max_count = max((row['count'] for row in rows), default=1)
    cumulative = 0
    pareto_rows = []

    for row in rows[:10]:
        cumulative += row['count']
        pareto_rows.append({
            **row,
            'bar_percent': round((row['count'] / max_count) * 100) if max_count else 0,
            'cumulative_percent': round((cumulative / total) * 100) if total else 0,
        })

    return {'total': total, 'rows': pareto_rows}


def _dashboard_cross(rows, label_getter, group_getter):
    label_counter = Counter(label_getter(row) for row in rows)
    group_counter = Counter(group_getter(row) for row in rows)
    labels = [label for label, _ in label_counter.most_common(8)]
    groups = [group for group, _ in group_counter.most_common(6)]
    datasets = []

    for index, group in enumerate(groups):
        datasets.append({
            'label': group,
            'data': [
                sum(
                    1 for row in rows
                    if label_getter(row) == label and group_getter(row) == group
                )
                for label in labels
            ],
            'color': DASHBOARD_COLORS[index % len(DASHBOARD_COLORS)],
        })

    return {'labels': labels, 'datasets': datasets}


def _dashboard_pagination(total_items, page, per_page):
    page_count = max((total_items + per_page - 1) // per_page, 1)
    current_page = min(max(page or 1, 1), page_count)
    start = (current_page - 1) * per_page
    end = start + per_page
    window_start = max(1, current_page - 2)
    window_end = min(page_count, current_page + 2)

    def page_url(page_number):
        args = request.args.to_dict()
        args['page'] = page_number
        return url_for('home_blueprint.index', **args)

    return {
        'page': current_page,
        'per_page': per_page,
        'total': total_items,
        'pages': page_count,
        'start': start,
        'end': end,
        'start_item': start + 1 if total_items else 0,
        'end_item': min(end, total_items),
        'prev_url': page_url(current_page - 1) if current_page > 1 else None,
        'next_url': page_url(current_page + 1) if current_page < page_count else None,
        'page_links': [
            {'number': number, 'url': page_url(number), 'is_current': number == current_page}
            for number in range(window_start, window_end + 1)
        ],
    }


def _dashboard_pivot(rows, row_getter, column_getter, row_heading):
    row_counter = Counter(row_getter(row) for row in rows)
    column_counter = Counter(column_getter(row) for row in rows)
    row_labels = [label for label, _ in row_counter.most_common(8)]
    column_labels = [label for label, _ in column_counter.most_common(7)]
    pivot_rows = []

    for row_label in row_labels:
        counts = []
        total = 0
        for column_label in column_labels:
            count = sum(
                1 for row in rows
                if row_getter(row) == row_label and column_getter(row) == column_label
            )
            counts.append(count)
            total += count
        pivot_rows.append({'label': row_label, 'counts': counts, 'total': total})

    return {
        'row_heading': row_heading,
        'columns': column_labels,
        'rows': sorted(pivot_rows, key=lambda item: item['total'], reverse=True),
    }


def _dashboard_table_rows(rows, deviation_type_map, qc_map, vessel_map):
    table_rows = []
    today = date.today()

    for row in rows:
        row_date = _parse_date(row.get('date'))
        days_open = (today - row_date).days if row_date and row.get('status') != 'Done' else None
        vessel_names = [
            vessel_map.get(vessel_id, str(vessel_id))
            for vessel_id in (row.get('vessel_ids') or [])
        ]
        table_rows.append({
            **row,
            'deviation_type_name': deviation_type_map.get(row.get('deviation_type_id'), 'Deviation'),
            'qc_name': qc_map.get(row.get('qc_id'), row.get('qc_id') or 'Unassigned'),
            'vessel_names': vessel_names,
            'days_open': days_open,
            'is_overdue': days_open is not None and days_open > OVERDUE_AFTER_DAYS,
        })

    return table_rows


@blueprint.route('/index')
@login_required
def index():
    # Dashboard view and overdue/open deviation summary.
    access_token = _access_token()
    rows = []
    deviation_type_options = []
    qc_options = []
    vessel_options = []

    if access_token:
        try:
            rows = api_client.list_deviations(access_token)
        except api_client.BackendAPIError as error:
            flash(str(error), 'danger')

        deviation_type_options = _deviation_type_options()
        try:
            qc_options = api_client.list_qcs(access_token)
        except api_client.BackendAPIError as error:
            flash(str(error), 'danger')
        try:
            vessel_options = api_client.list_vessels(access_token)
        except api_client.BackendAPIError as error:
            flash(str(error), 'danger')

    selected_filters = _selected_dashboard_filters()
    all_rows = rows
    rows = _filter_dashboard_rows(all_rows, selected_filters)
    total = len(rows)
    done = sum(1 for row in rows if row.get('status') == 'Done')
    deviation_type_map = {option['id']: option['name'] for option in deviation_type_options}
    qc_map = {option['id']: option['qcName'] for option in qc_options}
    vessel_map = {
        option['id']: f"{option['name']} - {option['codeVessel']}"
        for option in vessel_options
    }
    open_deviations = [row for row in rows if row.get('status') != 'Done']
    overdue_threshold = date.today() - timedelta(days=OVERDUE_AFTER_DAYS)
    overdue_deviations = [
        row for row in open_deviations
        if (parsed_date := _parse_date(row.get('date'))) and parsed_date < overdue_threshold
    ]
    chart_data = _dashboard_datasets(rows, deviation_type_map, qc_map, vessel_map)
    dashboard_table_rows = _dashboard_table_rows(rows, deviation_type_map, qc_map, vessel_map)
    pagination = _dashboard_pagination(
        len(dashboard_table_rows),
        request.args.get('page', 1, type=int),
        25,
    )
    latest_deviations = dashboard_table_rows[pagination['start']:pagination['end']]
    avg_days_open_values = [
        row['days_open'] for row in dashboard_table_rows
        if row['days_open'] is not None
    ]
    avg_days_open = round(sum(avg_days_open_values) / len(avg_days_open_values), 1) if avg_days_open_values else 0

    return render_template(
        'home/index.html',
        segment='index',
        stats={
            'total': total,
            'done': done,
            'open': len(open_deviations),
            'overdue': len(overdue_deviations),
            'closure_rate': round((done / total) * 100) if total else 0,
            'avg_days_open': avg_days_open,
        },
        latest_deviations=latest_deviations,
        pagination=pagination,
        open_deviations=open_deviations[:6],
        overdue_deviations=overdue_deviations[:6],
        overdue_after_days=OVERDUE_AFTER_DAYS,
        chart_data=chart_data,
        pie_data={
            'status': _dashboard_pie(chart_data['status']),
            'area': _dashboard_pie(chart_data['area']),
            'deviation_type': _dashboard_pie(chart_data['deviation_type']),
        },
        pareto_data={
            'deviation_type': _dashboard_pareto(chart_data['deviation_type']),
            'vessel': _dashboard_pareto(chart_data['vessel']),
            'area': _dashboard_pareto(chart_data['area']),
        },
        cross_data={
            'shift_area': _dashboard_cross(
                rows,
                lambda row: row.get('shiftType') or 'Unknown',
                lambda row: row.get('area') or 'Unknown',
            ),
            'vessel_status': _dashboard_cross(
                rows,
                lambda row: (
                    ', '.join(
                        vessel_map.get(vessel_id, str(vessel_id))
                        for vessel_id in (row.get('vessel_ids') or [])
                    ) or 'No vessel'
                ),
                lambda row: row.get('status') or 'Unknown',
            ),
        },
        pivot_data={
            'shift_area': _dashboard_pivot(
                rows,
                lambda row: row.get('shiftType') or 'Unknown',
                lambda row: row.get('area') or 'Unknown',
                'Shift',
            ),
            'area_type': _dashboard_pivot(
                rows,
                lambda row: row.get('area') or 'Unknown',
                lambda row: deviation_type_map.get(row.get('deviation_type_id'), row.get('deviation_type_id') or 'Unknown'),
                'Area',
            ),
            'shift_status': _dashboard_pivot(
                rows,
                lambda row: row.get('shiftType') or 'Unknown',
                lambda row: row.get('status') or 'Unknown',
                'Shift',
            ),
        },
        selected_filters=selected_filters,
        filter_options={
            'areas': sorted({row.get('area') for row in all_rows if row.get('area')} | set(AREA_TYPES)),
            'statuses': sorted({row.get('status') for row in all_rows if row.get('status')} | set(STATUS_TYPES)),
            'shifts': sorted({row.get('shiftType') for row in all_rows if row.get('shiftType')} | set(SHIFT_TYPES)),
            'deviation_types': deviation_type_options,
            'vessels': vessel_options,
        },
        deviation_type_map=deviation_type_map,
        qc_map=qc_map,
        vessel_map=vessel_map,
    )


@blueprint.route('/deviations')
@login_required
def deviations():
    # Deviation list view with reference-data maps for table display and filters.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        rows = api_client.list_deviations(access_token)
    except api_client.BackendAPIError as error:
        rows = []
        flash(str(error), 'danger')

    deviation_type_options = _deviation_type_options()
    deviation_type_map = {option['id']: option['name'] for option in deviation_type_options}
    try:
        qc_options = api_client.list_qcs(access_token)
    except api_client.BackendAPIError:
        qc_options = []
    qc_map = {option['id']: option['qcName'] for option in qc_options}
    try:
        vessel_options = api_client.list_vessels(access_token)
    except api_client.BackendAPIError:
        vessel_options = []
    vessel_map = {
        option['id']: f"{option['name']} - {option['codeVessel']}"
        for option in vessel_options
    }
    vessel_name_map = {option['id']: option['name'] for option in vessel_options}
    vessel_code_map = {option['id']: option['codeVessel'] for option in vessel_options}
    vessel_search_map = {
        option['id']: f"{option['name']} {option['codeVessel']}"
        for option in vessel_options
    }
    return render_template(
        'home/deviations.html',
        segment='deviations',
        deviations=rows,
        deviation_type_options=deviation_type_options,
        deviation_type_map=deviation_type_map,
        qc_options=qc_options,
        qc_map=qc_map,
        vessel_options=vessel_options,
        vessel_map=vessel_map,
        vessel_name_map=vessel_name_map,
        vessel_code_map=vessel_code_map,
        vessel_search_map=vessel_search_map,
        shift_options=SHIFT_TYPES,
        area_options=AREA_TYPES,
        status_options=STATUS_TYPES,
    )


@blueprint.route('/deviation-types')
@login_required
def deviation_types():
    # Deviation type administration list.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        rows = api_client.list_managed_deviation_types(access_token)
    except api_client.BackendAPIError as error:
        rows = []
        flash(str(error), 'danger')

    return render_template('home/deviation-types.html', segment='deviation-types', deviation_types=rows)


@blueprint.route('/users')
@login_required
def users():
    # User administration list.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        rows = api_client.list_users(access_token)
    except api_client.BackendAPIError as error:
        rows = []
        flash(str(error), 'danger')

    return render_template(
        'home/users.html',
        segment='users',
        users=rows,
        role_options=USER_ROLES,
        shift_options=SHIFT_TYPES,
    )


@blueprint.route('/vessels')
@login_required
def vessels():
    # Vessel directory list.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        rows = api_client.list_vessels(access_token)
    except api_client.BackendAPIError as error:
        rows = []
        flash(str(error), 'danger')

    return render_template('home/vessels.html', segment='vessels', vessels=rows)


@blueprint.route('/vessels/create', methods=['GET', 'POST'])
@login_required
def vessel_create():
    # Vessel create form and submission handler.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    if request.method == 'POST':
        payload = {
            'name': request.form.get('name'),
            'codeVessel': request.form.get('codeVessel'),
        }
        payload = {key: value for key, value in payload.items() if value not in (None, '')}

        try:
            vessel = api_client.create_vessel(access_token, payload)
        except api_client.BackendAPIError as error:
            flash(str(error), 'danger')
        else:
            flash('Vessel created.', 'success')
            return redirect(url_for('home_blueprint.vessel_detail', vessel_id=vessel['id']))

    return render_template('home/vessel-create.html', segment='vessels')


@blueprint.route('/vessels/<int:vessel_id>')
@login_required
def vessel_detail(vessel_id):
    # Vessel detail view.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        vessel = api_client.get_vessel(access_token, vessel_id)
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')
        return redirect(url_for('home_blueprint.vessels'))

    return render_template('home/vessel-detail.html', segment='vessels', vessel=vessel)


@blueprint.route('/vessels/<int:vessel_id>/edit', methods=['GET', 'POST'])
@login_required
def vessel_edit(vessel_id):
    # Vessel edit form and submission handler.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        vessel = api_client.get_vessel(access_token, vessel_id)
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')
        return redirect(url_for('home_blueprint.vessels'))

    if request.method == 'POST':
        payload = {
            'name': request.form.get('name'),
            'codeVessel': request.form.get('codeVessel'),
        }
        payload = {key: value for key, value in payload.items() if value not in (None, '')}

        try:
            api_client.update_vessel(access_token, vessel_id, payload)
        except api_client.BackendAPIError as error:
            flash(str(error), 'danger')
        else:
            flash('Vessel updated.', 'success')
            return redirect(url_for('home_blueprint.vessel_detail', vessel_id=vessel_id))

    return render_template('home/vessel-edit.html', segment='vessels', vessel=vessel)


@blueprint.route('/users/create', methods=['POST'])
@login_required
def user_create():
    # Admin user creation handler.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        api_client.create_user(
            access_token,
            request.form.get('firstName'),
            request.form.get('lastName'),
            request.form.get('email'),
            request.form.get('password'),
            request.form.get('role') or 'user',
            request.form.get('shift') or None,
            request.form.get('active') == 'on',
        )
        flash('User created.', 'success')
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')

    return redirect(url_for('home_blueprint.users'))


@blueprint.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
def user_edit(user_id):
    # Admin user update handler.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    payload = {
        'firstName': request.form.get('firstName'),
        'lastName': request.form.get('lastName'),
        'email': request.form.get('email'),
        'role': request.form.get('role'),
    }
    if str(user_id) == str(session.get('user', {}).get('id')):
        payload['active'] = True
    else:
        payload['active'] = request.form.get('active') == 'on'
    password = request.form.get('password')
    if password:
        payload['password'] = password
    payload = {key: value for key, value in payload.items() if value not in (None, '')}
    payload['shift'] = request.form.get('shift') or None

    try:
        api_client.update_user(access_token, user_id, payload)
        flash('User updated.', 'success')
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')

    return redirect(url_for('home_blueprint.users'))


@blueprint.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def user_delete(user_id):
    # Admin user deletion handler.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        api_client.delete_user(access_token, user_id)
        flash('User deleted.', 'success')
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')

    return redirect(url_for('home_blueprint.users'))


@blueprint.route('/deviation-types/create', methods=['POST'])
@login_required
def deviation_type_create():
    # Deviation type creation handler.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    payload = {
        'name': request.form.get('name'),
        'active': request.form.get('active') == 'on',
    }

    try:
        api_client.create_deviation_type(access_token, payload)
        flash('Deviation type created.', 'success')
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')

    return redirect(url_for('home_blueprint.deviation_types'))


@blueprint.route('/deviation-types/<int:deviation_type_id>/edit', methods=['POST'])
@login_required
def deviation_type_edit(deviation_type_id):
    # Deviation type update handler.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    payload = {
        'name': request.form.get('name'),
        'active': request.form.get('active') == 'on',
    }

    try:
        api_client.update_deviation_type(access_token, deviation_type_id, payload)
        flash('Deviation type updated.', 'success')
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')

    return redirect(url_for('home_blueprint.deviation_types'))


@blueprint.route('/deviation-types/<int:deviation_type_id>/delete', methods=['POST'])
@login_required
def deviation_type_delete(deviation_type_id):
    # Deviation type deletion handler.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        api_client.delete_deviation_type(access_token, deviation_type_id)
        flash('Deviation type deleted.', 'success')
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')

    return redirect(url_for('home_blueprint.deviation_types'))


@blueprint.route('/deviations/create', methods=['GET', 'POST'])
@login_required
def deviation_create():
    # Deviation create form and submission handler.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    if request.method == 'POST':
        payload = {
            'date': request.form.get('date'),
            'shiftType': request.form.get('shiftType'),
            'area': request.form.get('area'),
            'status': request.form.get('status'),
            'description': request.form.get('description'),
            'deviation_type_id': request.form.get('deviation_type_id', type=int),
            'qc_id': request.form.get('qc_id', type=int),
            'vessel_ids': [int(value) for value in request.form.getlist('vessel_ids') if value],
        }
        payload = {key: value for key, value in payload.items() if value not in (None, '')}

        try:
            deviation = api_client.create_deviation(access_token, payload)
        except api_client.BackendAPIError as error:
            flash(str(error), 'danger')
        else:
            flash('Deviation created.', 'success')
            return redirect(url_for('home_blueprint.deviation_detail', deviation_id=deviation['id']))

    deviation_type_options, qc_options, vessel_options = _form_options()
    return render_template(
        'home/deviation-create.html',
        segment='deviations',
        shift_options=SHIFT_TYPES,
        area_options=AREA_TYPES,
        status_options=STATUS_TYPES,
        deviation_type_options=deviation_type_options,
        qc_options=qc_options,
        vessel_options=vessel_options,
    )


@blueprint.route('/deviations/<int:deviation_id>')
@login_required
def deviation_detail(deviation_id):
    # Deviation detail view, including audit trail.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        deviation = api_client.get_deviation(access_token, deviation_id)
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')
        return redirect(url_for('home_blueprint.deviations'))

    try:
        audits = api_client.list_deviation_audits(access_token, deviation_id)
    except api_client.BackendAPIError as error:
        audits = []
        flash(str(error), 'danger')

    deviation_type_options = _deviation_type_options()
    deviation_type_map = {option['id']: option['name'] for option in deviation_type_options}
    try:
        qc_options = api_client.list_qcs(access_token)
    except api_client.BackendAPIError:
        qc_options = []
    qc_map = {option['id']: option['qcName'] for option in qc_options}
    try:
        vessel_options = api_client.list_vessels(access_token)
    except api_client.BackendAPIError:
        vessel_options = []
    vessel_map = {option['id']: option['name'] for option in vessel_options}
    return render_template(
        'home/deviation-detail.html',
        segment='deviations',
        deviation=deviation,
        audits=audits,
        deviation_type_map=deviation_type_map,
        qc_map=qc_map,
        vessel_map=vessel_map,
    )


@blueprint.route('/deviations/<int:deviation_id>/edit', methods=['GET', 'POST'])
@login_required
def deviation_edit(deviation_id):
    # Deviation edit form and submission handler.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        deviation = api_client.get_deviation(access_token, deviation_id)
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')
        return redirect(url_for('home_blueprint.deviations'))

    if request.method == 'POST':
        payload = {
            'date': request.form.get('date'),
            'shiftType': request.form.get('shiftType'),
            'area': request.form.get('area'),
            'status': request.form.get('status'),
            'description': request.form.get('description'),
            'deviation_type_id': request.form.get('deviation_type_id', type=int),
            'qc_id': request.form.get('qc_id', type=int),
            'vessel_ids': [int(value) for value in request.form.getlist('vessel_ids') if value],
        }
        payload = {key: value for key, value in payload.items() if value not in (None, '')}

        try:
            api_client.update_deviation(access_token, deviation_id, payload)
        except api_client.BackendAPIError as error:
            flash(str(error), 'danger')
        else:
            flash('Deviation updated.', 'success')
            return redirect(url_for('home_blueprint.deviation_detail', deviation_id=deviation_id))

    deviation_type_options, qc_options, vessel_options = _form_options()
    return render_template(
        'home/deviation-edit.html',
        segment='deviations',
        deviation=deviation,
        shift_options=SHIFT_TYPES,
        area_options=AREA_TYPES,
        status_options=STATUS_TYPES,
        deviation_type_options=deviation_type_options,
        qc_options=qc_options,
        vessel_options=vessel_options,
    )


@blueprint.route('/deviations/<int:deviation_id>/delete', methods=['POST'])
@login_required
def deviation_delete(deviation_id):
    # Deviation deletion handler.
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        api_client.delete_deviation(access_token, deviation_id)
        flash('Deviation deleted.', 'success')
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')

    return redirect(url_for('home_blueprint.deviations'))


@blueprint.route('/notifications')
@login_required
def notifications():
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        rows = api_client.list_notifications(access_token)
    except api_client.BackendAPIError as error:
        rows = []
        flash(str(error), 'danger')

    return render_template('home/notifications.html', segment='notifications', notifications=rows)


@blueprint.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def notification_read(notification_id):
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    deviation_id = request.form.get('deviation_id', type=int)
    try:
        api_client.mark_notification_read(access_token, notification_id)
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')
        return redirect(url_for('home_blueprint.notifications'))

    if deviation_id:
        return redirect(url_for('home_blueprint.deviation_detail', deviation_id=deviation_id))
    return redirect(url_for('home_blueprint.notifications'))


@blueprint.route('/notifications/read-all', methods=['POST'])
@login_required
def notifications_read_all():
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        api_client.mark_all_notifications_read(access_token)
        flash('Notifications marked as read.', 'success')
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')

    return redirect(url_for('home_blueprint.notifications'))
