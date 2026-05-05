# -*- encoding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, PasswordField
from wtforms.validators import Email, DataRequired, EqualTo, Regexp


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
                             validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm password',
        id='pwd_confirm_create',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match')],
    )
