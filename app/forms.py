from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    IntegerField,
    DateField,
    EmailField,
    TextAreaField,
    SelectField,
)
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField("Username / Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class CreateAccountForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])

    AddressLine1 = StringField("Line 1", validators=[DataRequired()])
    AddressLine2 = StringField("Line 2")
    AddressLine3 = StringField("Line 3")
    City = StringField("City", validators=[DataRequired()])
    post_code = StringField("Post Code", validators=[DataRequired()])
    Country = StringField("Country", validators=[DataRequired()])
    Phone_Number = IntegerField("Phone Number", validators=[DataRequired()])

    date_of_birth = DateField("Date of Birth", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Create Account")


class ChangePassword(FlaskForm):
    oldPassword = PasswordField("Password")
    newPassword = PasswordField("Password", validators=[DataRequired()])


class ForgotPassword(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])


class SelectUser(FlaskForm):
    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.userId.choices = choices

    userId = SelectField("userId", validators=[DataRequired()])


class CancelMembership(FlaskForm):
    description = TextAreaField("Description", validators=[DataRequired()])
    submit = SubmitField("Cancel Membership")
