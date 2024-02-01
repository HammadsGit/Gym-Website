from app import app, db
import datetime
from flask_mail import Mail, Message
import random, string
from flask import render_template, request, redirect, url_for, session, jsonify
from app.bookings import getBookings
from app.payments import checkMembership, getMembership
from app.forms import (
    CancelMembership,
    LoginForm,
    CreateAccountForm,
    ChangePassword,
    ForgotPassword,
)
from flask_login import (
    login_required,
    current_user,
    LoginManager,
)
from app.models import (
    Account,
    Booking,
    Address,
    Facility,
    Activity,
    ActivityLocation,
    AccountType,
    Booking,
    Membership,
    MembershipPrices,
    Receipt,
)
from app.util import (
    numberToDay,
    numericToTime,
    numericToTuple,
    timeToNumeric,
    dateSuffix,
)
import logging, datetime
from sqlalchemy import or_, and_
from decimal import Decimal, ROUND_UP, ROUND_DOWN
from uuid import uuid4
from pathlib import Path

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/"

app.config.update(
    dict(
        DEBUG=True,
        MAIL_SERVER="smtp.gmail.com",
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USE_SSL=False,
        MAIL_USERNAME="robotmail2000",
        MAIL_PASSWORD="ilyghdxhmfgcmggy",
    )
)

mail = Mail(app)


@login_manager.user_loader
def load_user(user_id):
    app.logger.info("Load User")
    return Account.query.get(user_id)


from app import login, bookings, payments, management

YOUR_DOMAIN = "https://localhost:5000"


@app.route("/", methods=["GET", "POST"])
def HomePage():
    if current_user.is_authenticated:
        membership = getMembership(current_user.id)

        # bookings = getBookings(current_user, until=(datetime.datetime.now() + datetime.timedelta(days=7)))
        bookings = getBookings(current_user)

        now = datetime.datetime.now()
        weekStart = now - datetime.timedelta(days=now.weekday())
        weekBookings = getBookings(current_user, fromTime=weekStart, until=now)
        weekBookingCount = len(weekBookings["past"]["activities"]) + len(
            weekBookings["past"]["classes"]
        )

        # Maximum number of activities/classes to show.
        activityCap = 3

        return render_template(
            "home.html",
            upcomingBookings=bookings["upcoming"]["activities"],
            upcomingClasses=bookings["upcoming"]["classes"],
            membership=membership,
            weekBookingCount=weekBookingCount,
            activityCap=activityCap,
        )

    return render_template("home.html")


@app.route("/pricing", methods=["GET", "POST"])
def pricing():
    allPrices = db.session.query(MembershipPrices).all()
    if current_user.is_authenticated:
        membership = getMembership(current_user.id)
        if membership:
            return render_template(
                "pricing.html",
                membership=membership,
                prices=allPrices,
                currentTime=datetime.datetime.now(),
            )
            # if membership exists then show membership
        elif not membership:
            return render_template("pricing.html", prices=allPrices)
            # if membership does not exist then show available memberships.
    else:
        return render_template("pricing.html", prices=allPrices)


@app.route("/facilities", methods=["GET", "POST"])
# facilities returns a list view of the centre's facilities,
# with information such as capacity, opening/closing times, and available activities.
def facilities():
    f = db.session.query(Facility).all()
    facilities = []
    for facility in f:
        activityLocations = (
            db.session.query(ActivityLocation)
            .filter(ActivityLocation.facilityId == facility.id)
            .all()
        )
        activities = []
        for al in activityLocations:
            a = db.session.query(Activity).get(al.activityId)
            activities.append(a.name)

        facilities.append(
            {
                "id": facility.id,
                "name": facility.name,
                "capacity": facility.capacity,
                "opens": numericToTime(facility.opens),
                "closes": numericToTime(facility.closes),
                "activities": activities,
            }
        )

    return render_template("facilities.html", facilities=facilities)


@app.route("/account_info", methods=["GET", "POST"])
@login_required
def accountInfo():
    emptyStr = ""
    # shows account infomation
    data = db.session.query(Account).get(current_user.id)
    receiptRows = (
        db.session.query(Receipt)
        .filter(Receipt.accountId == current_user.id)
        .order_by(Receipt.date.desc())
        .all()
    )
    receipts = []
    for r in receiptRows:
        if r.discountPct is None:
            r.discountPct = 0

        receipts.append(
            {
                "date": r.date.strftime("%A %D %B %Y"),
                "discountPct": r.discountPct,
                "itemName": r.itemName,
                "itemCount": r.itemCount,
                "itemPrice": r.itemPrice,
                "totalPrice": "{:.2f}".format(
                    ((100.0 - float(r.discountPct)) / 100.0)
                    * (float(r.itemPrice) * float(r.itemCount))
                ),
            }
        )

    address = (
        db.session.query(Address).filter(Address.accountId == current_user.id).first()
    )

    if address is None:
        # Empty placeholder address
        address = Address()

    # Generate receipts if necessary
    checkMembership(current_user.id)
    return render_template(
        "account_info.html",
        data=data,
        receipts=receipts,
        address=address,
        emptyStr=emptyStr,
    )


