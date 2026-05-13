# -*- encoding: utf-8 -*-
from flask import flash, render_template, redirect, request, session, url_for
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from apps import api_client, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import SessionUser

ALLOWED_EMAIL_DOMAIN = '@apmterminals.com'


@blueprint.app_errorhandler(api_client.BackendUnauthorized)
def backend_unauthorized(error):
    flash(str(error), 'warning')
    return redirect(url_for('authentication_blueprint.login'))


# Default entry point
@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))


# Login flow
@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:
        email = request.form['username']
        password = request.form['password']

        if not api_client.backend_enabled():
            return render_template(
                'accounts/login.html',
                msg='Backend API is not configured yet.',
                form=login_form,
            )

        try:
            token = api_client.login(email, password)
            profile = api_client.get_current_user(token['access_token'])
        except api_client.BackendAPIError as error:
            return render_template('accounts/login.html', msg=str(error), form=login_form)

        session['access_token'] = token['access_token']
        session['user'] = profile
        login_user(SessionUser(
            user_id=profile['id'],
            email=profile['email'],
            first_name=profile.get('firstName', ''),
            last_name=profile.get('lastName', ''),
            role=profile.get('role', 'user'),
            shift=profile.get('shift'),
            active=profile.get('active', True),
            access_token=token['access_token'],
        ))
        return redirect(url_for('home_blueprint.index'))

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))


# Registration and pending approval flow
@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:
        if not create_account_form.validate():
            first_error = next(
                (messages[0] for messages in create_account_form.errors.values() if messages),
                'Please check the account form and try again.',
            )
            return render_template(
                'accounts/register.html',
                msg=first_error,
                success=False,
                form=create_account_form,
            )

        if not api_client.backend_enabled():
            return render_template(
                'accounts/register.html',
                msg='Backend API is not configured yet.',
                success=False,
                form=create_account_form,
            )

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form.get('confirm_password', '')
        shift = request.form.get('shift') or None

        if not email.endswith(ALLOWED_EMAIL_DOMAIN):
            return render_template(
                'accounts/register.html',
                msg=f'Email must use {ALLOWED_EMAIL_DOMAIN}.',
                success=False,
                form=create_account_form,
            )

        if password != confirm_password:
            return render_template(
                'accounts/register.html',
                msg='Passwords must match.',
                success=False,
                form=create_account_form,
            )

        try:
            if current_user.is_authenticated and session.get('access_token'):
                api_client.create_user(session['access_token'], first_name, last_name, email, password, shift=shift)
                message = 'User created successfully. They can now log in.'
            else:
                try:
                    api_client.bootstrap_admin(first_name, last_name, email, password)
                    message = 'Admin created successfully. You can now log in.'
                except api_client.BackendAPIError as bootstrap_error:
                    if bootstrap_error.status_code != 409:
                        raise
                    api_client.register_pending_user(first_name, last_name, email, password, shift)
                    message = 'Account request submitted. An administrator must activate your account before you can log in.'
        except api_client.BackendAPIError as error:
            return render_template(
                'accounts/register.html',
                msg=str(error),
                success=False,
                form=create_account_form,
            )

        return render_template(
            'accounts/register.html',
            msg=message,
            success=True,
            form=create_account_form,
        )

    else:
        return render_template('accounts/register.html', form=create_account_form)


# Logout flow
@blueprint.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('authentication_blueprint.login')) 


# Error and unauthorized handlers
@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('authentication_blueprint.login'))


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
