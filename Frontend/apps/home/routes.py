# -*- encoding: utf-8 -*-

from collections import Counter
from datetime import date, datetime, timedelta

from apps import api_client
from apps.home import blueprint
from flask import current_app, flash, redirect, render_template, request, session, url_for
from flask_login import login_required
from jinja2 import TemplateNotFound

SHIFT_TYPES = ('Shift A', 'Shift B', 'Shift C', 'Shift D')
AREA_TYPES = ('Yard', 'Quay Side', 'PMTT', 'Pinning', 'Lash', 'Vessel')
STATUS_TYPES = ('Done', 'On going', 'Not Yet')
USER_ROLES = ('user', 'admin', 'superuser')
OVERDUE_AFTER_DAYS = 7


def _access_token():
    token = session.get('access_token')
    if not token:
        flash('Please sign in again.', 'danger')
    return token


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


@blueprint.route('/index')
@login_required
def index():
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

    total = len(rows)
    done = sum(1 for row in rows if row.get('status') == 'Done')
    ongoing = sum(1 for row in rows if row.get('status') == 'On going')
    not_yet = sum(1 for row in rows if row.get('status') == 'Not Yet')
    latest_deviations = rows[:5]
    active_type_count = sum(1 for option in deviation_type_options if option.get('active', True))
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

    return render_template(
        'home/index.html',
        segment='index',
        stats={
            'total': total,
            'done': done,
            'ongoing': ongoing,
            'not_yet': not_yet,
            'open': len(open_deviations),
            'overdue': len(overdue_deviations),
            'active_types': active_type_count,
        },
        latest_deviations=latest_deviations,
        open_deviations=open_deviations[:6],
        overdue_deviations=overdue_deviations[:6],
        overdue_after_days=OVERDUE_AFTER_DAYS,
        chart_data=chart_data,
        deviation_type_map=deviation_type_map,
        qc_map=qc_map,
        vessel_map=vessel_map,
    )


@blueprint.route('/deviations')
@login_required
def deviations():
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
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        rows = api_client.list_managed_deviation_types(access_token)
    except api_client.BackendAPIError as error:
        rows = []
        flash(str(error), 'danger')

    current_app.logger.info("rendering deviation-types page rows=%s values=%s", len(rows), rows)
    return render_template('home/deviation-types.html', segment='deviation-types', deviation_types=rows)


@blueprint.route('/users')
@login_required
def users():
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
    access_token = _access_token()
    if not access_token:
        return redirect(url_for('authentication_blueprint.login'))

    try:
        api_client.delete_deviation(access_token, deviation_id)
        flash('Deviation deleted.', 'success')
    except api_client.BackendAPIError as error:
        flash(str(error), 'danger')

    return redirect(url_for('home_blueprint.deviations'))


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
