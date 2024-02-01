// Use the last alert box on the page
// This means the default, floating one will be used unless
// the page adds its own one.
let alertBoxes = document.getElementsByClassName("alert-box");
const alertBox = alertBoxes[alertBoxes.length-1];
// function newAert creates a floating popup box with a message
// with options to change color and to set a timeout for it to disappear.
function newAlert(color, start, msg, timeout) {
    const alertDiv = document.createElement("div");
    let alertType = `alert-${color ? color : "primary"}`;
    alertDiv.classList.add("alert", alertType, "alert-dismissible", "fade");
    alertDiv.setAttribute("role", "alert");
    alertDiv.innerHTML = `
    <span class="fw-bold">${start}${start ? ":" : ""}</span>
    <span>${msg}</span>
    <span type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close Message"></span>
    `;
    
    // If "single" tag is on the alert box, only show one alert
    // at a time. Also don't fade in.
    const single = alertBox.classList.contains("single");
    if (single) {
        alertBox.textContent = "";
        alertDiv.classList.remove("fade");
    }
    alertBox.appendChild(alertDiv);
    if (!single)
        alertDiv.classList.add("show");

    if (timeout != 0) {
        const bsAlert = new bootstrap.Alert(alertDiv);
        setTimeout(
            () => bsAlert.close(),
            timeout
        );
    }
}

// function clearAlerts will empty the alert box.
function clearAlerts() {
    alertBox.textContent = "";
}
