# -*- encoding: utf-8 -*-

import requests
from flask import current_app, session
from flask_login import logout_user
from requests import RequestException


class BackendAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class BackendUnauthorized(Exception):
    pass


# Backend request helpers
def _base_url():
    return current_app.config.get('BACKEND_API_URL', '').rstrip('/')


def backend_enabled():
    return bool(_base_url())


def _error_message(response):
    try:
        payload = response.json()
    except ValueError:
        return response.text or 'Backend API request failed'

    detail = payload.get('detail') if isinstance(payload, dict) else None
    if isinstance(detail, list):
        return '; '.join(item.get('msg', str(item)) for item in detail)
    return detail or str(payload)


def _raise_for_error(response, redirect_on_unauthorized=True):
    if response.status_code == 401 and redirect_on_unauthorized:
        logout_user()
        session.clear()
        raise BackendUnauthorized('Your session expired. Please sign in again.')

    if response.status_code >= 400:
        raise BackendAPIError(_error_message(response), response.status_code)


def _auth_headers(access_token):
    return {'Authorization': f'Bearer {access_token}'}


def _log_response(method, path, response):
    current_app.logger.info(
        "Backend API %s %s -> %s",
        method,
        path,
        response.status_code,
    )


def _request(method, path, access_token=None, json=None):
    url = f'{_base_url()}{path}'
    headers = _auth_headers(access_token) if access_token else None
    try:
        response = requests.request(method, url, json=json, headers=headers, timeout=10)
    except RequestException as error:
        current_app.logger.exception("Backend API %s %s failed", method, path)
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
    _log_response(method, path, response)
    return response


# Authentication API
def login(email, password):
    response = _request('POST', '/auth/login', json={'email': email, 'password': password})
    _raise_for_error(response, redirect_on_unauthorized=False)
    return response.json()


def get_current_user(access_token):
    response = _request('GET', '/auth/me', access_token=access_token)
    _raise_for_error(response)
    return response.json()


def bootstrap_admin(first_name, last_name, email, password):
    response = _request(
        'POST',
        '/auth/bootstrap-admin',
        json={
            'firstName': first_name,
            'lastName': last_name,
            'email': email,
            'password': password,
        },
    )
    _raise_for_error(response)
    return response.json()


def register_pending_user(first_name, last_name, email, password, shift=None):
    payload = {
        'firstName': first_name,
        'lastName': last_name,
        'email': email,
        'password': password,
    }
    if shift:
        payload['shift'] = shift

    response = _request('POST', '/auth/register', json=payload)
    _raise_for_error(response)
    return response.json()


# User administration API
def create_user(access_token, first_name, last_name, email, password, role='user', shift=None, active=True):
    payload = {
        'firstName': first_name,
        'lastName': last_name,
        'email': email,
        'password': password,
        'role': role,
        'active': active,
    }
    if shift:
        payload['shift'] = shift

    response = _request('POST', '/users', access_token=access_token, json=payload)
    _raise_for_error(response)
    return response.json()


def list_users(access_token):
    response = _request('GET', '/users', access_token=access_token)
    _raise_for_error(response)
    return response.json()


def get_user(access_token, user_id):
    response = _request('GET', f'/users/{user_id}', access_token=access_token)
    _raise_for_error(response)
    return response.json()


def update_user(access_token, user_id, payload):
    response = _request('PATCH', f'/users/{user_id}', access_token=access_token, json=payload)
    _raise_for_error(response)
    return response.json()


def delete_user(access_token, user_id):
    response = _request('DELETE', f'/users/{user_id}', access_token=access_token)
    _raise_for_error(response)


# Deviation type API
def list_deviation_types(access_token):
    response = _request('GET', '/deviation-types', access_token=access_token)
    _raise_for_error(response)
    return response.json()


def list_managed_deviation_types(access_token):
    response = _request('GET', '/deviation-types/manage', access_token=access_token)
    if response.status_code == 404:
        current_app.logger.warning("Backend API /deviation-types/manage returned 404; falling back to /deviation-types")
        return list_deviation_types(access_token)
    _raise_for_error(response)
    return response.json()


def create_deviation_type(access_token, payload):
    response = _request('POST', '/deviation-types', access_token=access_token, json=payload)
    _raise_for_error(response)
    return response.json()


def update_deviation_type(access_token, deviation_type_id, payload):
    response = _request('PATCH', f'/deviation-types/{deviation_type_id}', access_token=access_token, json=payload)
    _raise_for_error(response)
    return response.json()


def delete_deviation_type(access_token, deviation_type_id):
    response = _request('DELETE', f'/deviation-types/{deviation_type_id}', access_token=access_token)
    _raise_for_error(response)


# Reference data API
def list_qcs(access_token):
    response = _request('GET', '/qcs', access_token=access_token)
    _raise_for_error(response)
    return response.json()


def list_vessels(access_token):
    response = _request('GET', '/vessels', access_token=access_token)
    _raise_for_error(response)
    return response.json()


def create_vessel(access_token, payload):
    response = _request('POST', '/vessels', access_token=access_token, json=payload)
    _raise_for_error(response)
    return response.json()


def get_vessel(access_token, vessel_id):
    response = _request('GET', f'/vessels/{vessel_id}', access_token=access_token)
    _raise_for_error(response)
    return response.json()


def update_vessel(access_token, vessel_id, payload):
    response = _request('PATCH', f'/vessels/{vessel_id}', access_token=access_token, json=payload)
    _raise_for_error(response)
    return response.json()


# Deviation API
def list_deviations(access_token):
    rows = []
    page = 1
    per_page = 200

    while True:
        response = _request('GET', f'/deviations?page={page}&per_page={per_page}', access_token=access_token)
        _raise_for_error(response)
        payload = response.json()

        if isinstance(payload, list):
            return payload

        rows.extend(payload.get('items', []))
        if page >= payload.get('pages', 1):
            return rows
        page += 1


def create_deviation(access_token, payload):
    response = _request('POST', '/deviations', access_token=access_token, json=payload)
    _raise_for_error(response)
    return response.json()


def get_deviation(access_token, deviation_id):
    response = _request('GET', f'/deviations/{deviation_id}', access_token=access_token)
    _raise_for_error(response)
    return response.json()


def list_deviation_audits(access_token, deviation_id):
    response = _request('GET', f'/deviations/{deviation_id}/audits', access_token=access_token)
    _raise_for_error(response)
    return response.json()


def update_deviation(access_token, deviation_id, payload):
    response = _request('PATCH', f'/deviations/{deviation_id}', access_token=access_token, json=payload)
    _raise_for_error(response)
    return response.json()


def delete_deviation(access_token, deviation_id):
    response = _request('DELETE', f'/deviations/{deviation_id}', access_token=access_token)
    _raise_for_error(response)


# Notification API
def list_notifications(access_token):
    response = _request('GET', '/notifications', access_token=access_token)
    _raise_for_error(response)
    return response.json()


def unread_notification_count(access_token):
    response = _request('GET', '/notifications/unread-count', access_token=access_token)
    _raise_for_error(response)
    return response.json().get('unread', 0)


def mark_notification_read(access_token, notification_id):
    response = _request('PATCH', f'/notifications/{notification_id}/read', access_token=access_token)
    _raise_for_error(response)
    return response.json()


def mark_all_notifications_read(access_token):
    response = _request('PATCH', '/notifications/read-all', access_token=access_token)
    _raise_for_error(response)
    return response.json()
