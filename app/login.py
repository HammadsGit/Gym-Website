import os
import logging
import requests
import datetime
from pathlib import Path
from app import app, db
from flask_mail import Mail
from flask import render_template, request, redirect, url_for, session, abort
from flask_login import login_user, login_required, logout_user, current_user

from app.models import Account, AccountType, Address

from app.forms import LoginForm, CreateAccountForm

# Google OAuth
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from google.oauth2 import id_token

# Facebook OAuth
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook

facebook_bp = make_facebook_blueprint(
    client_id="944779146703599",
    client_secret="26698767cda1fe14f5167226f5e88247",
    scope="email, public_profile, user_birthday,user_hometown",
)
app.register_blueprint(facebook_bp, url_prefix="/login/facebook")

# Google OAuth
from flask_dance.contrib.google import make_google_blueprint, google

google_bp = make_google_blueprint(
    client_id="630445047989-2m83hp7thu0buftqgfp974k21f36qinl.apps.googleusercontent.com",
    client_secret="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",
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/user.birthday.read",
    ],
)
app.register_blueprint(google_bp, url_prefix="/login/google")


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"



# Function to check account type
def AccountTypeCheck():
    if "accountType" in session:
        if session["accountType"] == "Manager":
            return "Manager"
        elif session["accountType"] == "Employee":
            return "Employee"
        elif session["accountType"] == "User":
            return "User"
        else:
            return "None"
    else:
        session["accountType"] = "None"
        return "None"


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)
        else:
            return function()

    return wrapper


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token, request=token_request, audience=GOOGLE_CLIENT_ID
    )

    # get's the user from the database
    user = (
        db.session.query(Account).filter(Account.email == id_info.get("email")).first()
    )

    # if the user is in the database, login in.
    if user != None:
        login_user(user)
        session["google_id"] = user.id
        return redirect("/")
    else:
        logging.warning(f"Account doesn't exist for {id_info.get('email')}")
        return redirect("/login")
    # print(user.email)


@app.route("/login_with_google", methods=["GET", "POST"])
def login_with_google():
    if not google.authorized:
        return redirect(url_for("google.login", next=request.url))
    resp = google.get("/oauth2/v2/userinfo")
    if resp.ok:
        user_data = resp.json()
        user_id = user_data.get("id")
        if not user_id:
            # flash('Email address not available from Google.')
            session["alert"] = {
                "color": "danger",
                "start": "Login Failed",
                "msg": "Google ID not available from Google.",
            }
            return redirect(url_for("loginPage"))
        user = db.session.query(Account).filter(Account.googleid == user_id).first()
        if user:
            login_user(user)
            # flash('Logged in successfully.')
            return redirect(url_for("HomePage"))
        else:
            # flash('Google Account is not linked to an Account.')
            session["alert"] = {
                "color": "danger",
                "start": "Login Failed",
                "msg": "Google Account is not linked to an Account",
            }
            return redirect(url_for("loginPage"))


@app.route("/login_with_facebook")
def login_with_facebook():
    if not facebook.authorized:
        return redirect(url_for("facebook.login", next=request.url))
    resp = facebook.get("/me?fields=id")
    if resp.ok:
        user_data = resp.json()
        user_id = user_data.get("id")
        if not user_id:
            # flash('Email address not available from Facebook.')
            session["alert"] = {
                "color": "danger",
                "start": "Login Failed",
                "msg": "Facebook ID not available from Facebook.",
            }
            return redirect(url_for("loginPage"))
        user = db.session.query(Account).filter(Account.facebookid == user_id).first()
        if user:
            login_user(user)
            # flash('Logged in successfully.')
            return redirect(url_for("HomePage"))
        else:
            # flash('Facebook Account is not linked to an Account.')
            session["alert"] = {
                "color": "danger",
                "start": "Login Failed",
                "msg": "Facebook Account is not linked to an Account",
            }
            return redirect(url_for("loginPage"))
    session["alert"] = {
        "color": "danger",
        "start": "Login Failed",
        "msg": "Facebook Login Failed",
    }
    return redirect(url_for("loginPage"))