@app.route("/account_info/address", methods=["PUT"])
@login_required
def changeAddress():
    newAddr = request.get_json()
    address = (
        db.session.query(Address).filter(Address.accountId == current_user.id).first()
    )
    existingAddress = address is not None
    if not existingAddress:
        address = Address(accountId=current_user.id)

    for field in ["line1", "line2", "line3", "city", "postcode", "country", "phone"]:
        if newAddr[field]:
            setattr(address, field, newAddr[field])

    if not existingAddress:
        db.session.add(address)

    db.session.commit()
    return "", 200


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def changePassword():
    form = ChangePassword()

    if request.method != "POST":
        return render_template("change_password.html", form=form)

    if not form.validate_on_submit():
        logging.warning("Change Password: Invalid form submitted")
        return (
            render_template(
                "change_password.html",
                form=form,
                alert={"color": "danger", "msg": "Invalid form."},
            ),
            500,
        )

    newPassword = form.newPassword.data

    if current_user.password == "":
        oldPassword = current_user.password
    else:
        oldPassword = form.oldPassword.data

    user = Account.query.get(current_user.id)
    if user and (user.check_password(oldPassword) or oldPassword == ""):
        user.set_password(newPassword)
        user.generatedPassword = False
        db.session.commit()
        return render_template(
            "change_password.html",
            form=form,
            alert={"start": "Success", "msg": "Password Changed", "color": "success"},
            redirect={"url": "/login", "timeout": "2000"},
        )

    logging.warning(f"Change Password: Old password doesn't match")
    return render_template(
        "change_password.html",
        form=form,
        alert={"msg": "Old Password invalid", "color": "danger"},
    )


@app.route("/forgot_password", methods=["GET", "POST"])
def forgotPassword():
    form = ForgotPassword()

    # Redirect if we're already logged in
    if current_user.is_authenticated:
        return redirect("/")

    if request.method != "POST":
        return render_template("forgot_password.html", form=form)

    if not form.validate_on_submit():
        logging.warning("Forgot Password: Invalid form submitted")
        return (
            render_template(
                "forgot_password.html",
                form=form,
                alert={"color": "danger", "msg": "Invalid form."},
            ),
            500,
        )

    email = form.email.data

    user = Account.query.filter_by(email=email).first()
    if user:
        # changes password
        characters = string.ascii_letters + "0123456789"
        password = str("".join(random.choice(characters) for i in range(10)))
        user.set_password(password)
        user.generatedPassword = True
        db.session.commit()
        # creates email
        msg = Message(
            "New Password",
            sender="robotmail2000@gmail.com",
            recipients=[form.email.data],
        )
        msg.body = (
            "Your username: "
            + user.username
            + "\r\nYour new password: "
            + password
            + "\r\nPlease change your password when you have logged in."
        )
        # Sends there new password to their email
        mail.send(msg)
        app.logger.info("{} forgot password, sent email".format(user.username))
        return render_template(
            "forgot_password.html",
            form=form,
            alert={"start": "Success", "msg": "Email Sent", "color": "success"},
            redirect={"url": "/login", "timeout": "3000"},
        )
    return render_template(
        "forgot_password.html",
        form=form,
        alert={"msg": "Invalid Email", "color": "danger"},
    )


@app.route("/facilities/<facilityId>/capacity", methods=["GET"])
# facilityCurrentCapacity returns an estimate of the number of people
# currently in <facilityId>. If <facilityId> == "all", estimate is
# for the whole gym.
# if the facility is closed, "open" = false is returned and remaining
# is set to zero.
def facilityCurrentCapacity(facilityId):
    today = datetime.datetime.now().replace(second=0, microsecond=0)
    time = timeToNumeric(datetime.datetime.now().strftime("%H:%M"))
    facilities = []
    if facilityId == "all":
        facilities = db.session.query(Facility).all()
    else:
        facilities = [db.session.query(Facility).get(facilityId)]

    facilityCapacities = [f.capacity for f in facilities]
    facilityRemainings = [f.capacity for f in facilities]

    facilityOpen = len(facilities)
    for f in facilities:
        if not (time > f.opens and time < f.closes):
            facilityOpen -= 1

    facilityOpen = facilityOpen > 0
    if not facilityOpen:
        facilityRemainings = [0]
    else:
        aclFilters = [(ActivityLocation.facilityId == f.id) for f in facilities]
        activityLocations = [
            db.session.query(ActivityLocation).filter(f).all() for f in aclFilters
        ]
        bookingFilters = [
            [(Booking.activityLocation == acl.id) for acl in acls]
            for acls in activityLocations
        ]
        bookings = [
            db.session.query(Booking).filter(or_(*filters)).all()
            for filters in bookingFilters
        ]

        for i, facilityBookings in enumerate(bookings):
            for booking in facilityBookings:
                if booking.start <= today and booking.end >= today:
                    facilityRemainings[i] -= 1

    return (
        jsonify(
            {
                "capacity": sum(facilityCapacities),
                "remaining": sum(facilityRemainings),
                "open": facilityOpen,
            }
        ),
        200,
    )


@app.route("/<path:path>")
# Static Proxy delivers files from the "app/static" folder.
def StaticProxy(path):
    return app.send_static_file(path)
