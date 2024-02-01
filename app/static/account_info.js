const editButton = document.getElementById("account-edit-address");
const editModeHTML = editButton.innerHTML;
const saveModeHTML = `Save <i class="ri-save-line ms-1"></i>`;
let editMode = false;

const addressFields = document.getElementById("account-address-fields").getElementsByTagName("input");

editButton.addEventListener("click", () => {
    editButton.innerHTML = editMode ? editModeHTML : saveModeHTML;
    editButton.classList.toggle("btn-warning");
    editButton.classList.toggle("btn-primary");
    for (let i = 0; i < addressFields.length; i++) {
        addressFields[i].disabled = editMode;
    }

    if (editMode) {
        editButton.setAttribute("aria-label", "Button to enable editing of address");
        let data = {};
        for (let i = 0; i < addressFields.length; i++) {
            data[addressFields[i].id.replace("account-address-", "")] = addressFields[i].value;
        }
        $.ajax({
            url: "/account_info/address",
            type: "PUT",
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify(data),
            success: () => newAlert("success", "Success", "Address saved.", 3000),
            failure: () => newAlert("danger", "Error", "Failed to save address changes.", 3000)
        });
    } else {
        editButton.setAttribute("aria-label", "Button to save changes to address");
    }
    editMode = !editMode;
});

