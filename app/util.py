# numberToDay returns a string day (e.g Monday) given a number between 1-7.
def numberToDay(num):
    return [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ][num - 1]


# numericToTime takes an SQLAlchemy Numeric(2, 2) (a float) and returns a formatted time.
def numericToTime(numeric, twentyFourHour=True):
    if twentyFourHour:
        return f"{numeric:.2f}".replace(".", ":").zfill(5)
    ampm = "AM"
    if numeric >= 13.0:
        numeric -= 12.0
        ampm = "PM"
    return f"{numeric:.2f} {ampm}".replace(".", ":").zfill(8)


# numericToTuple takes an SQLAlchemy Numeric(2, 2) (a float) and returns (hour, minute).
def numericToTuple(numeric):
    return int(numeric), int((numeric - int(numeric)) * 100)


# timeToNumeric takes string t and converts it into a float for database storage.
def timeToNumeric(t):
    return float(t.replace(":", "."))


# returns date suffix for given number (i.e. th, st, nd)
def dateSuffix(date):
    if (date // 10) == 1:
        return str(date) + "th"
    remainder = date - (date // 10) * 10
    if remainder == 0:
        return str(date) + "th"
    elif remainder == 1:
        return str(date) + "st"
    elif remainder == 2:
        return str(date) + "nd"
    elif remainder == 3:
        return str(date) + "rd"

    return str(date) + "th"
