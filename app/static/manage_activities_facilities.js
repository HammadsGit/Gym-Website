function updateFacilityName(facility) {
    $.ajax({
        url: "/manage_activities_facilities",
        type: "POST",
        data: {
            function: "updateFacilityName",
            facilityID: facility.id,
            facilityName: facility.value
        },
        success: () => {},
        error: () => {
            newAlert("danger", "Error", "Failed to update name.", 5000);
        }
    });
}

function updateFacilityCapacity(facility) {
    $.ajax({
            url: "/manage_activities_facilities",
            type: 'POST',
            data: {
                function: "updateFacilityCapacity",
                facilityID: facility.id,
                facilityCapacity: facility.value
            },
            success: function (response) {
            },
            error: function (response) {
            }
    })
}
function updateFacilityOpen(facility) {
    $.ajax({
            url: "/manage_activities_facilities",
            type: 'POST',
            data: {
                function: "updateFacilityOpen",
                facilityID: facility.id,
                time: facility.value
            },
            success: function (response) {
            },
            error: function (response) {
            }
    })
}
function updateFacilityClose(facility) {
    $.ajax({
            url: "/manage_activities_facilities",
            type: 'POST',
            data: {
                function: "updateFacilityClose",
                facilityID: facility.id,
                time: facility.value
            },
            success: function (response) {
            },
            error: function (response) {
            }
    })
}

function updateFacilityActivities(activity) {
    $.ajax({
            url: "/manage_activities_facilities",
            type: 'POST',
            data: {
                function: "updateFacilityActivities",
                facilityID: activity.name,
                activityName: activity.name,
                activityNew: activity.value
            },
            success: function (response) {
                window.location.reload();
            },
            error: function (response) {
            }
    })
}

const mappings = {
    "facility-name": updateFacilityName,
    "facility-capacity": updateFacilityCapacity,
    "facility-opens": updateFacilityOpen,
    "facility-closes": updateFacilityClose,
    "facility-activity": updateFacilityActivities,
};

for (const className in mappings) {
    const els = document.getElementsByClassName(className);
    for (let i = 0; i < els.length; i++) {
        els[i].addEventListener("change", () => mappings[className](els[i]));
    }
}
