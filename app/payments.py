import stripe
import datetime
import logging
from sqlalchemy import or_, and_
from app import app, db
from flask import render_template, request, redirect, url_for, session
from flask_login import login_required, current_user

from app.models import (
    Membership,
    MembershipPrices,
    Account,
    Receipt,
    Activity,
    Facility,
    ActivityLocation,
    Address,
    Booking,
)
from app.forms import CancelMembership
from decimal import Decimal, ROUND_UP, ROUND_DOWN

stripe.api_key = "sk_test_51MlDPbCvuWQSx8eZCIUKHwnf0PmQqe4Nk2KNdZkvBHUsnFNYSxA8Kb3e4Pbm7Hg2qCFYjs909XCAypquv7DLZ24F00cdEg4x2Y"

# Used for storing sensitive info, like payment session IDs.
localSession = {}


def checkMembership(accountId):
    return getMembership(accountId) is not None


# Check database for a valid membership, and re-verify with stripe if a subscription appears to have expired.
def getMembership(accountId):
    today = datetime.datetime.now()
    memberships = db.session.query(Membership).filter(
        Membership.accountId == current_user.id
    )
    validMembership = False
    m = None
    for membership in memberships:
        if (
            membership.startDate <= today
            and membership.endDate > today
            and membership.active
        ):
            validMembership = True
            m = membership
            break

    if validMembership:
        return m

    # Membership validity is only stored for the subscription period (a month or year). If it appears expired to us,
    # check with stripe if the subscription renewed succesfully and update the database if so.
    stripeUsers = stripe.Customer.search(
        query=f'metadata["accountId"]:"{accountId}"',
        limit=1,
        expand=["data.subscriptions"],
    )
    if len(stripeUsers["data"]) == 0:
        return None

    subs = stripeUsers["data"][0]["subscriptions"]["data"]
    validSubId = ""
    startDate = today
    endDate = today
    price = 0
    for sub in subs:
        if datetime.datetime.utcfromtimestamp(int(sub["current_period_end"])) > today:
            validSubId = sub["id"]
            startDate = datetime.datetime.utcfromtimestamp(
                int(sub["current_period_start"])
            )
            endDate = datetime.datetime.utcfromtimestamp(int(sub["current_period_end"]))
            price = float(sub["items"]["data"][0]["plan"]["amount"]) / 100.0
            break

    if validSubId == "":
        return None

    prod = stripe.Product.retrieve(
        stripe.Subscription.retrieve(validSubId)["plan"]["product"]
    )

    price = (
        db.session.query(MembershipPrices)
        .filter(MembershipPrices.name == prod["metadata"]["planPeriod"])
        .first()
    )
    membership = (
        db.session.query(Membership)
        .filter(
            and_(
                Membership.accountId == current_user.id,
                Membership.entryType == price.id,
            )
        )
        .first()
    )

    # Handle when app previously failed to register a successful payment
    if not membership:
        membership = Membership(
            accountId=accountId,
            entryType=price.id,
            startDate=startDate,
            endDate=endDate,
        )
        db.session.add(membership)

    setattr(membership, "endDate", endDate)
    setattr(membership, "active", True)

    r = Receipt(
        accountId=accountId,
        date=startDate,
        itemCount=1,
        discountPct=0,
        itemPrice=price.price,
    )

    if price.name == "Month":
        r.itemName = "Gold Subscription (1 Month)"
    else:
        r.itemName = "Platinum Subscription (1 Year)"

    db.session.add(r)

    logging.info(f"Updated membership validity for user {accountId}")
    db.session.commit()

    return membership


# deleteBasketItem removes an item from a user's basket.
# Always returns 201, since the end result is always that the basket item doesn't exist.
@app.route("/checkout/<basketItemId>", methods=["DELETE"])
@login_required
def deleteBasketItem(basketItemId):
    if "basket" not in session:
        return "", 201
    newBasket = []
    for item in session["basket"]:
        if (
            str(item["id"]) == str(basketItemId)
            and item["accountId"] == current_user.id
        ):
            continue
        newBasket.append(item)

    session["basket"] = newBasket
    return "", 201


