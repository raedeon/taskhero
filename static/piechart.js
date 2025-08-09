// Renders a pie chart of the number of each type of task

// Creates a list of dictionaries
var tasks = [
    {'type': 'Education', 'number': 0},
    {'type': 'Health', 'number': 0},
    {'type': 'Personal', 'number': 0},
    {'type': 'Social', 'number': 0},
    {'type': 'Shopping', 'number': 0},
    {'type': 'Work', 'number': 0},
    {'type': 'Others', 'number': 0},
];

// Stores the HTML table
var table = document.getElementById('table');

// Loops through each row of the table of the cell 'Type' to find the number of tasks of each type
for (var i = 1; i < table.rows.length; i++) {
    var row = table.rows[i];
    for (var j = 0; j < tasks.length; j++) {
        if (tasks[j]['type'] == row.cells[1].innerText) {
            tasks[j]['number']++;
        }
    }
};

// Converts the list of dictionaries into a list of lists
var chartdata = tasks.map(function(dict) {
    return Object.values(dict)
});

let header = ['Task Type', 'Number of Tasks'];

// Inserts an array into the start of an array of arrays via unshift method because the arratToDataTable function needs the first array to be the headers
chartdata.unshift(header);

// Loads the most current 'corechart' package from the Google Charts library. The 'corechart' package includes basic charts like pie charts, bar charts, etc.
google.charts.load('current', {'packages':['corechart']});

// Sets a callback function that will be executed once the Google Charts library is fully loaded. In this case, the callback function is drawChart.
google.charts.setOnLoadCallback(drawChart);

// This is the definition of the drawChart function. This function is responsible for creating the data for the chart and drawing the chart.
function drawChart() {

    // If the table is empty and only contains the header row
    if (table.rows.length == 1) {
        chartdata = [
            ['Task Type', 'Number'],
            ['No Data Available', 1]
        ];
    };

    // Creates the data for the chart. The data is an array of arrays, where each inner array represents a row in the chart's data table.
    var data = google.visualization.arrayToDataTable(chartdata);

    // Sets the options (an obect) for the chart. In this case, the only option set is the title of the chart.
    var options = {
    title: 'Tasks'
    };

    // Creates a new PieChart object. The chart will be drawn inside the HTML element with the id 'piechart'.
    var chart = new
    google.visualization.PieChart(document.getElementById('piechart'));

    // Draws the chart with the specified data and options.
    chart.draw(data, options);
};

