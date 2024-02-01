google.charts.load("current", {packages:['corechart']});
google.charts.setOnLoadCallback(drawChart);
google.charts.setOnLoadCallback(drawStuff);

function drawChart() {

    let w = data_js.Width;
    let h = data_js.Height;
    let matrix = data_js.Matrix;
    console.log(w);
    console.log(h);
    console.log(matrix);

    let graphMatrix = [['Activity']]
    for(let i = 0; i < h; i++) {
        for(let j = 0; j < w; j++) {
            if(i != 0) {
                let found = false;
                for(let k = 0; k < graphMatrix[0].length; k++) {
                    if(matrix[i][j][0] == graphMatrix[0][k]) {
                        found = true;
                        break;
                    }
                }

                if(found == false) {
                    graphMatrix[0].push(matrix[i][j][0]);
                }
            }
        }
    }

    for(let i = 0; i < graphMatrix[0].length; i++) {
        if(graphMatrix[0][i] == "") {
            graphMatrix[0].splice(i, 1);
        }
    }

    for(let i = 0; i < h-1; i++) {
        graphMatrix.push([]);
        graphMatrix[i+1][0] = matrix[0][i][0];
    }

    for(let i = 0; i < h-1; i++) {
        if(matrix[0][i][0] == graphMatrix[i+1][0]) {
            for(let j = 0; j < w; j++) {
                for(let k = 0; k < graphMatrix[0].length; k++) {
                    if(matrix[i+1][j][0] == graphMatrix[0][k]) {
                        graphMatrix[i+1][k] = matrix[i+1][j][1];
                        break;
                    }
                }
            }
        }
    }
    
    let maxMatrixWidth = 0;

    for(let i = 0; i < h; i++) {
        if (graphMatrix[i].length > maxMatrixWidth)
            maxMatrixWidth = graphMatrix[i].length;

        for(let j = 0; j < graphMatrix[0].length; j++) {
            if(graphMatrix[i][j] == undefined) {
                graphMatrix[i][j] = 0;
            }
        }
    }
    
    console.log(graphMatrix);
    console.log("Max width:", maxMatrixWidth);

    if (maxMatrixWidth < 2) {
        console.log("No data found.");
        // const usageBody = document.getElementById("columnchart_values");
        return;
    }

    let columnOptions = []
    let num = 0
    for(let i = 0; i < graphMatrix[0].length-1; i++) {
        columnOptions.push(i);
        num += 1;
    }

    columnOptions.push({calc: "stringify", type: "string", role: "annotation"});
    columnOptions.push(num);

    console.log(columnOptions);

    var data = google.visualization.arrayToDataTable(graphMatrix);

    var view = new google.visualization.DataView(data);
    view.setColumns(columnOptions);

    var options = {
    title: "Usage chart",
    subtitle: "Usage per facility per activity",
    legend: { position: 'top', maxLines: 3 },
    bar: { groupWidth: '75%' },
    isStacked: true,
    vAxes: {
        0: {title: 'Number of bookings'}
    }
    };

    const chartBody = document.getElementById("columnchart_values");
    chartBody.style = "width: 100%; height: 500px;";

    var chart = new google.visualization.ColumnChart(chartBody);
    chart.draw(view, options);
}

google.charts.load('current', {'packages':['corechart', 'bar']});

function drawStuff() {

    usage = data_js.Usage;

    var chartDiv = document.getElementById('chart_div');

    var data = google.visualization.arrayToDataTable([
        ['Membership types', 'Profit', 'No. of sales', 'No. of active'],
        usage[0],
        usage[1],
        usage[2]
    ]);

    var classicOptions = {
        series: {
        0: {targetAxisIndex: 0},
        1: {targetAxisIndex: 1},
        2: {targetAxisIndex: 1}
        },
        title: 'Sales and profit',
        legend: { position: 'top', maxLines: 3 },
        bar: { groupWidth: '75%' },
        vAxes: {
        // Adds titles to each axis.
        0: {title: 'Profit'},
        1: {title: 'Number of people'}
        }
    };

    chartDiv.style = "width: 100%; height: 500px";
    var classicChart = new google.visualization.ColumnChart(chartDiv);
    classicChart.draw(data, classicOptions);

}
