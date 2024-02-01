const specificDay = document.getElementById("activitySpecificDay");
const hideSection = document.getElementById("specificDayDependents");
const day = document.getElementById("activityStartDay");
const lengthDefined = document.getElementById("activityLengthDefined");
const length = document.getElementById("activityLength");
const addTimeslotButton = document.getElementById("add-timeslot-button");
const addTimeslotButtonCard = document.getElementById("add-timeslot-button-card");
const form = document.getElementById("activity-form");

var timeslotIndex = -1;
const appendTimeslot = (alID=null, startDay=null, startTime=null) => {
    if (alID != null) {
        lengthDefined.checked = true;
        checkLength();
    }
    if (timeslotIndex == -1)
        specificDay.checked = true;

    timeslotIndex++;
    let index = alID != null ? alID : timeslotIndex;
    const card = document.createElement("div");
    card.classList.add("card", "timeslot-card", "my-2");
    card.innerHTML = `
    <div class="card-header fs-5">
        <span class="timeslot-header">
            Timeslot ${timeslotIndex+1}
        </span>
        <span class="float-end">
            <span class="btn btn-sm btn-danger timeslot-delete">Delete &times;</span>
        </span>
    </div>
    <div class="card-body">
        <label class="form-label" for="activityStartDay${index}">Day</label>
        <div class="input-group">
            <select class="form-select" aria-label="Weekday Selection" id="activityStartDay${index}" name="activityStartDay${index}">
                <option value="1" selected>Monday</option>
                <option value="2">Tuesday</option>
                <option value="3">Wednesday</option>
                <option value="4">Thursday</option>
                <option value="5">Friday</option>
                <option value="6">Saturday</option>
                <option value="7">Sunday</option>
            </select>
        </div>
        <label class="form-label" for="activityTime${index}">Time:</label>
        <div class="input-group">
            <input class="form-control" autocomplete="off" type="time" id="activityTime${index}" name="activityTime${index}" value="${alID != null ? startTime : "08:00"}">
        </div>
    </div>
    `;

    if (startDay != null) {
        const select = card.querySelector("select");
        for (let i = 1; i <= 7; i++) {
            select.querySelector(`option[value="${i}"]`).selected = (i == startDay);
        }
    }
    card.querySelector(".timeslot-delete").addEventListener("click", () => {
        addTimeslotButtonCard.parentElement.removeChild(card);
        const timeslotCards = document.getElementsByClassName("timeslot-card");
        for (let i = 0; i < timeslotCards.length; i++) {
            timeslotCards[i].querySelector(".timeslot-header").textContent = `Timeslot ${i+1}`;
        }
        if (alID != null) {
            const hiddenInput = document.createElement("input");
            hiddenInput.classList.add("hidden");
            hiddenInput.type = "text";
            hiddenInput.name = `deleteActivityLocation${alID}`;
            hiddenInput.value = alID;
            addTimeslotButtonCard.parentElement.appendChild(hiddenInput);
        }
        timeslotIndex--;
    });

    addTimeslotButtonCard.parentElement.insertBefore(card, addTimeslotButtonCard);
}

// Called when editing an activity to fill in all necessary fields.
const setData = (activityName, activityCapacity, activityLength=null) => {
    const name = document.getElementById("activityName");
    const capacity = document.getElementById("activityCapacity");
    const length = document.getElementById("activityLength");

    name.value = activityName;
    if (activityCapacity != 0)
        capacity.value = activityCapacity;
    if (activityLength != null)
        length.value = activityLength;
};

addTimeslotButton.addEventListener("click", appendTimeslot);

const checkLength = () => {
    length.disabled = !(lengthDefined.checked);
    const timeslotCards = document.getElementsByClassName("timeslot-card");
    if (lengthDefined.checked) {
        addTimeslotButtonCard.classList.remove("hidden");
        if (timeslotCards.length > 0)
            specificDay.checked = true;
    } else {
        addTimeslotButtonCard.classList.add("hidden");
        if (timeslotCards.length > 0)
            specificDay.checked = false;
    }
    for (let i = 0; i < timeslotCards.length; i++) { 
        if (lengthDefined.checked)
            timeslotCards[i].classList.remove("hidden");
        else
            timeslotCards[i].classList.add("hidden");
    }
};

specificDay.checked = false;

lengthDefined.addEventListener("change", checkLength);

lengthDefined.checked = false;
checkLength();

form.addEventListener("formdata", (e) => {
    const data = e.originalEvent.formData;
    console.log(data);
});
