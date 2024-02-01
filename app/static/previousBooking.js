function showPage(pageType, pageNumber) {
    // hide all pages of the given page type
    var pages = document.getElementsByClassName(pageType + ' list-group');
    for (var i = 0; i < pages.length; i++) {
        pages[i].classList.add('d-none');
    }

    // show the selected page
    var page = document.getElementById(pageType + '-' + pageNumber);
    page.classList.remove('d-none');

    // update the active class on the pagination links
    var links = document.getElementsByClassName(pageType + ' page-item');
    for (var i = 0; i < links.length; i++) {
        links[i].classList.remove('active');
    }
    links[pageNumber].classList.add('active');
}