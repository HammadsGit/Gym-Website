function updateType(options) {
    const userId = options.parentElement.parentElement.children[0].textContent;
    $.ajax({
            url: "/manage_staff",
            type: 'POST',
            data: {
                function: "updateType",
                userID: userId,
                option: options.value
            },
            success: function (response) {
                window.location.reload();
            },
            error: function (response) {
            }
    })
}

const accountTypeSelections = document.getElementsByClassName("manage-account-type");
for (let i = 0; i < accountTypeSelections.length; i++) {
    accountTypeSelections[i].addEventListener("change", () => updateType(accountTypeSelections[i]));
}
