const SELECTOR_METAL_RATES = '#metal_rates';
const SELECTOR_FROM_DATE = "#from_date";
const SELECTOR_TO_DATE = "#to_date";
const SELECTOR_CHART_ID = "lineChart";
const SELECTOR_SELECT_METAL = "#select_metal";
const SELECTOR_USE_FOR_UPDATES_CHART = '.use_for_updates_chart';


function fill_table() {
    return $(SELECTOR_METAL_RATES).DataTable({
        data: window.items,
        lengthMenu: [
            [5, 10, 25, 50, -1],
            ["5 записей", "10 записей", "25 записей", "50 записей", "Все записи"]
        ],
        columns: [
            { title: "Дата", data: 'date', render: date_render },
            { title: "Золото", data: 'gold', type: 'num' },
            { title: "Серебро", data: 'silver', type: 'num' },
            { title: "Платина", data: 'platinum', type: 'num' },
            { title: "Палладий", data: 'palladium', type: 'num' },
        ],
        order: [[ 0, "desc" ]],  // Сортировка по убыванию даты добавления
        language: {
            // NOTE: https://datatables.net/plug-ins/i18n/Russian.html
            search: "Поиск:",
            lengthMenu: "_MENU_",
            zeroRecords: "Записи отсутствуют.",
            info: "Записи с _START_ до _END_ из _TOTAL_",
            infoEmpty: "Записи с 0 до 0 из 0 записей",
            infoFiltered: "(отфильтровано из _MAX_ записей)",
            paginate: {
                previous: '←',
                next: '→',
            }
        },
        responsive: true,
    });
}

function fill_chart(chart_data) {
    let ctx = document.getElementById(SELECTOR_CHART_ID).getContext("2d");
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: chart_data.labels,
            datasets: [
                {
                    data: chart_data.data,
                    borderColor: chart_data.color,
                }
            ],
        },
        options: {
            legend: {
                display: false
            },
            scales: {
                xAxes: [{
                    type: 'time',
                    time: {
                        unit: chart_data.time_unit,
                        tooltipFormat: 'DD/MM/YYYY',
                        displayFormats: {
                           month: 'DD/MM/YYYY',
                        }
                    },
                    distribution: 'linear'
                }]
            },
        }
    });
}

function get_metal_color(metal) {
    // SOURCE: Цвет взят из http://mfd.ru/centrobank/preciousmetals
    switch (metal) {
        case "gold":
            return "rgb(255, 102, 10)";

        case "silver":
            return "rgb(137, 137, 137)";

        case "platinum":
            return "rgb(134, 176, 102)";

        case "palladium":
            return "rgb(97, 125, 180)";

        default:
            throw new Error('Неизвестный металл ' + metal);
    }
}

function get_chart_data() {
    let metal = $(SELECTOR_SELECT_METAL).val();
    let from_date_val = $(SELECTOR_FROM_DATE).val();
    let to_date_val = $(SELECTOR_TO_DATE).val();
    console.log(`[get_chart_data] ${metal}, ${from_date_val} - ${to_date_val}`);

    let from_date = new Date(from_date_val);
    let to_date = new Date(to_date_val);

    let color = get_metal_color(metal);

    let labels = [];
    let data = [];

    window.table.rows().every(function() {
        let row = this.data();

        let date = new Date(row.date_iso);
        if (date < from_date || date > to_date) {
            return;
        }

        labels.push(row.date_iso);
        data.push({
            x: row.date_iso,
            y: row[metal],
        });
    });

    let time_unit = labels.length > 365 ? 'year' : 'month';

    return {
        labels: labels,
        data: data,
        color: color,
        time_unit: time_unit,
    };
}

function update_chart() {
    let chart_data = get_chart_data()

    window.chart.data.datasets[0] = {
        data: chart_data.data,
        borderColor: chart_data.color,
    };
    window.chart.options.scales.xAxes[0].time.unit = chart_data.time_unit;
    window.chart.update();
}

$(document).ready(function() {
    window.table = fill_table();

    let chart_data = get_chart_data()
    window.chart = fill_chart(chart_data);

    $(SELECTOR_USE_FOR_UPDATES_CHART).change(function() {
        update_chart();
    });
});

function date_render(data, type, row, meta) {
    if (type === 'display' || type === 'filter') {
        return row.date;
    }

    return row.date_iso;
}