def findOrCreateStripeUser(current_user):
    customerSearch = stripe.Customer.search(
        query=f'metadata["accountId"]:"{current_user.id}"', limit=1
    )

    if len(customerSearch.data) == 1:
        logging.debug("Found existing Stripe user")
        return customerSearch.data[0]

    address = (
        db.session.query(Address).filter(Address.accountId == current_user.id).first()
    )
    customerAddr = {}
    if address is not None:
        customerAddr = {
            "city": address.city,
            "line1": address.line1,
            "line2": address.line2,
            "postal_code": address.postcode,
        }

    logging.debug("Couldn't existing Stripe user, creating new...")

    customerDetails = {
        "address": customerAddr,
        "metadata": {"accountId": current_user.id},
        "email": current_user.email,
        "name": current_user.firstname + " " + current_user.surname,
    }

    if address is not None:
        customerDetails["phone"] = address.phone

    customer = stripe.Customer.create(**customerDetails)

    return customer


@app.route("/pay/gold", methods=["GET"])
@login_required
def payGold():
    # First, create/get a stripe user so we can bind the subscription to the user's account.
    try:
        customer = findOrCreateStripeUser(current_user)
        checkout_session = stripe.checkout.Session.create(
            line_items=[{"price": "price_1MnWN0CvuWQSx8eZDCv22dnH", "quantity": 1}],
            customer=customer.id,
            mode="subscription",
            success_url=url_for("success", _external=True, purchase_type="gold")
            + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("cancel", _external=True),
        )
    except Exception as e:
        return str(e)

    if "subscriptionCheckoutIds" not in localSession:
        localSession["subscriptionCheckoutIds"] = {}

    subscriptionCheckoutIds = localSession["subscriptionCheckoutIds"]
    subscriptionCheckoutIds[checkout_session.id] = (current_user.id, "gold")
    localSession["subscriptionCheckoutIds"] = subscriptionCheckoutIds
    return redirect(checkout_session.url)


@app.route("/pay/platinum", methods=["GET"])
@login_required
def payPlatinum():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[{"price": "price_1MoBEjCvuWQSx8eZBMNPIZqF", "quantity": 1}],
            mode="subscription",
            success_url=url_for("success", _external=True, purchase_type="platinum")
            + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("cancel", _external=True),
        )
    except Exception as e:
        return str(e)

    if "subscriptionCheckoutIds" not in localSession:
        localSession["subscriptionCheckoutIds"] = {}

    subscriptionCheckoutIds = localSession["subscriptionCheckoutIds"]
    subscriptionCheckoutIds[checkout_session.id] = (current_user.id, "platinum")
    localSession["subscriptionCheckoutIds"] = subscriptionCheckoutIds
    return redirect(checkout_session.url)


@app.route("/pay/single", methods=["GET"])
@login_required
def paySingleSession():
    if "basket" not in session or len(session["basket"]) == 0:
        return "Basket Empty.", 400

    basket = list(
        filter(lambda bk: bk["accountId"] == current_user.id, session["basket"])
    )
    args = {}
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
            discount_pct = int(
                db.session.query(MembershipPrices)
                .filter(MembershipPrices.name == "Discount")
                .first()
                .price
                * 100
            )
            coupon = stripe.Coupon.create(percent_off=discount_pct, duration="once")
            args = {"discounts": [{"coupon": coupon.id}]}
    try:
        customer = findOrCreateStripeUser(current_user)
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {"price": "price_1MnlF4CvuWQSx8eZOVvPJ5Hi", "quantity": len(basket)}
            ],
            mode="payment",
            customer=customer.id,
            success_url=url_for("success", _external=True, purchase_type="single")
            + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("BookingCheckout", _external=True),
            **args,
        )
    except Exception as e:
        return str(e)

    if "checkoutIds" not in localSession:
        localSession["checkoutIds"] = {}

    checkoutIds = localSession["checkoutIds"]
    checkoutIds[checkout_session.id] = current_user.id
    localSession["checkoutIds"] = checkoutIds
    return redirect(checkout_session.url)


