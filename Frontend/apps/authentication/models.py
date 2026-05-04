from flask_login import UserMixin
from flask import session

from apps import login_manager

class SessionUser(UserMixin):
    def __init__(self, user_id, email, first_name='', last_name='', role='user', shift=None, active=True, access_token=None):
        self.id = str(user_id)
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.shift = shift
        self.active = active
        self.access_token = access_token

@login_manager.user_loader
def user_loader(user_id):
    user = session.get('user')
    if not user or str(user.get('id')) != str(user_id):
        return None
    return SessionUser(
        user_id=user['id'],
        email=user.get('email', ''),
        first_name=user.get('firstName', ''),
        last_name=user.get('lastName', ''),
        role=user.get('role', 'user'),
        shift=user.get('shift'),
        active=user.get('active', True),
        access_token=session.get('access_token'),
    )
