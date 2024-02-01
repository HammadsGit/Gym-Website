function downloadPDF(bookingId) {
    // Clone the content element and remove the close & download buttons
    var content = document.querySelector('#popup-box' + bookingId + ' .modal-dialog').cloneNode(true);
    content.querySelector('.btn-close').remove();
    content.querySelector('.modal-footer').remove();

    let date = content.querySelector(".receipt-date").textContent;
    // Instead of using a pdf generator, simply replace the DOM with the modal content temporarily, and allow the browser to print the document.
    let originalPage = document.body.innerHTML;
    let originalTitle = document.title;
    document.title = `Booking Receipt - ${date}`;
    document.body.innerHTML = content.outerHTML;
    window.print();
    document.title = originalTitle;
    document.body.innerHTML = originalPage;
    // Reload page to preserve it's functionality
    window.location.reload();
}