@app.route("/success/<purchase_type>", methods=["GET", "POST"])
@login_required
def success(purchase_type=None):
    session_id = request.args.get("session_id")

    if purchase_type == "single":
        # Check to ensure stripe payment session is real before doing anything
        if (
            "checkoutIds" not in localSession
            or session_id not in localSession["checkoutIds"]
            or localSession["checkoutIds"][session_id] != current_user.id
        ):
            return "Basket not found.", 400
        checkoutIds = localSession["checkoutIds"]
        checkoutIds.pop(session_id)
        localSession["checkoutIds"] = checkoutIds

        checkoutSession = stripe.checkout.Session.retrieve(session_id)

        purchased = list(
            filter(lambda bk: bk["accountId"] == current_user.id, session["basket"])
        )
        discount = (
            db.session.query(MembershipPrices)
            .filter(MembershipPrices.name == "Discount")
            .first()
            .price
        )
        price = (
            db.session.query(MembershipPrices)
            .filter(MembershipPrices.name == "Single")
            .first()
            .price
        )
        r = Receipt(
            accountId=current_user.id,
            date=datetime.date.today(),
            itemCount=len(purchased),
            itemPrice=price,
            stripePaymentIntentId=checkoutSession.payment_intent,
        )
        if len(purchased) >= 3:
            withinSevenDays = True
            first = datetime.datetime.strptime(
                purchased[0]["start"], "%a %d/%m/%y %H:%M"
            )
            for bk in purchased:
                if (
                    datetime.datetime.strptime(bk["start"], "%a %d/%m/%y %H:%M") - first
                ).days > 7:
                    withinSevenDays = False
                    break

            if withinSevenDays:
                r.discountPct = int(float(discount) * 100)

        name = "Single Session:\n"
        for i, bk in enumerate(purchased):
            if i == len(purchased) - 1 and len(purchased) != 1:
                name += "\nand "
            elif i != 0:
                name += ",\n"
            acl = db.session.query(ActivityLocation).get(bk["activityLocation"])
            act = db.session.query(Activity).get(acl.activityId)
            fac = db.session.query(Facility).get(acl.facilityId)
            name += f"{act.name} ({fac.name})"

        r.itemName = name

        db.session.add(r)
        db.session.flush()

        if "basket" not in session or len(session["basket"]) == 0:
            return "Basket Empty.", 400
        newBasket = []
        for bk in session["basket"]:
            if bk["accountId"] == current_user.id:
                start = datetime.datetime.strptime(bk["start"], "%a %d/%m/%y %H:%M")
                endTime = datetime.datetime.strptime(bk["end"], "%H:%M")
                end = start.replace(hour=endTime.hour, minute=endTime.minute)
                t = Booking(
                    accountId=current_user.id,
                    activityLocation=bk["activityLocation"],
                    start=start,
                    end=end,
                    teamBooking=bk["teamBooking"],
                    receiptId=r.id,
                )
                # FIXME: Check booking not already taken
                db.session.add(t)
                continue
            newBasket.append(bk)
        db.session.commit()
        session["basket"] = newBasket

        db.session.add(r)
        db.session.commit()
    elif purchase_type == "gold":
        if (
            "subscriptionCheckoutIds" not in localSession
            or session_id not in localSession["subscriptionCheckoutIds"]
            or localSession["subscriptionCheckoutIds"][session_id][0] != current_user.id
        ):
            return "Basket not found.", 400
        subscriptionCheckoutIds = localSession["subscriptionCheckoutIds"]
        if subscriptionCheckoutIds[session_id][1] != "gold":
            return "Basket not found.", 400

        subscriptionCheckoutIds.pop(session_id)
        gold = (
            db.session.query(MembershipPrices)
            .filter(MembershipPrices.name == "Month")
            .first()
        )
        start = datetime.datetime.now()
        end = start.replace(month=start.month + 1)
        # FIXME: Ensure membership validity gets updated each month by checking w/ stripe
        r = Receipt(
            accountId=current_user.id,
            date=start,
            itemCount=1,
            itemPrice=gold.price,
            itemName="Gold Subscription (1 Month)",
        )

        m = Membership(
            accountId=current_user.id,
            entryType=gold.id,
            startDate=start,
            endDate=end,
        )

        db.session.add(r)
        db.session.add(m)
        db.session.commit()
        return redirect("/account_info")

    elif purchase_type == "platinum":
        if (
            "subscriptionCheckoutIds" not in localSession
            or session_id not in localSession["subscriptionCheckoutIds"]
            or localSession["subscriptionCheckoutIds"][session_id][0] != current_user.id
        ):
            return "Basket not found.", 400
        subscriptionCheckoutIds = localSession["subscriptionCheckoutIds"]
        if subscriptionCheckoutIds[session_id][1] != "platinum":
            return "Basket not found.", 400

        subscriptionCheckoutIds.pop(session_id)
        platinum = (
            db.session.query(MembershipPrices)
            .filter(MembershipPrices.name == "Year")
            .first()
        )
        start = datetime.datetime.now()
        end = start.replace(year=start.year + 1)
        r = Receipt(
            accountId=current_user.id,
            date=start,
            itemCount=1,
            itemPrice=platinum.price,
            itemName="Platinum Subscription (1 Year)",
        )

        m = Membership(
            accountId=current_user.id,
            entryType=platinum.id,
            startDate=start,
            endDate=end,
        )

        db.session.add(r)
        db.session.add(m)
        db.session.commit()
        return redirect("/account_info")

    return redirect(url_for("bookings"))


