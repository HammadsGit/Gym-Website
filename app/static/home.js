(() => {
    const capacityCard = document.getElementById("capacity-card");
    const header = capacityCard.querySelector(".capacity-header");
    const headerText = header.querySelector(".capacity-header-text");
    const headerUpdated = header.querySelector(".capacity-header-updated");
    const body = capacityCard.querySelector(".capacity-body");

    var capacityUpdated = 0;


    const loadCapacity = () => $.ajax({
            url: "/facilities/all/capacity",
            type: "GET",
            dataType: "json",
            success: function(data) {


                let occupationPct = ((data["capacity"] - data["remaining"]) / data["capacity"]) * 100.0;
                // occupationPct = 35;

                // data["open"] = true;
                let paragraph = "";
                let color = "bg-primary";
                if (!data["open"]) {
                    headerText.textContent = "We're closed";
                    paragraph = "Check the facilities page to see what time we open. You can still make bookings now.";
                    color = "bg-dark";
                } else if (occupationPct <= 5) {
                    if (occupationPct == 0) {
                        headerText.textContent = "We're Empty";
                    } else {
                        headerText.textContent = "Almost Empty";
                    }
                    paragraph = "You'll have the whole place to yourself!";
                } else if (occupationPct <= 40) {
                    headerText.textContent = "Not too busy";
                    paragraph = "The gym is estimated to be only PCT full, it's a perfect time to visit!";
                    color = "bg-warning";
                } else if (occupationPct <= 70) {
                    headerText.textContent = "A little busy";
                    paragraph = "The gym is estimated to be PCT full, so your favourite weights might be taken.";
                } else {
                    color = "bg-danger";
                    headerText.textContent = "Very busy";
                    paragraph = "The gym is estimated to be PCT full, so maybe visit a little later.";
                }

                const occupants = Math.ceil((data["capacity"] - data["remaining"])/10) * 10;
                const capacity = Math.ceil(data["capacity"] / 10) * 10;
                pctString = Math.round(occupationPct) + "%";
                if (occupationPct >= 99) {
                    pctString = "";
                }
                body.innerHTML = `
                <p>${paragraph.replace("PCT", pctString)}</p>
                <div class="progress" role="progressbar" aria-label="Estimated occupants" aria-valuenow="${occupants}" aria-valuemin="0" aria-valuemax="${capacity}">
                    <div class="progress-bar ${color}" style="width: ${Math.round(occupationPct)}%;"></div>
                </div>
                `;
                capacityUpdated = 0;
            }
    });

    const capacityUpdatedCheck = () => {
        if (!headerText.textContent.includes("closed"))
            headerUpdated.textContent = `Updated ${capacityUpdated}s ago`;
        else
            headerUpdated.textContent = '';
        capacityUpdated += 1;
    };


    loadCapacity();
    setInterval(loadCapacity, 15000);
    capacityUpdatedCheck();
    setInterval(capacityUpdatedCheck, 1000);
})();
