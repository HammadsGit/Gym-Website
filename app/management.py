import logging
from app import app, db
from flask import render_template, request, redirect, url_for, session
from flask_login import login_required, current_user
from app.models import (
    Membership,
    MembershipPrices,
    Activity,
    Facility,
    ActivityLocation,
    Account,
    AccountType,
    Booking,
    Receipt,
    Address,
)
from app.forms import CreateAccountForm

from app.login import AccountTypeCheck
from app.util import timeToNumeric, numericToTime
from sqlalchemy import and_, or_


# All management pages
@app.route("/management", methods=["GET", "POST"])
def Management():
    # Checks if the account is a managers account
    if AccountTypeCheck() == "Manager":
        return render_template("management.html")
    return redirect("/")


@app.route("/manage_prices", methods=["GET", "POST"])
def ManagePrices():
    if AccountTypeCheck() == "Manager":
        allPrices = db.session.query(MembershipPrices).all()
        if request.method == "POST":
            if len(request.form["bronze_price"]) > 0:
                newPrice = "{0:.2f}".format(
                    round(float(request.form["bronze_price"]), 2)
                )
                toChange = (
                    db.session.query(MembershipPrices)
                    .filter(MembershipPrices.name == "Single")
                    .first()
                )
                toChange.price = newPrice
            if len(request.form["gold_price"]) > 0:
                newPrice = "{0:.2f}".format(round(float(request.form["gold_price"]), 2))
                toChange = (
                    db.session.query(MembershipPrices)
                    .filter(MembershipPrices.name == "Month")
                    .first()
                )
                toChange.price = newPrice
            if len(request.form["platinum_price"]) > 0:
                newPrice = "{0:.2f}".format(
                    round(float(request.form["platinum_price"]), 2)
                )
                toChange = (
                    db.session.query(MembershipPrices)
                    .filter(MembershipPrices.name == "Year")
                    .first()
                )
                toChange.price = newPrice

            db.session.commit()
        return render_template("manage_prices.html", prices=allPrices)
    return redirect("/")