@app.route("/create_account_with_facebook")
def create_account_with_facebook():
    if not facebook.authorized:
        return redirect(url_for("facebook.login", next=request.url))
    resp = facebook.get("/me?fields=id,email,birthday,first_name,last_name")
    if resp.ok:
        user_data = resp.json()
        user_email = user_data.get("email")
        user_id = user_data.get("id")
        user_birthday = user_data.get("birthday")
        user_firstname = (user_data.get("first_name"),)
        user_lastname = (user_data.get("last_name"),)
        # Convert tuple to string
        user_firstname = "".join(user_firstname)
        user_lastname = "".join(user_lastname)

        # Convert birthday string to datetime
        user_birthday = datetime.datetime.strptime(user_birthday, "%m/%d/%Y")
        if not user_email:
            # flash('Email address not available from Facebook.')
            session["alert"] = {
                "color": "danger",
                "start": "Login Failed",
                "msg": "Email address not available from Facebook.",
            }
            return redirect(url_for("loginPage"))
        user = db.session.query(Account).filter(Account.facebookid == user_id).first()
        if user:
            login_user(user)
            session["alert"] = {
                "color": "success",
                "start": "Logged In",
                "msg": "Logged in successfully.",
            }
            return redirect(url_for("HomePage"))
        else:
            # Create new account
            new_account = Account(
                username="FacebookUser" + user_id,
                firstname=user_firstname,
                surname=user_lastname,
                email=user_email,
                password="",  # No password for Facebook accounts
                facebookid=user_id,
                dob=user_birthday,
            )
            db.session.add(new_account)
            db.session.commit()
            # Login
            login_user(new_account)
            session["alert"] = {
                "color": "success",
                "start": "Account Created",
                "msg": "Account created successfully.",
            }
            return redirect(url_for("HomePage"))
    session["alert"] = {
        "color": "danger",
        "start": "Login Failed",
        "msg": "Failed to get user info from Facebook.",
    }
    return redirect(url_for("loginPage"))


@app.route("/create_account_with_google")
def create_account_with_google():
    if not google.authorized:
        return redirect(url_for("google.login", next=request.url))
    resp = google.get("/oauth2/v2/userinfo")
    if resp.ok:
        user_data = resp.json()
        user_email = user_data.get("email")
        user_id = user_data.get("id")
        user_firstname = user_data.get("given_name")
        user_lastname = user_data.get("family_name")
        user = db.session.query(Account).filter(Account.email == user_email).first()
        if user:
            session["alert"] = {
                "color": "danger",
                "start": "Account Already Exists",
                "msg": "An account with this email address already exists.",
            }
            return redirect(url_for("loginPage"))
        if not user_email:
            # flash('Email address not available from Google.')
            session["alert"] = {
                "color": "danger",
                "start": "Login Failed",
                "msg": "Email address not available from Google.",
            }
            return redirect(url_for("loginPage"))
        user = db.session.query(Account).filter(Account.googleid == user_id).first()
        if user:
            login_user(user)
            session["alert"] = {
                "color": "success",
                "start": "Logged In",
                "msg": "Logged in successfully.",
            }
            return redirect(url_for("HomePage"))
        else:
            # Create new account
            new_account = Account(
                username="GoogleUser" + user_id,
                firstname=user_firstname,
                surname=user_lastname,
                email=user_email,
                password="",  # No password for Google accounts
                googleid=user_id,
                # Give default date of birth
                dob=datetime.datetime.strptime("01/01/0001", "%m/%d/%Y"),
            )
            db.session.add(new_account)
            db.session.commit()
            # Login
            login_user(new_account)
            session["alert"] = {
                "color": "success",
                "start": "Account Created",
                "msg": "Account created successfully.",
            }
            return redirect(url_for("HomePage"))


@app.route("/link_account_with_facebook")
def link_account_with_facebook():
    if current_user.is_authenticated:
        if not facebook.authorized:
            return redirect(url_for("facebook.login", next=request.url))
        resp = facebook.get("/me?fields=id")
        if resp.ok:
            # Get current logged in user
            user = current_user
            user_data = resp.json()
            user_id = user_data.get("id")
            if not user_id:
                session["alert"] = {
                    "color": "danger",
                    "start": "Login Failed",
                    "msg": "Facebook ID not available from Facebook.",
                }
                return redirect(url_for("account_info"))
            user.facebookid = user_id
            db.session.commit()
            session["alert"] = {
                "color": "success",
                "start": "Account Linked",
                "msg": "Facebook account linked successfully.",
            }
            return redirect(url_for("HomePage"))


@app.route("/link_account_with_google")
def link_account_with_google():
    if current_user.is_authenticated:
        if not google.authorized:
            return redirect(url_for("google.login", next=request.url))
        resp = google.get("/oauth2/v2/userinfo")
        if resp.ok:
            # Get current logged in user
            user = current_user
            user_data = resp.json()
            user_id = user_data.get("id")
            if not user_id:
                # flash('Google ID not available from Google.')
                session["alert"] = {
                    "color": "danger",
                    "start": "Login Failed",
                    "msg": "Google ID not available from Google.",
                }
                return redirect(url_for("account_info"))
            user.googleid = user_id
            db.session.commit()
            session["alert"] = {
                "color": "success",
                "start": "Account Linked",
                "msg": "Google account linked successfully.",
            }
            return redirect(url_for("HomePage"))


