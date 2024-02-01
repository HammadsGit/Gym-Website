import datetime
import logging
from decimal import Decimal, ROUND_UP, ROUND_DOWN

from app import app, db
from flask import render_template, request, redirect, url_for, session
from flask_login import login_required, current_user
from app.models import (
    Booking,
    Activity,
    Facility,
    ActivityLocation,
    AccountType,
    Account,
    Membership,
    Receipt,
    MembershipPrices,
)
from app.forms import SelectUser
from app.util import numberToDay, numericToTime, numericToTuple, dateSuffix
from app.payments import checkMembership, refundBooking
from app.login import AccountTypeCheck
from sqlalchemy import or_, and_


def getBookings(current_user, **kwargs):
    fromTime = None
    until = None
    if "fromTime" in kwargs:
        fromTime = kwargs["fromTime"]
    if "until" in kwargs:
        until = kwargs["until"]

    bookings = (
        db.session.query(Booking)
        .filter(Booking.accountId == current_user.id)
        .order_by(Booking.start)
        .all()
    )

    activities = {
        "upcoming": {"activities": [], "classes": []},
        "past": {"activities": [], "classes": []},
    }
    now = datetime.datetime.now()
    for booking in bookings:
        if until is not None and booking.end > until:
            continue
        if fromTime is not None and booking.start < fromTime:
            continue
        acl = db.session.query(ActivityLocation).get(booking.activityLocation)
        act = db.session.query(Activity).get(acl.activityId)
        fac = db.session.query(Facility).get(acl.facilityId)
        duration = (booking.end - booking.start).total_seconds()
        hours = int(duration // 3600)
        duration -= hours * 3600
        minutes = int(duration // 60)
        durationString = ""
        if hours > 0:
            durationString += f"{hours}h"
        if minutes > 0:
            durationString += f"{minutes}m"

        activity = {
            "id": booking.id,
            "name": act.name,
            "facility": fac.name,
            "date": booking.start.strftime("%A %d/%m/%y"),
            "time": booking.start.strftime("%H:%M")
            + " - "
            + booking.end.strftime("%H:%M"),
            "duration": durationString,
        }

        if booking.end < now:
            if acl.startDay and acl.startTime:
                activities["past"]["classes"].append(activity)
            else:
                activities["past"]["activities"].append(activity)
        else:
            if acl.startDay and acl.startTime:
                activities["upcoming"]["classes"].append(activity)
            else:
                activities["upcoming"]["activities"].append(activity)

    return activities


# Check if a class is bookable on the given day. Since classes have fixed times, time overlap checking isn't needed.
def classBookable(activityLocationId, day, accountId=None):
    acl = db.session.query(ActivityLocation).get(activityLocationId)
    bookings = (
        db.session.query(Booking)
        .filter(Booking.activityLocation == activityLocationId)
        .all()
    )
    availableCapacity = db.session.query(Facility).get(acl.facilityId).capacity
    delta = datetime.timedelta(days=1)

    # dont show stuff that's already happened as bookable
    if day.weekday() > acl.startDay - 1:
        # delta = datetime.timedelta(days=-1)
        return False

    # "day" arg is the searched date, even though the class might not be on that date.
    # increment the searched date to match the class' weekday.
    while acl.startDay - 1 != day.weekday():
        day += delta

    for booking in bookings:
        if booking.start.date() != day.date():
            continue
        if booking.teamBooking is True:
            return False

        # Don't show classes you've already booked
        if accountId is not None and booking.accountId == accountId:
            print(f"AL{activityLocationId} not bookable as user has already booked it")
            return False
        availableCapacity -= 1

    if availableCapacity <= 0:
        print(f"AL{activityLocationId} not bookable as no slots available")
    return availableCapacity > 0


# Check if an activity is bookable on the given period.
# Bookings are allowed in 30 minute intervals so that available capacity can be checked
# over a regular interval.
def activityBookable(activityLocationId, start, end, accountId=None):
    start = start.replace(second=0, microsecond=0)
    end = end.replace(second=0, microsecond=0)
    acl = db.session.query(ActivityLocation).get(activityLocationId)
    act = db.session.query(Activity).get(acl.activityId)
    availableCapacity = db.session.query(Facility).get(acl.facilityId).capacity
    sameFacilityACLs = (
        db.session.query(ActivityLocation)
        .filter(ActivityLocation.facilityId == acl.facilityId)
        .all()
    )
    # Assemble filter for all bookings with activityLocations with the same facility as our main one
    bookingFilters = []
    for facl in sameFacilityACLs:
        bookingFilters.append(Booking.activityLocation == facl.id)

    bookings = db.session.query(Booking).filter(or_(*bookingFilters)).all()
    startTime = start
    periodIndex = 0
    periodCapacities = [int(availableCapacity)]
    # Loop over 30 minute intervals, calculating the available capacity for each.
    while startTime != end:
        for booking in bookings:
            if booking.start.date() != start.date():
                continue
            if booking.start <= startTime and booking.end > startTime:
                periodCapacities[periodIndex] -= 1
                if accountId is not None and booking.accountId == accountId:
                    return False

        if periodCapacities[periodIndex] == 0:
            return False

        periodCapacities.append(int(availableCapacity))
        periodIndex += 1
        startTime += datetime.timedelta(minutes=30)
    return True


# Returns the 30-minute slots available for an activityLocation on a given day.
def availableSlots(activityLocationId, day):
    day = day.replace(second=0, microsecond=0)
    acl = db.session.query(ActivityLocation).get(activityLocationId)
    act = db.session.query(Activity).get(acl.activityId)
    fac = db.session.query(Facility).get(acl.facilityId)
    openHour, openMinute = numericToTuple(fac.opens)
    opening = day.replace(hour=openHour, minute=openMinute)
    closeHour, closeMinute = numericToTuple(fac.closes)
    closing = day.replace(hour=closeHour, minute=closeMinute)

    availableCapacity = db.session.query(Facility).get(acl.facilityId).capacity
    sameFacilityACLs = (
        db.session.query(ActivityLocation)
        .filter(ActivityLocation.facilityId == acl.facilityId)
        .all()
    )
    # Assemble filter for all bookings with activityLocations with the same facility as our main one
    bookingFilters = []
    for facl in sameFacilityACLs:
        bookingFilters.append(Booking.activityLocation == facl.id)

    bookings = db.session.query(Booking).filter(or_(*bookingFilters)).all()
    periods = []
    # Loop over 30 minute intervals, calculating the available capacity for each.
    while opening != closing:
        if opening < datetime.datetime.now():
            opening += datetime.timedelta(minutes=30)
            continue
        p = [
            opening.strftime("%H:%M"),
            (opening + datetime.timedelta(minutes=30)).strftime("%H:%M"),
        ]
        available = availableCapacity
        for booking in bookings:
            if booking.start.date() != opening.date():
                continue
            if booking.start <= opening and booking.end > opening:
                available -= 1

        if available > 0:
            periods.append(p)
        opening += datetime.timedelta(minutes=30)
    return periods


# getActivityData returns data necessary to render the booking pages.
def getActivityData(auth=False, accountId=None, searchedDatetime=None):
    currentDatetime = datetime.datetime.now()
    currentDate = currentDatetime.strftime("%Y-%m-%d")
    if not auth:
        searchedDatetime = None

    if (not auth) or searchedDatetime is None:
        searchedDatetime = currentDatetime
        searchedDate = currentDate
    else:
        searchedDate = searchedDatetime.strftime("%Y-%m-%d")

    a = db.session.query(Activity).all()
    activities = []
    classes = []

    # Get dates for every day in the week
    weekDayDates = [
        (
            searchedDatetime
            - datetime.timedelta(days=(searchedDatetime.weekday() % 7) - i)
        )
        for i in range(7)
    ]
    weekDayDateStrings = [dateSuffix(date.day) for date in weekDayDates]
    weekDayDatesPast = [(currentDatetime > date) for date in weekDayDates]
    # Don't show dates if not logged in.
    if accountId is None:
        weekDayDateStrings = ["" for _ in weekDayDates]
        weekDayDatesPast = [False for _ in weekDayDates]

    personalBasket = {}
    if "basket" in session:
        pb = list(
            filter(lambda bk: bk["accountId"] == current_user.id, session["basket"])
        )
        for basketItem in pb:
            personalBasket[basketItem["id"]] = True

    for act in a:
        activity = {
            "id": act.id,
            "name": act.name,
            "facilities": {},
        }
        if act.length is not None and act.length > 0:
            activity["length"] = act.length

        isClass = False
        als = (
            db.session.query(ActivityLocation)
            .filter(ActivityLocation.activityId == act.id)
            .order_by(ActivityLocation.startTime)
        )
        for al in als:
            if al.facilityId not in activity["facilities"]:
                facility = db.session.query(Facility).get(al.facilityId)
                if facility is not None:
                    activity["facilities"][al.facilityId] = facility.name
            if al.startDay and al.startTime:
                if "times" not in activity:
                    activity["times"] = {}

                bookable = True

                acl = db.session.query(ActivityLocation).get(al.id)
                if db.session.query(Facility).get(acl.facilityId) is not None:
                    if current_user.is_authenticated:
                        bookable = classBookable(
                            al.id, searchedDatetime, accountId=accountId
                        )

                dayName = numberToDay(al.startDay)
                if dayName not in activity["times"]:
                    activity["times"][dayName] = []

                classObject = {
                    "facilityId": al.facilityId,
                    "activityLocationId": al.id,
                    "start": numericToTime(al.startTime),
                    "end": numericToTime(al.startTime + act.length),
                    "bookable": bookable,
                }

                if accountId is not None and classObject["bookable"]:
                    classStart = datetime.datetime.strptime(
                        classObject["start"], "%H:%M"
                    )
                    classStart = weekDayDates[al.startDay - 1].replace(
                        hour=classStart.hour,
                        minute=classStart.minute,
                        second=0,
                        microsecond=0,
                    )
                    classEnd = datetime.datetime.strptime(classObject["end"], "%H:%M")
                    classEnd = weekDayDates[al.startDay - 1].replace(
                        hour=classEnd.hour,
                        minute=classEnd.minute,
                        second=0,
                        microsecond=0,
                    )
                    classHash = hash(
                        frozenset(
                            {
                                "accountId": accountId,
                                "activityLocation": al.id,
                                "start": classStart,
                                "end": classEnd,
                            }.items()
                        )
                    )
                    print("Checking:", classStart, classEnd, classHash)
                    if classHash in personalBasket:
                        classObject["bookable"] = False

                activity["times"][dayName].append(classObject)

                isClass = True
            elif auth:
                acl = db.session.query(ActivityLocation).get(al.id)
                if db.session.query(Facility).get(acl.facilityId) is not None:
                    periods = availableSlots(al.id, searchedDatetime)
                    if "slots" not in activity:
                        activity["slots"] = {}
                    activity["slots"][al.facilityId] = periods

        if isClass:
            classes.append(activity)
        else:
            activities.append(activity)

    return {
        "activities": activities,
        "classes": classes,
        "currentDate": currentDate,
        "searchedDate": searchedDate,
        "weekDayDates": weekDayDateStrings,
        "weekDayDatesPast": weekDayDatesPast,
    }


@app.route("/activities", methods=["GET", "POST"])
def activities():
    args = {
        "auth": current_user.is_authenticated,
    }
    if current_user.is_authenticated:
        args["accountId"] = current_user.id

    if current_user.is_authenticated and request.args.get("date") is not None:
        searchedDate = request.args.get("date")
        searchedDatetime = datetime.datetime.strptime(searchedDate, "%Y-%m-%d")
        args["searchedDatetime"] = searchedDatetime

    data = getActivityData(**args)
    # limit search to two weeks ahead
    data["maxDate"] = datetime.datetime.strftime(
        datetime.datetime.now() + datetime.timedelta(days=2 * 7), "%Y-%m-%d"
    )
    return render_template("activities.html", **data)


@login_required
@app.route("/user_booking", methods=["GET", "POST"])
def userBooking():
    if AccountTypeCheck() == "User":
        return redirect("/activities")
    users = Account.query.filter_by(accountType="User").all()
    args = {
        "auth": current_user.is_authenticated,
    }
    # if request.args.get("accountId") is not None:
    #     args["accountId"] = request.args.get("accountId")

    if current_user.is_authenticated and request.args.get("date") is not None:
        searchedDate = request.args.get("date")
        searchedDatetime = datetime.datetime.strptime(searchedDate, "%Y-%m-%d")
        args["searchedDatetime"] = searchedDatetime
    data = getActivityData(**args)
    data["users"] = users
    if request.args.get("accountId") is not None:
        account = db.session.query(Account).get(request.args.get("accountId"))
        data["accountId"] = account.id
        data["accountUsername"] = account.username
    return render_template("user_booking.html", **data)


@app.route("/bookings", methods=["GET", "POST"])
@login_required
def bookings():
    bookings = getBookings(current_user)

    membership = (
        db.session.query(Membership)
        .filter(Membership.accountId == current_user.id)
        .first()
    )

    return render_template(
        "bookings.html",
        upcomingClasses=bookings["upcoming"]["classes"],
        upcomingActivities=bookings["upcoming"]["activities"],
        pastClasses=bookings["past"]["classes"],
        pastActivities=bookings["past"]["activities"],
        membership=membership,
        user=True,
    )


@app.route("/view_user_bookings", methods=["GET", "POST"])
@login_required
def viewUserBookings():
    if AccountTypeCheck() == "User":
        return redirect("/bookings")

    users = Account.query.filter_by(accountType="User").all()
    choices = []
    for user in users:
        choices.append(user.username)

    form = SelectUser(choices=choices)

    if request.method != "POST":
        return render_template("view_user_bookings.html", form=form, users=users)

    if not form.validate_on_submit():
        logging.warning("View User Bookings: Invalid form submitted")
        return (
            render_template(
                "view_user_bookings.html",
                form=form,
                users=users,
                alert={"color": "danger", "msg": "Invalid form."},
            ),
            500,
        )

    username = form.userId.data
    user = Account.query.filter_by(username=username).first()

    membership = (
        db.session.query(Membership)
        .filter(Membership.accountId == current_user.id)
        .first()
    )

    bookings = getBookings(user)
    return render_template(
        "view_user_bookings.html",
        upcomingClasses=bookings["upcoming"]["classes"],
        upcomingActivities=bookings["upcoming"]["activities"],
        pastClasses=bookings["past"]["classes"],
        form=form,
        users=users,
        pastActivities=bookings["past"]["activities"],
        username=username,
        accountId=user.id,
        membership=membership,
        user=False,
    )


@app.route("/cancel_booking/<bookingId>", methods=["GET", "POST"])
@login_required
def cancel_booking(bookingId):
    accountId = Booking.query.get(bookingId).accountId

    redirectURL = "/bookings"
    if (
        session["accountType"] == "Manager" or session["accountType"] == "Employee"
    ) and accountId != current_user.id:
        redirectURL = "/view_user_bookings"

    booking = db.session.query(Booking).get(bookingId)
    receipt = None

    if booking.receiptId:
        receipt = db.session.query(Receipt).get(booking.receiptId)

    if (
        accountId == current_user.id
        or session["accountType"] == "Manager"
        or session["accountType"] == "Employee"
    ):
        db.session.delete(booking)
        db.session.commit()
        app.logger.info("Booking canceled")
    else:
        app.logger.info(
            "Booking cancellation failed, booking was not owned by the user"
        )
        session["alert"] = {"color": "danger", "msg": "Cancellation failed."}
        return redirect(redirectURL)

    if receipt is not None:
        refundAmount = receipt.itemPrice
        itemCount = receipt.itemCount - receipt.refundedItemCount
        refundReceiptType = "Refund"
        alert = {
            "color": "success",
            "start": "Cancelled",
            "msg": f"£{refundAmount:.2f} refunded.",
        }
        # For discounted purchases, charge full price for the uncanceled bookings, and refund the remaining money.
        if (
            receipt.refundedItemCount == 0
            and receipt.discountPct
            and receipt.discountPct > 0
            and (itemCount - 1 < 3)
        ):
            refundReceiptType = "Partial Refund"
            total = ((100 - receipt.discountPct) / 100) * (
                itemCount * float(receipt.itemPrice)
            )
            refundAmount = total - ((itemCount - 1) * float(receipt.itemPrice))
            alert[
                "msg"
            ] = f"£{refundAmount:.2f} refunded as a discount no longer applies."
            # Store that we've refunded an item so that future refunds from this purchase are for the full amount
            setattr(receipt, "refundedItemCount", receipt.refundedItemCount + 1)

        cancellationReceipt = Receipt(
            accountId=accountId,
            date=datetime.datetime.today(),
            itemCount=1,
            itemPrice=-1 * refundAmount,
            discountPct=0,
            itemName=f"{refundReceiptType}: {receipt.itemName}",
        )
        db.session.add(cancellationReceipt)

        refundBooking(receipt.stripePaymentIntentId, refundAmount)

        session["alert"] = alert

        db.session.commit()

    return redirect(redirectURL)


@app.route(
    "/add_booking/<userId>/<classOrFacility>/<activityLocationId>/<day>",
    methods=["GET", "POST"],
)
@login_required
def add_booking(userId, classOrFacility, activityLocationId, day):
    referrer = request.args.get("referrer")
    redirectURL = "/activities"
    if referrer == "user_booking":
        redirectURL = "/user_booking"

    if classOrFacility == "class":
        activityLocation = db.session.query(ActivityLocation).get(activityLocationId)
        activity = db.session.query(Activity).get(activityLocation.activityId)
    else:
        # Some jank. Since for non-class bookings the site doesn't know the activityLocation, it sends the activity and facility IDs instead, which are used here to find the AL.
        activity = db.session.query(Activity).get(activityLocationId)
        activityLocation = (
            db.session.query(ActivityLocation)
            .filter(
                and_(
                    ActivityLocation.activityId == activity.id,
                    ActivityLocation.facilityId == classOrFacility,
                )
            )
            .first()
        )

    date = datetime.datetime.strptime(day, "%Y-%m-%d")
    endDate = date
    if classOrFacility == "class":
        # Ensure booking day actually matches the class day
        while activityLocation.startDay - 1 != date.weekday():
            date += datetime.timedelta(days=1)
        startTime = numericToTuple(activityLocation.startTime)
        date = date.replace(hour=startTime[0], minute=startTime[1])
        endDate = date + datetime.timedelta(hours=activity.length)
        if not classBookable(activityLocation.id, date, accountId=current_user.id):
            session["alert"] = {"color": "danger", "msg": "Slot no longer available."}
            return redirect(redirectURL)
    else:
        startTime = datetime.datetime.strptime(request.args.get("start"), "%H:%M")
        endTime = datetime.datetime.strptime(request.args.get("end"), "%H:%M")
        date = date.replace(hour=startTime.hour, minute=startTime.minute)
        endDate = endDate.replace(hour=endTime.hour, minute=endTime.minute)
        if not activityBookable(
            activityLocation.id, date, endDate, accountId=current_user.id
        ):
            session["alert"] = {"color": "danger", "msg": "Slot no longer available."}
            return redirect(redirectURL)

    teamEvent = "Team" in activity.name

    if (
        userId != "None"
        and current_user.accountType != AccountType.User
        and referrer != "activities"
    ):
        t = Booking(
            accountId=userId,
            activityLocation=activityLocation.id,
            start=date,
            end=endDate,
            teamBooking=teamEvent,
        )
        db.session.add(t)
        db.session.commit()

        session["alert"] = {
            "color": "success",
            "start": "Success",
            "msg": "Booking created.",
        }
        return redirect("/user_booking")

    validMembership = checkMembership(current_user.id)
    if validMembership:
        t = Booking(
            accountId=current_user.id,
            activityLocation=activityLocation.id,
            start=date,
            end=endDate,
            teamBooking=teamEvent,
        )
        db.session.add(t)
        db.session.commit()
        return redirect("/bookings")

    # add to basket
    if "basket" not in session:
        session["basket"] = []

    basket = session["basket"]
    basketItem = {
        "accountId": current_user.id,
        "activityLocation": activityLocation.id,
        "start": date.strftime("%a %d/%m/%y %H:%M"),
        "end": endDate.strftime("%H:%M"),
        "teamBooking": teamEvent,
    }
    # we need some way of recognizing each booking in the basket.
    # here we generate a temporary one, which can also be used to find duplicates quickly.
    print("Hashing:", date, endDate, end="")
    basketItem["id"] = hash(
        frozenset(
            {
                "accountId": current_user.id,
                "activityLocation": activityLocation.id,
                "start": date.replace(microsecond=0),
                "end": endDate.replace(microsecond=0),
            }.items()
        )
    )
    print(", ", basketItem["id"])

    personalBasket = list(filter(lambda bk: bk["accountId"] == current_user.id, basket))
    for item in personalBasket:
        if item["id"] == basketItem["id"]:
            session["alert"] = {
                "color": "danger",
                "start": "Failed",
                "msg": "This is already in your basket.",
            }
            return redirect("/activities")

    basket.append(basketItem)

    session["basket"] = basket

    return redirect("/checkout")

    # db.session.add(t)
    # db.session.commit()

    # return redirect("/bookings")

@app.route("/checkout", methods=["GET", "POST"])
def BookingCheckout():
     print(session["basket"])
     if not "basket" in session or len(session["basket"]) == 0:
         return redirect("/pricing")

     singlePrice = (
         db.session.query(MembershipPrices)
         .filter(MembershipPrices.name == "Single")
         .first()
         .price
     )
     discount = (
         db.session.query(MembershipPrices)
         .filter(MembershipPrices.name == "Discount")
         .first()
         .price
     )
     discountString = ""
     if discount:
         discountString = str(int(discount * Decimal(100))) + "%"
     priceBeforeDiscount = Decimal(0.0)
     basket = session["basket"]
     bookings = []
     for bk in basket:
         if bk["accountId"] != current_user.id:
             continue
         booking = {"id": bk["id"], "teamBooking": bk["teamBooking"]}
         al = db.session.query(ActivityLocation).get(bk["activityLocation"])
         act = db.session.query(Activity).get(al.activityId)
         fac = db.session.query(Facility).get(al.facilityId)
         booking["name"] = act.name
         booking["facility"] = fac.name
         booking["time"] = bk["start"] + " — " + bk["end"]
         booking["price"] = singlePrice

         priceBeforeDiscount += singlePrice

         bookings.append(booking)

     totalPrice = priceBeforeDiscount
     discountSubtracted = Decimal(0.0)
     hasDiscount = False
     if len(basket) >= 3:
         withinSevenDays = True
         first = datetime.datetime.strptime(basket[0]["start"], "%a %d/%m/%y %H:%M")
         for bk in basket:
             if (
                 datetime.datetime.strptime(bk["start"], "%a %d/%m/%y %H:%M") - first
             ).days > 7:
                 withinSevenDays = False
                 break

         if withinSevenDays:
             hasDiscount = True
             discountSubtracted = totalPrice * discount
             totalPrice -= discountSubtracted

     return render_template(
         "checkout.html",
         bookings=bookings,
         priceBeforeDiscount=priceBeforeDiscount.quantize(
             Decimal(".01"), rounding=ROUND_UP
         ),
         totalPrice=totalPrice.quantize(Decimal(".01"), rounding=ROUND_UP),
         discount=hasDiscount,
         discountString=discountString,
         discountSubtracted=discountSubtracted.quantize(
             Decimal(".01"), rounding=ROUND_DOWN
         ),
     )
