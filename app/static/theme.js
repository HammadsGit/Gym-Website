const toggleButton = document.getElementById("theme-toggle-button");
const icon = toggleButton.children[0];

const isDarkMode = () => {
    return (document.documentElement.getAttribute("data-bs-theme") == "dark");
};

const setButtonState = () => {
    const darkMode = isDarkMode()
    if (darkMode) {
        icon.classList.add("ri-sun-line");
        icon.classList.remove("ri-moon-line");
    } else {
        icon.classList.add("ri-moon-line");
        icon.classList.remove("ri-sun-line");
    }
};

const setDarkMode = (on) => {
    document.documentElement.setAttribute("data-bs-theme", on ? "dark" : "light");
};

const toggleTheme = (setPreference=false) => {
    const darkMode = isDarkMode();
    setDarkMode(!darkMode);
    setButtonState();

    if (setPreference) {
        // Store preference in Cookie.
        document.cookie = `prefers-color-scheme=${isDarkMode() ? "dark" : "light"}`;
    }
};


toggleButton.addEventListener("click", toggleTheme);

let preference = "none";

let cookies = decodeURIComponent(document.cookie);
let cookieList = cookies.split(";");
for (let i = 0; i < cookieList.length; i++) {
    if (!(cookieList[i].includes("prefers-color-scheme"))) continue;
    preference = cookieList[i].split("=")[1];
    break;
}


if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches && preference != "light") {
    console.log("Found color preference, setting.");
    setDarkMode(true);
} else if (preference == "light") {
    setDarkMode(false);
}
setButtonState();
