# -*- encoding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, PasswordField
from wtforms.validators import Email, DataRequired, EqualTo, Length, Regexp


PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9\s]).{8,128}$'
PASSWORD_MESSAGE = 'Password must be 8-128 characters and include uppercase, lowercase, number, and symbol'


# Login form
class LoginForm(FlaskForm):
    username = StringField('Email',
                         id='username_login',
                         validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             id='pwd_login',
                             validators=[DataRequired()])


# Registration form
class CreateAccountForm(FlaskForm):
    first_name = StringField('First name',
                             id='first_name_create',
                             validators=[DataRequired()])
    last_name = StringField('Last name',
                            id='last_name_create',
                            validators=[DataRequired()])
    email = StringField('Email',
                      id='email_create',
                      validators=[
                          DataRequired(),
                          Email(),
                          Regexp(r'^[^@\s]+@apmterminals\.com$', message='Email must use @apmterminals.com'),
                      ])
    shift = SelectField(
        'Shift',
        id='shift_create',
        choices=[
            ('', 'Select shift'),
            ('Shift A', 'Shift A'),
            ('Shift B', 'Shift B'),
            ('Shift C', 'Shift C'),
            ('Shift D', 'Shift D'),
        ],
    )
    password = PasswordField('Password',
                             id='pwd_create',
                             validators=[
                                 DataRequired(),
                                 Length(min=8, max=128, message=PASSWORD_MESSAGE),
                                 Regexp(PASSWORD_PATTERN, message=PASSWORD_MESSAGE),
                             ])
    confirm_password = PasswordField(
        'Confirm password',
        id='pwd_confirm_create',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match')],
    )
