const deleteButtons = document.getElementsByClassName("checkout-delete-item");
for (let i = 0; i < deleteButtons.length; i++) {
    deleteButtons[i].addEventListener("click", () => $.ajax({
        url: `/checkout/${deleteButtons[i].id}`,
        type: "DELETE",
        success: () => {
            window.location.reload();
        }
    }));
}
