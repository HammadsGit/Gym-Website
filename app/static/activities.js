const datePicker = document.getElementById("activities-datepicker");

// changeHref updates the given anchor element to use a new userId.
function changeHref(el) {
    var hrefValue = el.getAttribute("initialhref");
    if (!hrefValue) return;
    var changedHref = hrefValue.replace("None", userId.value);
    el.href = changedHref;
}

var userId = "None";
if (window.location.href.includes("user_booking")){
    const timeslots = document.getElementsByClassName("timeslot");
    userId = document.getElementById("user-booking");
    const onUserIdChange = () => {
        for (let i = 0; i < timeslots.length; i++) {
            changeHref(timeslots[i]);
        }
    };
    userId.addEventListener("change", onUserIdChange);
    if (preSelect) {
        userId.value = preSelectId;
    }
    onUserIdChange();
}


function idFromFacilitySelector(sel) {
    const classList = sel.className.split(" ");
    for (let i = 0; i < classList.length; i++) {
        if (classList[i].includes("facility-selector-button")) continue;
        if (!(classList[i].includes("facility-selector"))) continue;
        return classList[i].replace("facility-selector-", "");
    }
    return "";
}


const activities = document.getElementsByClassName("activity-item");
var currentFacilities = {};
var currentDayEls = {};
var previouslySelected = {};

