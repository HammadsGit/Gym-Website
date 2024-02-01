import enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


# Enum AccountType represents the whether the account belongs to a manager, employee or user.
class AccountType(enum.Enum):
    User = 0
    Employee = 1
    Manager = 2


# Class Account represents an account of GymCorp, and stores most personal details.
class Account(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50), index=True)
    surname = db.Column(db.String(50), index=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False, unique=False)
    facebookid = db.Column(db.String(200), nullable=True, unique=True)
    googleid = db.Column(db.String(200), nullable=True, unique=True)

    # Hashes password before storing
    def set_password(self, password):
        self.password = generate_password_hash(password, method="sha256")

    # Helper function to compare passwords in hash form.
    def check_password(self, password):
        return check_password_hash(self.password, password)

    email = db.Column(db.String(100), nullable=False, unique=True)
    dob = db.Column(db.DateTime, nullable=True, unique=False)
    address = db.relationship("Address", backref="account", lazy="dynamic")

    # Type of account. See AccountType enum for options.
    generatedPassword = db.Column(db.Boolean, default=False)
    accountType = db.Column(
        db.Enum(AccountType), nullable=False, default=AccountType.User
    )


# Class CardDetails stores the card details of a user, including card details and address.
# class CardDetails(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50), index=True)
#     accountId = db.Column(db.Integer, db.ForeignKey("account.id"))
#     addressId = db.Column(db.Integer, db.ForeignKey("address.id"))
#     cardNumber = db.Column(db.String(20), nullable=False)
#     expiryMonth = db.Column(db.Integer, nullable=False)
#     expiryYear = db.Column(db.Integer, nullable=False)
#     cvv = db.Column(db.Integer, nullable=False)


# Class Address stores the address of an account, with different meanings based on context.
# Represents a home address or a billing address, depending on
# which of accountId & cardDetailsId is set.
class Address(db.Model):
    # Constraint to ensure an address is mapped to either an Account or set of Payment details.
    __table_args__ = (db.CheckConstraint("NOT(accountId IS NULL)"),)
    id = db.Column(db.Integer, primary_key=True)
    accountId = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=True)
    line1 = db.Column(db.String(200), nullable=True, unique=False)
    line2 = db.Column(db.String(200), nullable=True, unique=False)
    line3 = db.Column(db.String(200), nullable=True, unique=False)
    city = db.Column(db.String(100), nullable=True, unique=False)
    postcode = db.Column(db.String(100), nullable=True, unique=False)
    country = db.Column(db.String(100), nullable=True, unique=False)
    phone = db.Column(db.String(100), nullable=True, unique=False)


# Class Receipt stores details of a purchase by a user, including card details and price.
class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accountId = db.Column(db.Integer, db.ForeignKey("account.id"))
    date = db.Column(db.Date, nullable=False)
    discountPct = db.Column(db.Integer)
    itemName = db.Column(db.String(100), nullable=False)
    itemCount = db.Column(db.Integer, nullable=False)
    refundedItemCount = db.Column(db.Integer, nullable=False, default=0)
    # Store price as Numeric to avoid floating point issues.
    # Allowed 3 integer places for pounds, 2 for pence.
    itemPrice = db.Column(db.Numeric(3, 2), nullable=False)
    # Used for processing refunds.
    stripePaymentIntentId = db.Column(db.String(100))
    # Total Price = (100-discountPct)/100 * (itemPrice * itemCount)


# Class EntryType represents holds the different membership prices and discount value.
class MembershipPrices(db.Model):
    id = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(3, 2), nullable=False)


# Class Membership stores user's Gym memberships as well as one-time passes.
class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accountId = db.Column(db.Integer, db.ForeignKey("account.id"))
    # Type of pass. See EntryType enum for options.
    entryType = db.Column(
        db.Integer, db.ForeignKey(MembershipPrices.id), nullable=False
    )
    # Number of membership passes/single entries remaining.
    count = db.Column(db.Integer, nullable=True)
    startDate = db.Column(db.DateTime, nullable=True)
    endDate = db.Column(db.DateTime, nullable=True)
    bookedActivity = db.Column(db.Integer, db.ForeignKey("booking.id"))
    # If membership is active.
    active = db.Column(db.Boolean, default=True)
    cancellationReason = db.Column(db.String(100), nullable=True)
    cancellationDate = db.Column(db.DateTime, nullable=True)


# Class Facility stores details about Gym facilities.
class Facility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True, nullable=False)
    capacity = db.Column(db.Integer)
    activities = db.relationship("ActivityLocation", backref="facility", lazy="dynamic")
    # Opening and closing time
    opens = db.Column(db.Numeric(2, 2), default=8.00)
    closes = db.Column(db.Numeric(2, 2), default=22.00)


# Class Activity stores details about activities, such as location, capacity, etc.
class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), index=True)
    # If length not given, length can be specified in booking.
    length = db.Column(db.Integer)
    capacity = db.Column(db.Integer)
    # Links to instances of activities in each location.
    facilities = db.relationship("ActivityLocation", backref="activity", lazy="dynamic")


# Class ActivityLocation maps activities to their location (facility),
# and in the case of classes, their start time.
class ActivityLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    facilityId = db.Column(db.Integer, db.ForeignKey("facility.id"))
    activityId = db.Column(db.Integer, db.ForeignKey("activity.id"))
    # Start time (only relevant to classes)
    # Start day, where 1 = Monday.
    startDay = db.Column(db.Integer)
    startTime = db.Column(db.Numeric(2, 2))


# Class Booking stores booking details for activities.
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accountId = db.Column(db.Integer, db.ForeignKey("account.id"))
    activityLocation = db.Column(db.Integer, db.ForeignKey(ActivityLocation.id))
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    # Whether or not the booking is for a team
    # If so, the facility is fully occupied.
    teamBooking = db.Column(db.Boolean, default=False)
    receiptId = db.Column(db.Integer, db.ForeignKey("receipt.id"))