@app.route("/manage_activities_facilities", methods=["GET", "POST"])
def ManageActivitiesFacilities():
    if AccountTypeCheck() == "Manager":
        # This happens if they have updated anything
        if request.method == "POST":
            if "function" in request.form:
                toChange = (
                    db.session.query(Facility)
                    .filter(request.form["facilityID"] == Facility.id)
                    .first()
                )
                if request.form["function"] == "updateFacilityName":
                    toChange.name = request.form["facilityName"]
                elif request.form["function"] == "updateFacilityCapacity":
                    toChange.capacity = request.form["facilityCapacity"]
                elif request.form["function"] == "updateFacilityOpen":
                    newTime = timeToNumeric(request.form["time"])
                    toChange.opens = newTime
                elif request.form["function"] == "updateFacilityClose":
                    newTime = timeToNumeric(request.form["time"])
                    toChange.closes = newTime
                elif request.form["function"] == "updateFacilityActivities":
                    activity = (
                        db.session.query(Activity)
                        .filter(request.form["activityName"] == Activity.name)
                        .first()
                    )
                    activity.name = request.form["activityNew"]
            else:
                # Remove all existing function tags from session
                session.pop("accActToFac", None)
                session.pop("editActivityName", None)
                session.pop("editFacilityID", None)
                for key in request.form:
                    if key.startswith("delete_facility."):
                        facilityID = key.partition(".")[-1]
                        toChange = (
                            db.session.query(Facility)
                            .filter(facilityID == Facility.id)
                            .first()
                        )
                        db.session.delete(toChange)
                    elif key.startswith("delete_activity."):
                        partition = key.split(".")
                        facilityID = partition[1]
                        activityID = (
                            db.session.query(Activity)
                            .filter(partition[2] == Activity.name)
                            .first()
                            .id
                        )
                        toChange = (
                            db.session.query(ActivityLocation)
                            .filter(
                                activityID == ActivityLocation.activityId,
                                facilityID == ActivityLocation.facilityId,
                            )
                            .first()
                        )
                        db.session.delete(toChange)
                    elif key.startswith("addActivity."):
                        partition = key.split(".")
                        facilityID = partition[1]
                        session["addActToFac"] = facilityID
                        logging.warning(session["addActToFac"])
                        return redirect("/manage_add_activity")
                    elif key.startswith("edit_activity."):
                        partition = key.split(".")
                        session["editActivityName"] = partition[2]
                        session["editFacilityID"] = partition[1]
                        logging.warning(
                            f'Editing activity "{partition[2]}" of requested'
                        )
                        return redirect("/manage_add_activity")
                    elif key == "addFacility":
                        return redirect("/manage_add_facility")
            db.session.commit()

        f = db.session.query(Facility).all()
        facilities = []
        for facility in f:
            activityLocations = (
                db.session.query(ActivityLocation)
                .filter(ActivityLocation.facilityId == facility.id)
                .group_by(ActivityLocation.activityId)
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
        return render_template(
            "manage_activities_facilities.html", facilities=facilities
        )
    return redirect("/")


@app.route("/manage_add_facility", methods=["GET", "POST"])
def ManageAddFacility():
    if AccountTypeCheck() == "Manager":
        alert = {"msg": "", "color": "danger"}
        if request.method == "POST":
            logging.warning(session["addActToFac"])
            if "facilityName" in request.form:
                # only allow alpha characters and spaces
                if request.form["facilityName"].replace(" ", "").isalpha():
                    if request.form["facilityOpen"] == "":
                        alert["msg"] = "Invalid open time."
                    elif request.form["facilityClose"] == "":
                        alert["msg"] = "Invalid close time."
                    else:
                        openTime = timeToNumeric(request.form["facilityOpen"])
                        closeTime = timeToNumeric(request.form["facilityClose"])

                        newFac = Facility(
                            name=request.form["facilityName"],
                            capacity=request.form["facilityCapacity"],
                            opens=openTime,
                            closes=closeTime,
                        )
                        db.session.add(newFac)
                        db.session.commit()
                        alert["msg"] = "Activity Added."
                        alert["color"] = "success"
                        alert["start"] = "Success"
                        return render_template(
                            "manage_add_facility.html",
                            alert=alert,
                            redirect={
                                "url": "/manage_activities_facilities",
                                "timeout": "2000",
                            },
                        )
                else:
                    alert["msg"] = "Invalid name."
        if alert["msg"]:
            return render_template("manage_add_facility.html", alert=alert)
        else:
            return render_template("manage_add_facility.html")
    return redirect("/")


@app.route("/manage_add_activity", methods=["GET", "POST"])
def ManageAddActivity():
    if AccountTypeCheck() == "Manager":
        alert = {"msg": "", "color": "danger"}
        args = {}
        if "addActToFac" in session:
            facility = db.session.query(Facility).get(session["addActToFac"])
            facName = facility.name
            facCapacity = facility.capacity
        if "editActivityName" in session:
            activity = (
                db.session.query(Activity)
                .filter(Activity.name == session["editActivityName"])
                .first()
            )
            facility = db.session.query(Facility).get(session["editFacilityID"])
            facName = facility.name
            facCapacity = facility.capacity
            activityLocations = (
                db.session.query(ActivityLocation)
                .filter(
                    and_(
                        ActivityLocation.activityId == activity.id,
                        ActivityLocation.facilityId == facility.id,
                    )
                )
                .all()
            )
            args = {
                "isEditing": True,
                "activityName": activity.name,
                "activityCapacity": activity.capacity,
                "activityLocations": [],
            }
            if activity.length:
                args["activityLength"] = activity.length

            if activity.capacity is None:
                args["activityCapacity"] = 0

            for al in activityLocations:
                if al.startDay:
                    args["activityLocations"].append(
                        {
                            "id": al.id,
                            "startDay": al.startDay,
                            "startTime": numericToTime(al.startTime),
                        }
                    )

        if request.method == "POST":
            if "activityName" in request.form:
                # checkbox values are only sent if they're true, so we check they exist
                specificDay = "activitySpecificDay" in request.form
                lengthDefined = "activityLengthDefined" in request.form
                startDays = []
                startTimes = []
                # When editing an activity, activityLocation IDs are given along with each startDay/Time. They are stored here for later use.
                editedIDs = []
                # ActivityLocation IDs requested for deletion
                deleteIDs = []
                if specificDay and lengthDefined:
                    for key in request.form:
                        if "activityTime" in key:
                            startTimes.append(request.form[key])
                            if "isEditing" in args and args["isEditing"]:
                                editedIDs.append(key.replace("activityTime", ""))
                        elif "activityStartDay" in key:
                            startDays.append(request.form[key])
                        elif "deleteActivityLocation" in key:
                            deleteIDs.append(request.form[key])
                # only allow alpha characters and spaces
                if request.form["activityName"].replace(" ", "").isalpha():
                    if specificDay and len(startDays) == 0:
                        alert["msg"] = "Invalid start day."
                    elif specificDay and len(startTimes) == 0:
                        alert["msg"] = "Invalid start time."
                    elif (lengthDefined or specificDay) and request.form[
                        "activityLength"
                    ] == "":
                        if specificDay:
                            alert[
                                "msg"
                            ] = "Length must be set for scheduled activities."
                        else:
                            alert["msg"] = "Invalid length."
                    else:
                        if "isEditing" in args and args["isEditing"]:
                            setattr(activity, "name", str(request.form["activityName"]))
                            if not request.form["activityCapacity"]:
                                setattr(activity, "capacity", None)
                            else:
                                setattr(
                                    activity,
                                    "capacity",
                                    int(request.form["activityCapacity"]),
                                )
                            if lengthDefined:
                                setattr(
                                    activity,
                                    "length",
                                    int(request.form["activityLength"]),
                                )
                        else:
                            newAcc = Activity(name=request.form["activityName"])
                            if not request.form["activityCapacity"]:
                                newAcc.capacity = None
                            else:
                                newAcc.capacity = request.form["activityCapacity"]
                            if lengthDefined:
                                newAcc.length = request.form["activityLength"]

                            db.session.add(newAcc)
                        db.session.commit()

                        if not specificDay:
                            if not "isEditing" in args and args["isEditing"]:
                                newAccLoc = ActivityLocation(
                                    activityId=newAcc.id,
                                    facilityId=session["addActToFac"],
                                )
                                db.session.add(newAccLoc)
                                db.session.commit()
                        else:
                            for i in range(len(startDays)):
                                if "isEditing" in args and args["isEditing"]:
                                    acl = db.session.query(ActivityLocation).get(
                                        editedIDs[i]
                                    )
                                    if not acl:
                                        acl = ActivityLocation(
                                            activityId=activity.id,
                                            facilityId=facility.id,
                                            startDay=startDays[i],
                                            startTime=timeToNumeric(startTimes[i]),
                                        )
                                        db.session.add(acl)
                                    else:
                                        acl.startDay = startDays[i]
                                        acl.startTime = timeToNumeric(startTimes[i])
                                else:
                                    newAccLoc = ActivityLocation(
                                        activityId=newAcc.id,
                                        facilityId=session["addActToFac"],
                                        startDay=startDays[i],
                                        startTime=timeToNumeric(startTimes[i]),
                                    )
                                    db.session.add(newAccLoc)
                            db.session.commit()

                        if "isEditing" in args and args["isEditing"]:
                            for id in deleteIDs:
                                db.session.delete(
                                    db.session.query(ActivityLocation).get(id)
                                )

                            db.session.commit()
                            session.pop("editActivityName")
                            session.pop("editFacilityID")
                        else:
                            session.pop("addActToFac")
                        alert["msg"] = "Added Activity."
                        alert["start"] = "Success"
                        alert["color"] = "success"
                        return render_template(
                            "manage_add_activity.html",
                            alert=alert,
                            redirect={
                                "url": "/manage_activities_facilities",
                                "timeout": "2000",
                            },
                            **args,
                        )
                else:
                    alert["msg"] = "Invalid name"
        if alert["msg"]:
            return render_template(
                "manage_add_activity.html",
                alert=alert,
                facName=facName,
                facCapacity=facCapacity,
                **args,
            )
        else:
            return render_template(
                "manage_add_activity.html",
                facName=facName,
                facCapacity=facCapacity,
                **args,
            )
    return redirect("/")


@app.route("/manage_staff", methods=["GET", "POST"])
def ManageStaff():
    if AccountTypeCheck() == "Manager":
        if request.method == "POST":
            if "function" in request.form:
                user = Account.query.filter(
                    Account.id == request.form["userID"]
                ).first()
                newType = request.form["option"]
                if newType == "User":
                    user.accountType = AccountType.User
                elif newType == "Employee":
                    user.accountType = AccountType.Employee
                elif newType == "Manager":
                    user.accountType = AccountType.Manager
                db.session.commit()
            elif "add_account" in request.form:
                session["manageAccType"] = request.form["add_account"]
                return redirect("/manage_add_account")
            else:
                for key in request.form:
                    if key.startswith("delete_account."):
                        userID = key.partition(".")[-1]
                        toChange = (
                            db.session.query(Booking)
                            .filter(userID == Booking.accountId)
                            .all()
                        )
                        for a in toChange:
                            db.session.delete(a)
                        toChange = (
                            db.session.query(Receipt)
                            .filter(userID == Receipt.accountId)
                            .all()
                        )
                        for a in toChange:
                            db.session.delete(a)
                        toChange = (
                            db.session.query(Address)
                            .filter(userID == Address.accountId)
                            .all()
                        )
                        for a in toChange:
                            db.session.delete(a)
                        toChange = (
                            db.session.query(Membership)
                            .filter(userID == Membership.accountId)
                            .all()
                        )
                        for a in toChange:
                            db.session.delete(a)
                        toChange = (
                            db.session.query(Account).filter(userID == Account.id).all()
                        )
                        for a in toChange:
                            db.session.delete(a)
                        db.session.commit()
        users = Account.query.all()
        return render_template(
            "manage_staff.html", users=users, AccountType=AccountType
        )
    return redirect("/")


@app.route("/manage_add_account", methods=["GET", "POST"])
def ManageAddAccount():
    if AccountTypeCheck() == "Manager":
        form = CreateAccountForm()

        if request.method == "GET":
            return render_template(
                "manage_add_account.html", form=form, accType=session["manageAccType"]
            )

        if not form.validate_on_submit():
            logging.warning("Signup: Invalid form submitted")
            return render_template(
                "manage_add_account.html",
                form=form,
                alert={"color": "danger", "msg": "Invalid form."},
                accType=session["manageAccType"],
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
                "manage_add_account.html",
                form=form,
                alert={
                    "msg": "Username/Password taken, please try another",
                    "color": "danger",
                },
                accType=session["manageAccType"],
            )
        user = db.session.query(Account).filter(Account.email == email).first()
        if user:
            return render_template(
                "manage_add_account.html",
                form=form,
                alert={
                    "msg": "Email address taken, please try another",
                    "color": "danger",
                },
                accType=session["manageAccType"],
            )

        new_user = Account(
            username=username,
            email=email,
            firstname=first_name,
            surname=last_name,
            dob=date_of_birth,
        )
        new_user.set_password(password)

        if session["manageAccType"] == "addManager":
            new_user.accountType = AccountType.Manager
        elif session["manageAccType"] == "addEmployee":
            new_user.accountType = AccountType.Employee
        elif session["manageAccType"] == "addUser":
            new_user.accountType = AccountType.User

        # Commit user so we can get its ID to put in the address.
        with app.app_context():
            db.session.add(new_user)
            db.session.flush()

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

        session.pop("manageAccType")
        # Render page with success message, then redirect to login after 2s (2000ms).
        return render_template(
            "manage_add_account.html",
            form=form,
            alert={"start": "Success", "msg": "Account created.", "color": "success"},
            redirect={"url": "/manage_staff", "timeout": "2000"},
        )
    return redirect("/")


@app.route("/manage_discount", methods=["GET", "POST"])
def ManageDiscount():
    if AccountTypeCheck() == "Manager":
        discountValue = (
            db.session.query(MembershipPrices)
            .filter(MembershipPrices.name == "Discount")
            .first()
        )
        if request.method == "POST":
            if len(request.form["discount_value"]) > 0:
                val = float(request.form["discount_value"]) / 100
                discountValue.price = val
        db.session.commit()
        return render_template("manage_discount.html", discountValue=discountValue)
    return redirect("/")


@app.route("/management_graphs", methods=["GET", "POST"])
def ManageGraphs():
    if AccountTypeCheck() == "Manager":
        facilities = db.session.query(Facility).filter().all()
        activities = db.session.query(Activity).filter().all()
        activityLocations = db.session.query(ActivityLocation).filter().all()
        bookings = db.session.query(Booking).filter().all()

        max = len(facilities)
        for f in facilities:
            num = 0
            for a in activityLocations:
                if a.facilityId == f.id:
                    num += 1
                if max < num:
                    max = num

        w, h = max, len(facilities) + 1
        Matrix = [[[0 for x in range(2)] for z in range(w)] for y in range(h)]

        for i, f in enumerate(facilities):
            Matrix[0][i][0] = f.name
            Matrix[0][i][1] = 0

        for i in range(h):
            for contents in range(w):
                if i != 0:
                    Matrix[i][contents][0] = ""
                    Matrix[i][contents][1] = 0

        for booking in bookings:
            for activityLocation in activityLocations:
                if booking.activityLocation == activityLocation.id:
                    facility = (
                        db.session.query(Facility)
                        .filter(activityLocation.facilityId == Facility.id)
                        .first()
                    )
                    activity = (
                        db.session.query(Activity)
                        .filter(activityLocation.activityId == Activity.id)
                        .first()
                    )

                    index = -1
                    for i in range(len(facilities)):
                        if Matrix[0][i][0] == facility.name:
                            index = i
                            Matrix[0][i][1] += 1
                            break

                    found = False
                    for i in range(max):
                        if Matrix[index + 1][i][0] == activity.name:
                            found = True
                            Matrix[index + 1][i][1] += 1
                            break
                    if found == False:
                        for i in range(max):
                            if Matrix[index + 1][i][0] == "":
                                Matrix[index + 1][i][0] = activity.name
                                Matrix[index + 1][i][1] += 1
                                break

        Usage = [["Single", 0, 0, 0], ["Monthly", 0, 0, 0], ["Yearly", 0, 0, 0]]

        membershipPrices = db.session.query(MembershipPrices).filter().all()
        memberships = db.session.query(Membership).filter().all()

        single = 0
        actSingle = 0

        monthly = 0
        actMonthly = 0

        yearly = 0
        actYearly = 0

        for mem in memberships:
            if mem.entryType == 0:
                single += 1
                if mem.active == True:
                    actSingle += 1
            elif mem.entryType == 1:
                monthly += 1
                if mem.active == True:
                    actMonthly += 1
            elif mem.entryType == 2:
                yearly += 1
                if mem.active == True:
                    actYearly += 1

        if single != 0:
            Usage[0][1] = (
                single
                * db.session.query(MembershipPrices)
                .filter(MembershipPrices.name == "Single")
                .first()
                .price
            )
            Usage[0][2] = single
            Usage[0][3] = actSingle

        if monthly != 0:
            Usage[1][1] = (
                monthly
                * db.session.query(MembershipPrices)
                .filter(MembershipPrices.name == "Month")
                .first()
                .price
            )
            Usage[1][2] = monthly
            Usage[1][3] = actMonthly

        if yearly != 0:
            Usage[2][1] = (
                yearly
                * db.session.query(MembershipPrices)
                .filter(MembershipPrices.name == "Year")
                .first()
                .price
            )
            Usage[2][2] = yearly
            Usage[2][3] = actYearly

        data = {"Matrix": Matrix, "Width": w, "Height": h, "Usage": Usage}
        return render_template("management_graphs.html", data=data)
    return redirect("/")
