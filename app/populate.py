# Populates DB with initial data about facilities and such.
import sys, datetime, stripe
from app import app, db
from app.models import (
    Facility,
    Activity,
    ActivityLocation,
    Booking,
    Account,
    AccountType,
    Membership,
    MembershipPrices,
)
from app.util import numericToTuple

stripe.api_key = "sk_test_51MlDPbCvuWQSx8eZCIUKHwnf0PmQqe4Nk2KNdZkvBHUsnFNYSxA8Kb3e4Pbm7Hg2qCFYjs909XCAypquv7DLZ24F00cdEg4x2Y"


# populate fills the database with initial values from the brief.
def populate(makeBooking=False, wipeStripe=True):
    facilities = {
        "swimmingpool": Facility(
            name="Swimming Pool", capacity=30, opens=8.00, closes=20.00
        ),
        "fitnessroom": Facility(name="Fitness Room", capacity=35),
        "squashcourt1": Facility(name="Squash Court 1", capacity=4),
        "squashcourt2": Facility(name="Squash Court 2", capacity=4),
        "sportshall": Facility(name="Sports Hall", capacity=45),
        "climbingwall": Facility(
            name="Climbing Wall", capacity=22, opens=10.00, closes=20.00
        ),
        "studio": Facility(
            name="Studio",
            capacity=25,
        ),
    }

    activities = {
        "generaluse": Activity(name="General Use"),
        "laneswimming": Activity(name="Lane Swimming"),
        "lessons": Activity(name="Lessons"),
        "teamevents": Activity(name="Team Events", length=2),
        "1hoursession": Activity(name="1 Hour Session", length=1),
        "pilates": Activity(name="Pilates", length=1),
        "aerobics": Activity(name="Aerobics", length=1),
        "yoga": Activity(name="Yoga", length=1),
    }

    with app.app_context():
        print("Clearing tables...")
        db.session.query(Facility).delete()
        db.session.query(Activity).delete()
        db.session.query(ActivityLocation).delete()

        for f in facilities:
            db.session.add(facilities[f])

        for a in activities:
            db.session.add(activities[a])

        db.session.flush()
        db.session.commit()

        for f in facilities:
            print(f + ": ", facilities[f].id)

        activityLocations = [
            ActivityLocation(
                facilityId=facilities["swimmingpool"].id,
                activityId=activities["generaluse"].id,
            ),
            ActivityLocation(
                facilityId=facilities["swimmingpool"].id,
                activityId=activities["laneswimming"].id,
            ),
            ActivityLocation(
                facilityId=facilities["swimmingpool"].id,
                activityId=activities["lessons"].id,
            ),
            ActivityLocation(
                facilityId=facilities["swimmingpool"].id,
                activityId=activities["teamevents"].id,
                startDay=5,
                startTime=8.00,
            ),
            ActivityLocation(
                facilityId=facilities["swimmingpool"].id,
                activityId=activities["teamevents"].id,
                startDay=7,
                startTime=8.00,
            ),
            ActivityLocation(
                facilityId=facilities["fitnessroom"].id,
                activityId=activities["generaluse"].id,
            ),
            ActivityLocation(
                facilityId=facilities["squashcourt1"].id,
                activityId=activities["1hoursession"].id,
            ),
            ActivityLocation(
                facilityId=facilities["squashcourt2"].id,
                activityId=activities["1hoursession"].id,
            ),
            ActivityLocation(
                facilityId=facilities["sportshall"].id,
                activityId=activities["1hoursession"].id,
            ),
            ActivityLocation(
                facilityId=facilities["sportshall"].id,
                activityId=activities["teamevents"].id,
                startDay=4,
                startTime=19,
            ),
            ActivityLocation(
                facilityId=facilities["sportshall"].id,
                activityId=activities["teamevents"].id,
                startDay=6,
                startTime=9,
            ),
            ActivityLocation(
                facilityId=facilities["climbingwall"].id,
                activityId=activities["generaluse"].id,
            ),
            ActivityLocation(
                facilityId=facilities["studio"].id,
                activityId=activities["pilates"].id,
                startDay=1,
                startTime=18,
            ),
            ActivityLocation(
                facilityId=facilities["studio"].id,
                activityId=activities["aerobics"].id,
                startDay=2,
                startTime=10,
            ),
            ActivityLocation(
                facilityId=facilities["studio"].id,
                activityId=activities["aerobics"].id,
                startDay=4,
                startTime=19,
            ),
            ActivityLocation(
                facilityId=facilities["studio"].id,
                activityId=activities["aerobics"].id,
                startDay=6,
                startTime=10,
            ),
            ActivityLocation(
                facilityId=facilities["studio"].id,
                activityId=activities["yoga"].id,
                startDay=5,
                startTime=19,
            ),
            ActivityLocation(
                facilityId=facilities["studio"].id,
                activityId=activities["yoga"].id,
                startDay=7,
                startTime=9,
            ),
        ]

        for a in activityLocations:
            db.session.add(a)
            db.session.commit()

        singleMem = (
            db.session.query(MembershipPrices)
            .filter(MembershipPrices.name == "Single")
            .first()
        )
        if not singleMem:
            singleMem = MembershipPrices(
                id=0,
                name="Single",
                price=8.00,
            )

            db.session.add(singleMem)
            db.session.commit()

        monthMem = (
            db.session.query(MembershipPrices)
            .filter(MembershipPrices.name == "Month")
            .first()
        )
        if not monthMem:
            monthMem = MembershipPrices(
                id=1,
                name="Month",
                price=35.00,
            )

            db.session.add(monthMem)
            db.session.commit()

        yearMem = (
            db.session.query(MembershipPrices)
            .filter(MembershipPrices.name == "Year")
            .first()
        )
        if not yearMem:
            yearMem = MembershipPrices(
                id=2,
                name="Year",
                price=300.00,
            )

            db.session.add(yearMem)
            db.session.commit()

        discountVal = (
            db.session.query(MembershipPrices)
            .filter(MembershipPrices.name == "Discount")
            .first()
        )
        if not discountVal:
            discountVal = MembershipPrices(
                id=3,
                name="Discount",
                price=0.15,
            )

            db.session.add(discountVal)
            db.session.commit()

        acc = db.session.query(Account).filter(Account.username == "testAcc").first()
        if not acc:
            acc = Account(
                firstname="Test",
                surname="Account",
                username="testAcc",
                email="test@test.com",
                dob=datetime.datetime(year=2001, month=1, day=1),
                accountType=AccountType.User,
            )

            acc.set_password("test")
            db.session.add(acc)

            Memebership = Membership(
                accountId=acc.id,
                entryType=1,
                startDate=datetime.datetime.now(),
                endDate=datetime.datetime.now() + datetime.timedelta(days=30),
            )

            db.session.add(Memebership)
            db.session.flush()
            db.session.commit()

        acc2 = (
            db.session.query(Account).filter(Account.username == "managerAcc").first()
        )
        if not acc2:
            acc2 = Account(
                firstname="Manager",
                surname="Account",
                username="managerAcc",
                email="manager@test.com",
                dob=datetime.datetime(year=2001, month=1, day=1),
                accountType=AccountType.Manager,
            )

            acc2.set_password("test")
            db.session.add(acc2)

            db.session.flush()
            db.session.commit()

        acc3 = (
            db.session.query(Account).filter(Account.username == "employeeAcc").first()
        )
        if not acc3:
            acc3 = Account(
                firstname="Employee",
                surname="Account",
                username="employeeAcc",
                email="employee@test.com",
                dob=datetime.datetime(year=2001, month=1, day=1),
                accountType=AccountType.Employee,
            )

            acc3.set_password("test")
            db.session.add(acc3)

            db.session.flush()
            db.session.commit()

        # Clear stripe users, except for the above three accounts
        if wipeStripe:
            users = stripe.Customer.list()
            for i in range(len(users["data"])):
                accountId = ""
                if (
                    "metadata" in users["data"][i]
                    and "accountId" in users["data"][i]["metadata"]
                ):
                    accountId = users["data"][i]["metadata"]["accountId"]

                if (accountId == "") or (
                    accountId != acc.id
                    and accountId != acc2.id
                    and accountId != acc3.id
                ):
                    print(f'Deleting customer {users["data"][i]["id"]}')
                    stripe.Customer.delete(users["data"][i]["id"])

        if makeBooking:
            # 1: Team booking of Swimming Pool on 10th March 2023 from 8:00-10:00 AM
            aclHour, aclMinute = numericToTuple(activityLocations[3].startTime)
            date = datetime.datetime(
                year=2023,
                month=3,
                day=activityLocations[3].startDay + 5,
                hour=aclHour,
                minute=aclMinute,
            )
            booking = Booking(
                accountId=acc.id,
                activityLocation=activityLocations[3].id,
                start=date,
                end=date + datetime.timedelta(hours=activities["teamevents"].length),
                teamBooking=True,
            )

            db.session.add(booking)

            # 2: 25 bookings (full) of Pilates on Monday 6th March from 18:00-19:00
            aclHour, aclMinute = numericToTuple(activityLocations[12].startTime)
            date = datetime.datetime(
                year=2023,
                month=3,
                day=activityLocations[12].startDay + 5,
                hour=aclHour,
                minute=aclMinute,
            )

            for _ in range(25):
                booking = Booking(
                    accountId=acc.id,
                    activityLocation=activityLocations[12].id,
                    start=date,
                    end=date + datetime.timedelta(hours=activities["pilates"].length),
                    teamBooking=False,
                )
                db.session.add(booking)

            dateStart = datetime.datetime(
                year=2023, month=3, day=datetime.datetime.now().day, hour=15, minute=30
            )
            for _ in range(30):
                booking = Booking(
                    accountId=acc.id,
                    activityLocation=activityLocations[0].id,
                    start=dateStart,
                    end=dateStart + datetime.timedelta(minutes=30),
                    teamBooking=False,
                )
                db.session.add(booking)

            db.session.commit()
