# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import Flask
from flask import flash
from flask import redirect
from flask import request
from flask import session
from flask import url_for
from flask_login import LoginManager
from flask_login import current_user
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from importlib import import_module


login_manager = LoginManager()
csrf = CSRFProtect()


# Flask extension registration
def register_extensions(app):
    login_manager.init_app(app)
    csrf.init_app(app)


# Application blueprint registration
def register_blueprints(app):
    for module_name in ('authentication', 'home'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def register_context_processors(app):
    @app.context_processor
    def inject_notifications():
        if not current_user.is_authenticated or current_user.role not in ('admin', 'superuser'):
            return {'app_notifications': [], 'app_unread_notifications': 0}

        access_token = session.get('access_token')
        if not access_token:
            return {'app_notifications': [], 'app_unread_notifications': 0}

        from apps import api_client

        try:
            notifications = api_client.list_notifications(access_token)
            unread = api_client.unread_notification_count(access_token)
        except api_client.BackendAPIError:
            notifications = []
            unread = 0

        return {
            'app_notifications': notifications[:5],
            'app_unread_notifications': unread,
        }


def register_error_handlers(app):
    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        flash('The form expired or could not be verified. Please try again.', 'warning')
        return redirect(request.referrer or url_for('authentication_blueprint.login'))


# Flask application factory
def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    register_context_processors(app)
    register_error_handlers(app)
    return app
