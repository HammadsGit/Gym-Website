// Model used for generating diagrams
Table Account {
    id int [pk]
    firstname varchar
    surname varchar
    username varchar
    password varchar
    email varchar
    dob date
    accountType int
}

Table CardDetails {
    id int [pk]
    name varchar
    accountId int [ref: > Account.id]
    addressId int [ref: > Address.id]
    cardNumber varchar
    expiryMonth int
    expiryYear int
    cvv int
}


Table Address {
    id int [pk]
    accountId int [ref: > Account.id]
    line1 varchar
    line2 varchar
    line3 varchar
    city varchar
    postcode varchar
    country varchar
    phone varchar
}

Table Receipt {
    id int [pk]
    accountId int [ref: > Account.id]
    cardDetailsId int [ref: > CardDetails.id]
    date date
    discountPct int
    itemName varchar
    itemCount int
    itemPrice numeric
}

Table Membership {
    id int [pk]
    accountId int [ref: > Account.id]
    entryType int
    count int
    startDate date
    endDate date
}

Table Facility {
    id int [pk]
    name varchar
    capacity int
    opens numeric
    closes numeric
}

Table Activity {
    id int [pk]
    name varchar
    length int
    capacity int
}

Table ActivityLocation {
    id int [pk]
    facilityId int [ref: > Facility.id]
    activityId int [ref: > Activity.id]
    startDay int
    startTime numeric
}

Table Booking {
    id int [pk]
    accountId int [ref: > Account.id]
    activityLocation int [ref: > ActivityLocation.id]
    start date
    end date
    teamBooking boolean
}
