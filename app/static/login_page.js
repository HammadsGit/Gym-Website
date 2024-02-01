const pairs = [[document.getElementById("login-list"), document.getElementById("login-list-button")],
               [document.getElementById("signup-list"), document.getElementById("signup-list-button")]];

const apply = (clicked) => {
    for (let j = 0; j < pairs.length; j++) {
        if (pairs[j][1].id == clicked.id) {
            pairs[j][1].classList.add("btn-dark");
            pairs[j][1].classList.remove("btn-light");
            pairs[j][0].classList.remove("hidden");
        } else {
            pairs[j][1].classList.add("btn-light");
            pairs[j][1].classList.remove("btn-dark");
            pairs[j][0].classList.add("hidden");
        }
    }
}

for (let i = 0; i < pairs.length; i++) {
    pairs[i][1].addEventListener("click", () => apply(pairs[i][1]));
}

apply(pairs[0][1]);