// Setup interaction with the date/time pickers on classes.
for (let i = 0; i < activities.length; i++) {
    const timePairs = [
        activities[i].querySelectorAll(".date-section-Monday"),
        activities[i].querySelectorAll(".date-section-Tuesday"),
        activities[i].querySelectorAll(".date-section-Wednesday"),
        activities[i].querySelectorAll(".date-section-Thursday"),
        activities[i].querySelectorAll(".date-section-Friday"),
        activities[i].querySelectorAll(".date-section-Saturday"),
        activities[i].querySelectorAll(".date-section-Sunday")
    ];
    
    let first = true;
    // These are only used on non-classes, so their existence means we don't have to deal
    // with date picking.
    const nonClassSections = {
        'start': activities[i].querySelectorAll(".facility-time-section-start"),
        'end': activities[i].querySelectorAll(".facility-time-section-end")
    };
    const nonClass = nonClassSections.start.length > 0;
    const multipleFacilities = activities[i].getElementsByClassName("facility-selector-button").length != 0;
    let facilitySelectors = [];
    if (multipleFacilities) {
        facilitySelectors = activities[i].querySelectorAll(".facility-selector-button");
    }
    if (nonClass) {
        const container = nonClassSections.start[0].parentElement.parentElement;
        container.querySelector(".activity-book-button").addEventListener("click", () => {
            container.querySelector(".activity-booking-area").classList.toggle("hidden");
        });
        let facilityButtonsShown = multipleFacilities ? facilitySelectors.length : 1;
        for (let j = 0; j < nonClassSections.start.length; j++) {
            let periodButtonCount = nonClassSections.start[j].getElementsByClassName("time-period-start").length;
            if (periodButtonCount > 0) continue;
            if (multipleFacilities) {
                const listElement = activities[i].querySelector(`li.facility-${idFromFacilitySelector(facilitySelectors[j])}`);
                console.log(activities[i]);
                listElement.innerHTML = `<del>${listElement.textContent}</del>`;
                facilitySelectors[j].classList.add("hidden");
                nonClassSections.start[j].classList.add("hidden");
            }
            facilityButtonsShown -= 1;
        }
        if (facilityButtonsShown == 0) {
            const container = nonClassSections.start[0].parentElement.parentElement;
            const bookButton = container.querySelector(".activity-book-button");
            bookButton.disabled = true;
            bookButton.classList.add("disabled");
            bookButton.textContent = "No slots available.";
        }
    }


    if (multipleFacilities) {
        // Find first day element so filtering by facility works
        for (let j = 0; j < timePairs.length; j++) {
            if (timePairs[j].length != 2) continue;
            currentDayEls[activities[i].id] = timePairs[j][0];
            break;
        }
        
        for (let j = 0; j < facilitySelectors.length; j++) {
            if (nonClass && facilitySelectors[j].classList.contains("hidden")) {
                facilitySelectors[j].parentElement.parentElement.removeChild(facilitySelectors[j].parentElement);
                continue;
            };

            let facilityClass = '';
            const classes = facilitySelectors[j].className.split(' ');
            // Get facilityId from class list
            for (let k = 0; k < classes.length; k++) {
                if (classes[k] == "facility-selector-button") continue;
                if (!(classes[k].includes("facility"))) continue;
                facilityClass = classes[k];
                break;
            }
            facilitySelectors[j].addEventListener("click", () => {
                facilitySelectors[j].classList.add("btn-dark");
                facilitySelectors[j].classList.remove("btn-light");
                
                currentFacilities[activities[i].id] = facilityClass.replace("facility-selector-", "");
                for (let l = 0; l < facilitySelectors.length; l++) {
                    if (l == j) continue;
                    facilitySelectors[l].classList.add("btn-light");
                    facilitySelectors[l].classList.remove("btn-dark");
                }
                
                if (nonClass) {
                    for (let k = 0; k < nonClassSections.start.length; k++) {
                        if (nonClassSections.start[k].classList.contains(`facility-${currentFacilities[activities[i].id]}`)) {
                            nonClassSections.start[k].classList.remove("hidden");
                            nonClassSections.end[k].classList.add("hidden");
                        } else {
                            nonClassSections.start[k].classList.add("hidden");
                            nonClassSections.end[k].classList.add("hidden");
                        }
                    }
                }

                // Force recheck of which times are for this facility
                if (!nonClass)
                    currentDayEls[activities[i].id].click();
            });
            if (first) {
                facilitySelectors[j].classList.add("btn-dark");
                facilitySelectors[j].classList.remove("btn-light");
                currentFacilities[activities[i].id] = facilityClass.replace("facility-selector-", "");
                if (nonClass) {
                    nonClassSections.start[0].classList.remove("hidden");
                    facilitySelectors[j].click();
                }
                first = false;
            }
        }
    }
    if (nonClass) {
        for (let j = 0; j < nonClassSections.start.length; j++) {
            const backButton = nonClassSections.end[j].querySelector(".time-end-back");
            const periods = {
                "starts": nonClassSections.start[j].querySelectorAll(".time-period-start"),
                "ends": nonClassSections.end[j].querySelectorAll(".time-period-end")
            };

            backButton.onclick = () => {
                for (let k = 0; k < periods.starts.length; k++) {
                    periods.starts[k].classList.remove("selected");
                    periods.ends[k].classList.remove("selected");
                    periods.starts[k].classList.remove("hidden");
                    periods.ends[k].classList.remove("hidden");
                    periods.starts[k].onclick = () => periodStartFunc(periods.starts[k], periods.ends[k]);
                }
                nonClassSections.start[j].classList.remove("hidden");
                nonClassSections.end[j].classList.add("hidden");
            };

            // Helper function to extract the string from a period's element.
            const stringFromPeriod = (p) => {
                const classes = p.className.split(" ");
                for (let i = 0; i < classes.length; i++) {
                    if (classes[i].startsWith("period-")) {
                        return classes[i].replace("period-", "");
                    }
                }
            };
            // Runs when clicking a period initially.
            const periodStartFunc = (periodStart, periodEnd) => {
                nonClassSections.end[j].classList.remove("hidden");
                nonClassSections.start[j].classList.add("hidden");

                periodStart.classList.add("selected");
                let periodString = stringFromPeriod(periodEnd);
                
                let currentPeriod = stringFromPeriod(periods.ends[0]);
                // Increment last period so the last time does get checked
                let lastPeriod = incrementTimeString(stringFromPeriod(periods.ends[periods.ends.length-1]), 30);


                // 1: Hide all previous periods
                while (currentPeriod != periodString) {
                    const el = periods.ends[0].parentElement.querySelector(`.period-${currentPeriod.replace(":", "\\:")}`);
                    if (el) {
                        el.classList.add("hidden");
                    }
                    currentPeriod = incrementTimeString(currentPeriod, 30);
                }

                // Loop through the remaining potential periods.
                // If we find a missing one, hide everything after it.
                let foundEnd = false;

                // Detect if this activity has a fixed length, so we can hide necessary end elements.
                let activityLength = activities[i].getAttribute("activity-length");
                // Multiply it by 60, since it was in hours
                activityLength = activityLength ? activityLength * 60 : null;
                // Counter for added time to check the above
                let minutesAdded = 0;

                while (currentPeriod != lastPeriod) {
                    const el = periods.ends[0].parentElement.querySelector(`.period-${currentPeriod.replace(":", "\\:")}`);
                    if (foundEnd && el) {
                        el.classList.add("hidden");
                    } else if (!foundEnd && !el) {
                        foundEnd = true;
                    } else if (el && activityLength && (minutesAdded % activityLength == 0 || minutesAdded > activityLength)) {
                        el.classList.add("hidden");
                    } else if (el) {
                        el.onclick = () => periodEndFunc(periodStart, el);
                    }
                    currentPeriod = incrementTimeString(currentPeriod, 30);
                    minutesAdded += 30;
                }
            }

            // Runs when selecting a period for the second time.
            const periodEndFunc = (periodStart, periodEnd) => {
                periodEnd.classList.add("selected");
                let data = {
                    "start": stringFromPeriod(periodStart),
                    "end": stringFromPeriod(periodEnd),
                    "activityId": activities[i].id
                };
                const facilityElClasses = periodStart.parentElement.className.split(" ");
                for (let l = 0; l < facilityElClasses.length; l++) {
                    if (facilityElClasses[l].includes("facility-time"))
                        continue;
                    if (facilityElClasses[l].includes("facility-")) {
                        data["facilityId"] = facilityElClasses[l].replace("facility-", "");
                        break;
                    }
                }
                
                console.log("Booking:", data);
                window.location.href = `/add_booking/${userId.value}/${data.facilityId}/${data.activityId}/${datePicker.value}?start=${data.start}&end=${data.end}&referrer=${referrer}`;
            };
            for (let l = 0; l < periods.starts.length; l++) {
                periods.starts[l].onclick = () => periodStartFunc(periods.starts[l], periods.ends[l]);
            }
        }
    }

    first = true;
    let firstEl; 
    for (let j = 0; j < timePairs.length; j++) {
        if (timePairs[j].length != 2) continue;
        timePairs[j][0].addEventListener("click", () => {
            timePairs[j][0].classList.add("btn-secondary");
            timePairs[j][0].classList.remove("btn-light");
            timePairs[j][1].classList.remove("hidden");
            currentDayEls[activities[i].id] = timePairs[j][0];
            for (let k = 0; k < timePairs.length; k++) {
                if (k == j || timePairs[k].length != 2) continue;
                timePairs[k][0].classList.add("btn-light");
                timePairs[k][0].classList.remove("btn-secondary");
                timePairs[k][1].classList.add("hidden");
                if (multipleFacilities) {
                    const individualTimes = timePairs[k][1].children;
                    let hidden = 0;
                    for (let l = 0; l < individualTimes.length; l++) {
                        if (!(individualTimes[l].classList.contains(`timeslot-facility-${currentFacilities[activities[i].id]}`))) {
                            hidden++;
                        } else {
                            hidden--;
                        }
                    }
                    if (hidden == individualTimes.length) {
                        timePairs[k][0].disabled = true;
                        timePairs[k][0].text = "No bookings available."
                    } else {
                        timePairs[k][0].disabled = false;
                        timePairs[k][0].text = ""
                    }
                }
            }
            if (multipleFacilities || timePairs[j][0].classList.contains("disabled")) {
                const individualTimes = timePairs[j][1].children;
                let hidden = 0;
                if (timePairs[j][0].classList.contains("disabled")) {
                    hidden = individualTimes.length;
                } else {
                    for (let k = 0; k < individualTimes.length; k++) {
                        if (!(individualTimes[k].classList.contains(`timeslot-facility-${currentFacilities[activities[i].id]}`))) {
                            individualTimes[k].classList.add("hidden");
                            hidden++;
                        } else {
                            individualTimes[k].classList.remove("hidden");
                            hidden--;
                        }
                    }
                }
                // If no slots available on day, check the next or previously selected day.
                console.log("checking", timePairs[j][0], "got", hidden, "/", individualTimes.length);
                if (hidden == individualTimes.length) {
                    if (previouslySelected[activities[i].id] && previouslySelected[activities[i].id] != timePairs[j][0]) {
                        previouslySelected[activities[i].id].click();
                    } else {
                        let found = false;
                        let nextDay = currentDayEls[activities[i].id];
                        nextDay = nextDay.parentElement.nextElementSibling;
                        if (nextDay && nextDay.children.length != 0) {
                            nextDay = nextDay.children[0];
                        } else {
                            nextDay = currentDayEls[activities[i].id].parentElement.parentElement.children[0].children[0];
                        }
                        nextDay.click();
                    }
                }
            }
            previouslySelected[activities[i].id] = timePairs[j][0];
        });
        if (first) {
            // timePairs[j][0].classList.add("btn-secondary");
            // timePairs[j][0].classList.remove("btn-light");
            // timePairs[j][1].classList.remove("hidden");
            currentDayEls[activities[i].id] = timePairs[j][0];
            firstEl = timePairs[j][0];
            first = false;
        }
    }
    if (firstEl) {
        // Simulate click to highlight first suitable element.
        firstEl.click();
    }
}

if (datePicker)
    datePicker.addEventListener("change", () => {
        window.location.href = window.location.href.split('?')[0] + `?date=${datePicker.value}`;
    });


