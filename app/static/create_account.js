function checkPasswordMatch() {
    var password = $("#password").val();
    var confirmPassword = $("#confirmPassword").val();

    if (password != confirmPassword) {
        newAlert("danger", "", "Passwords do not match!", 5000);
        document.getElementById("submit").disabled = true;
    } else {
        clearAlerts();
        // document.getElementById("message").innerHTML = "Passwords match";
        // document.getElementById("message").style.color = "green";
        document.getElementById("submit").disabled = false;
    }
}


