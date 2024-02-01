// Increments t (of format "<H>H:MM" by mins.
function incrementTimeString(t, mins) {
    let [hourString, minString] = t.split(":");
    let hour = parseInt(hourString);
    let min = parseInt(minString);
    min += mins;
    while (min >= 60) {
        hour++;
        min -= 60;
    }

    if (hour == 23)
        hour = 0;

    return ("0" + hour).slice(-2) + ":" + ("0" + min).slice(-2);
}