@app.route("/unlink_account_from_facebook")
def unlink_account_from_facebook():
    if current_user.is_authenticated:
        user = current_user
        user.facebookid = None
        db.session.commit()
        session["alert"] = {
            "color": "success",
            "start": "Facebook Account Unlinked",
            "msg": "Facebook Account unlinked successfully.",
        }
        return redirect(url_for("accountInfo"))


@app.route("/unlink_account_from_google")
def unlink_account_from_google():
    if current_user.is_authenticated:
        user = current_user
        user.googleid = None
        db.session.commit()
        session["alert"] = {
            "color": "success",
            "start": "Google Account Unlinked",
            "msg": "Google Account unlinked successfully.",
        }
        return redirect(url_for("accountInfo"))


@app.route("/login", methods=["GET", "POST"])
def loginPage():
    form = LoginForm()
    # Redirect if we're already logged in
    if current_user.is_authenticated:
        return redirect("/")

    if request.method != "POST":
        return render_template("login_page.html", form=form)

    if not form.validate_on_submit():
        logging.warning("Login: Invalid form submitted")
        return (
            render_template(
                "login_page.html",
                form=form,
                alert={"color": "danger", "msg": "Invalid form."},
            ),
            500,
        )

    # Read details from form
    username = form.username.data
    password = form.password.data

    user = db.session.query(Account).filter(Account.username == username).first()
    if user and user.check_password(password):
        login_user(user)
        session["google_id"] = user.id  # setting the google login id.

        logging.info(f"User {user.username} logged in")
        # Session variable to determine account type
        if user.accountType == AccountType.Manager:
            session["accountType"] = "Manager"
        elif user.accountType == AccountType.Employee:
            session["accountType"] = "Employee"
        else:
            session["accountType"] = "User"

        if user.generatedPassword:
            return redirect("/change_password")
        return redirect("/")
    logging.warning(f"Login: Username/Password was invalid")
    return render_template(
        "login_page.html",
        form=form,
        alert={"msg": "Username/Password invalid", "color": "danger"},
    )


@app.route("/create_account", methods=["GET", "POST"])
def createAccountPage():
    form = CreateAccountForm()
    # Redirect if we're already logged in
    if current_user.is_authenticated:
        return redirect("/")

    if request.method != "POST":
        return render_template("create_account.html", form=form)

    if not form.validate_on_submit():
        logging.warning("Signup: Invalid form submitted")
        return (
            render_template(
                "create_account.html",
                form=form,
                alert={"color": "danger", "msg": "Invalid form."},
            ),
            500,
        )

    username = form.username.data
    password = form.password.data
    email = form.email.data
    first_name = form.first_name.data
    last_name = form.last_name.data
    post_code = form.post_code.data
    date_of_birth = form.date_of_birth.data

    address_line_1 = form.AddressLine1.data
    address_line_2 = form.AddressLine2.data
    address_line_3 = form.AddressLine3.data
    city = form.City.data
    country = form.Country.data
    phone_number = form.Phone_Number.data

    user = db.session.query(Account).filter(Account.username == username).first()
    if user:
        return render_template(
            "create_account.html",
            form=form,
            alert={
                "msg": "Username/Password taken, please try another",
                "color": "danger",
            },
        )
    user = db.session.query(Account).filter(Account.email == email).first()
    if user:
        return render_template(
            "create_account.html",
            form=form,
            alert={"msg": "Email address taken, please try another", "color": "danger"},
        )

    new_user = Account(
        username=username,
        email=email,
        firstname=first_name,
        surname=last_name,
        dob=date_of_birth,
    )

    new_user.set_password(password)
    # Commit user so we can get its ID to put in the address.
    with app.app_context():
        db.session.add(new_user)
        db.session.flush()

        # address = Address(accountId=new_user.id, postcode=post_code)
        address = Address(
            accountId=new_user.id,
            line1=address_line_1,
            line2=address_line_2,
            line3=address_line_3,
            city=city,
            country=country,
            postcode=post_code,
            phone=phone_number,
        )
        db.session.add(address)

        db.session.commit()

    # Render page with success message, then redirect to login after 2s (2000ms).
    return render_template(
        "create_account.html",
        form=form,
        alert={"start": "Success", "msg": "Account created.", "color": "success"},
        redirect={"url": "/login", "timeout": "2000"},
    )


@app.route("/logout", methods=["GET", "POST"])
@login_required
def Logout():
    logout_user()
    session["accountType"] = "None"
    return redirect(url_for("HomePage"))
