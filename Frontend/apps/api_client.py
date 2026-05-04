# -*- encoding: utf-8 -*-

import requests
from flask import current_app
from requests import RequestException


class BackendAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


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


def _raise_for_error(response):
    if response.status_code >= 400:
        raise BackendAPIError(_error_message(response), response.status_code)


def _auth_headers(access_token):
    return {'Authorization': f'Bearer {access_token}'}


def _log_response(method, url, response):
    current_app.logger.info(
        "Backend API %s %s -> %s body=%s",
        method,
        url,
        response.status_code,
        response.text[:500],
    )


def _request(method, path, access_token=None, json=None):
    url = f'{_base_url()}{path}'
    headers = _auth_headers(access_token) if access_token else None
    try:
        response = requests.request(method, url, json=json, headers=headers, timeout=10)
    except RequestException as error:
        current_app.logger.exception("Backend API %s %s failed", method, url)
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
    _log_response(method, url, response)
    return response


def login(email, password):
    try:
        response = requests.post(
            f'{_base_url()}/auth/login',
            json={'email': email, 'password': password},
            timeout=10,
        )
    except RequestException as error:
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
    _raise_for_error(response)
    return response.json()


def get_current_user(access_token):
    try:
        response = requests.get(
            f'{_base_url()}/auth/me',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
    except RequestException as error:
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
    _raise_for_error(response)
    return response.json()


def bootstrap_admin(first_name, last_name, email, password):
    try:
        response = requests.post(
            f'{_base_url()}/auth/bootstrap-admin',
            json={
                'firstName': first_name,
                'lastName': last_name,
                'email': email,
                'password': password,
            },
            timeout=10,
        )
    except RequestException as error:
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
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

    try:
        response = requests.post(
            f'{_base_url()}/auth/register',
            json=payload,
            timeout=10,
        )
    except RequestException as error:
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
    _raise_for_error(response)
    return response.json()


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

    try:
        response = requests.post(
            f'{_base_url()}/users',
            json=payload,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
    except RequestException as error:
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
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


def list_qcs(access_token):
    try:
        response = requests.get(
            f'{_base_url()}/qcs',
            headers=_auth_headers(access_token),
            timeout=10,
        )
    except RequestException as error:
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
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


def list_deviations(access_token):
    try:
        response = requests.get(
            f'{_base_url()}/deviations',
            headers=_auth_headers(access_token),
            timeout=10,
        )
    except RequestException as error:
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
    _raise_for_error(response)
    return response.json()


def create_deviation(access_token, payload):
    try:
        response = requests.post(
            f'{_base_url()}/deviations',
            json=payload,
            headers=_auth_headers(access_token),
            timeout=10,
        )
    except RequestException as error:
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
    _raise_for_error(response)
    return response.json()


def get_deviation(access_token, deviation_id):
    try:
        response = requests.get(
            f'{_base_url()}/deviations/{deviation_id}',
            headers=_auth_headers(access_token),
            timeout=10,
        )
    except RequestException as error:
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
    _raise_for_error(response)
    return response.json()


def list_deviation_audits(access_token, deviation_id):
    response = _request('GET', f'/deviations/{deviation_id}/audits', access_token=access_token)
    _raise_for_error(response)
    return response.json()


def update_deviation(access_token, deviation_id, payload):
    try:
        response = requests.patch(
            f'{_base_url()}/deviations/{deviation_id}',
            json=payload,
            headers=_auth_headers(access_token),
            timeout=10,
        )
    except RequestException as error:
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
    _raise_for_error(response)
    return response.json()


def delete_deviation(access_token, deviation_id):
    try:
        response = requests.delete(
            f'{_base_url()}/deviations/{deviation_id}',
            headers=_auth_headers(access_token),
            timeout=10,
        )
    except RequestException as error:
        raise BackendAPIError(f'Could not reach backend API: {error}') from error
    _raise_for_error(response)