@app.route("/cancel", methods=["GET", "POST"])
def cancel():
    return render_template("cancel.html")


# Cancel Membership
@app.route("/cancel_membership", methods=["GET", "POST"])
@login_required
def cancelMembership():
    form = CancelMembership()

    if request.method == "POST":
        if form.validate_on_submit():
            # Get the user
            user = Account.query.get(current_user.id)
            # Get the membership
            membership = (
                db.session.query(Membership)
                .filter(Membership.accountId == user.id)
                .first()
            )
            # Set the membership to inactive
            setattr(membership, "active", False)
            # Set the cancellation reason
            setattr(membership, "cancellationReason", form.description.data)
            # Set Cancellation Date
            setattr(membership, "cancellationDate", datetime.datetime.now())
            # Commit the changes
            db.session.commit()

            # Cancel membership on stripe

            stripeUsers = stripe.Customer.search(
                query=f'metadata["accountId"]:"{user.id}"',
                limit=1,
                expand=["data.subscriptions"],
            )

            # If the user doesn't have a stripe account, return false
            if len(stripeUsers["data"]) == 0:
                return False

            if len(stripeUsers["data"][0]["subscriptions"]["data"]) != 0:
                stripe.Subscription.delete(
                    stripeUsers["data"][0]["subscriptions"]["data"][0]["id"]
                )

            # Redirect to the login page
            return render_template(
                "cancel_membership.html",
                form=form,
                alert={
                    "start": "Success",
                    "msg": "Membership Cancelled. You can continue to use your benefits until the current period expires.",
                    "color": "success",
                },
                redirect={"url": "/", "timeout": "2000"},
            )

    return render_template("cancel_membership.html", form=form)


def refundBooking(paymentIntentId, amount):
    return stripe.refund.create(
        payment_intent=paymentIntentId, amount=int(amount * 100)
    )
