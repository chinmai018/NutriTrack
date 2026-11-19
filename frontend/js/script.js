
let riskChart = null;
let screeningChart = null;
let trendChart = null;
let factorChart = null;


// LOAD DASHBOARD

async function loadDashboard() {
    try {
        const dashboardResponse = await fetch("/api/dashboard");

        if (!dashboardResponse.ok) {
            throw new Error("Unable to load dashboard data.");
        }

        const dashboard = await dashboardResponse.json();

        updateDashboardStatistics(dashboard);
        updateRiskChart(dashboard);

        let records = [];

        const recordsResponse = await fetch("/api/assessments");

        if (recordsResponse.ok) {
            const recordsData = await recordsResponse.json();

            records = Array.isArray(recordsData)
                ? recordsData
                : (recordsData.assessments || recordsData.records || []);
        }

        const latestRecord = records.length
            ? records[0]
            : dashboard.latest_assessment;

        displayLatestAssessment(latestRecord);
        displayRecentAssessments(records);

        // UPDATE ANALYTICS USING REAL RECORDS
        updateScreeningChart(records);
        updateTrendChart(records);
        updateFactorChart(records);

        const backendStatus = document.getElementById("backendStatus");

        if (backendStatus) {
            backendStatus.textContent = "Connected";
        }

    } catch (error) {
        console.error("Dashboard error:", error);

        const status = document.getElementById("backendStatus");

        if (status) {
            status.textContent = "Connection error";
        }

        const latest = document.getElementById("latestAssessment");

        if (latest) {
            latest.textContent = "Unable to load assessment information.";
        }
    }
}


// UPDATE DASHBOARD STATISTICS

function updateDashboardStatistics(data) {
    const statistics = {
        totalAssessments: data.total_assessments ?? 0,
        lowRisk: data.low_risk ?? 0,
        moderateRisk: data.moderate_risk ?? 0,
        highRisk: data.high_risk ?? 0,
        veryHighRisk: data.very_high_bmi ?? 0,
        calculatedScreenings: data.calculated_screenings ?? 0,
        noAdditionalFactors: data.no_additional_factors ?? 0,
        factorsRequiringReview: data.factors_requiring_review ?? 0,
        multipleFactorsRequiringReview:
            data.multiple_factors_requiring_review ?? 0
    };

    Object.entries(statistics).forEach(([id, value]) => {
        const element = document.getElementById(id);

        if (element) {
            element.textContent = value;
        }
    });
}


// BMI CATEGORY DISTRIBUTION

function updateRiskChart(data) {
    const chartElement = document.getElementById("riskChart");

    if (!chartElement || typeof Chart === "undefined") {
        return;
    }

    const chartData = {
        labels: [
            "Low BMI",
            "Adult BMI Reference Range",
            "Higher BMI",
            "High BMI"
        ],

        datasets: [{
            label: "Assessments",

            data: [
                data.low_risk ?? 0,
                data.moderate_risk ?? 0,
                data.high_risk ?? 0,
                data.very_high_bmi ?? 0
            ],

            backgroundColor: [
                "#e8a0a0",
                "#70b7a9",
                "#e8c879",
                "#d88989"
            ],

            borderWidth: 1
        }]
    };

    if (riskChart) {
        riskChart.data = chartData;
        riskChart.update();
    } else {
        riskChart = new Chart(chartElement, {
            type: "doughnut",
            data: chartData,

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        });
    }
}


// GET IDENTIFIED FACTORS

function getFactors(record) {
    if (!record) {
        return [];
    }

    let factors = record.identified_factors || record.factors || [];

    if (typeof factors === "string") {
        try {
            factors = JSON.parse(factors);
        } catch {
            factors = factors ? [factors] : [];
        }
    }

    if (!Array.isArray(factors)) {
        return [];
    }

    return factors
        .filter(factor => factor !== null && factor !== undefined)
        .map(factor => String(factor));
}


// GET SCREENING SCORE

function getScreeningScore(record) {
    if (
        record.screening_score === null ||
        record.screening_score === undefined ||
        record.screening_score === ""
    ) {
        return null;
    }

    const score = Number(record.screening_score);

    return Number.isFinite(score) ? score : null;
}


// GET SCREENING CATEGORY

function getScreeningCategory(record) {
    const category = (record.screening_category || "").toLowerCase();
    const score = getScreeningScore(record);

    if (
        category.includes("multiple factors") ||
        (score !== null && score > 2)
    ) {
        return "Multiple Factors Requiring Review";
    }

    if (
        category.includes("factors requiring review") ||
        (score !== null && score > 0)
    ) {
        return "Factors Requiring Review";
    }

    if (
        category.includes("no additional factors") ||
        score === 0
    ) {
        return "No Additional Risk Factors Reported";
    }

    return "Not Assessed";
}


// SCREENING CATEGORY DISTRIBUTION CHART

function updateScreeningChart(records) {
    const canvas = document.getElementById("screeningChart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    const categories = {
        "No Additional Risk Factors Reported": 0,
        "Factors Requiring Review": 0,
        "Multiple Factors Requiring Review": 0
    };

    records.forEach(record => {
        const category = getScreeningCategory(record);

        if (Object.prototype.hasOwnProperty.call(categories, category)) {
            categories[category]++;
        }
    });

    const chartData = {
        labels: Object.keys(categories),

        datasets: [{
            label: "Assessments",
            data: Object.values(categories),

            backgroundColor: [
                "#70b7a9",
                "#e8c879",
                "#d88989"
            ],

            borderWidth: 1
        }]
    };

    if (screeningChart) {
        screeningChart.data = chartData;
        screeningChart.update();
    } else {
        screeningChart = new Chart(canvas, {
            type: "doughnut",
            data: chartData,

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        });
    }
}


// ASSESSMENT TRENDS CHART

function updateTrendChart(records) {
    const canvas = document.getElementById("trendChart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    const dateCounts = {};

    records.forEach(record => {
        if (!record.created_at) {
            return;
        }

        const date = String(record.created_at).substring(0, 10);

        dateCounts[date] = (dateCounts[date] || 0) + 1;
    });

    const sortedDates = Object.keys(dateCounts).sort();

    const chartData = {
        labels: sortedDates,

        datasets: [{
            label: "Assessments",
            data: sortedDates.map(date => dateCounts[date]),

            borderColor: "#477f70",
            backgroundColor: "rgba(71, 127, 112, 0.15)",

            fill: true,
            tension: 0.3
        }]
    };

    if (trendChart) {
        trendChart.data = chartData;
        trendChart.update();
    } else {
        trendChart = new Chart(canvas, {
            type: "line",
            data: chartData,

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        position: "bottom"
                    }
                },

                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
}


// FREQUENTLY IDENTIFIED FACTORS CHART

function updateFactorChart(records) {
    const canvas = document.getElementById("factorChart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    const factorCounts = {};

    records.forEach(record => {
        const factors = getFactors(record);

        factors.forEach(factor => {
            factorCounts[factor] = (factorCounts[factor] || 0) + 1;
        });
    });

    const sortedFactors = Object.entries(factorCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8);

    const chartData = {
        labels: sortedFactors.map(item => item[0]),

        datasets: [{
            label: "Number of Assessments",
            data: sortedFactors.map(item => item[1]),

            backgroundColor: "#70b7a9",
            borderWidth: 1
        }]
    };

    if (factorChart) {
        factorChart.data = chartData;
        factorChart.update();
    } else {
        factorChart = new Chart(canvas, {
            type: "bar",
            data: chartData,

            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        display: false
                    }
                },

                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
}


// DISPLAY A DETAIL ROW

function addDetail(container, label, value) {
    const paragraph = document.createElement("p");

    const strong = document.createElement("strong");
    strong.textContent = label + ": ";

    paragraph.appendChild(strong);

    paragraph.appendChild(
        document.createTextNode(
            value === null || value === undefined || value === ""
                ? "Not available"
                : String(value)
        )
    );

    container.appendChild(paragraph);
}


// DISPLAY SCREENING STATUS

function displayScreeningStatus(record) {
    const statusBox = document.getElementById("screeningStatus");

    if (!statusBox) {
        return;
    }

    statusBox.className = "screening-status";
    statusBox.innerHTML = "";

    if (!record) {
        statusBox.textContent = "No assessment available.";
        return;
    }

    const category = getScreeningCategory(record);

    let heading;
    let description;
    let statusClass;

    if (category === "Multiple Factors Requiring Review") {
        heading = "Multiple Factors Require Review";

        description =
            "Several nutritional factors have been identified. " +
            "Professional assessment is recommended.";

        statusClass = "status-high";

    } else if (category === "Factors Requiring Review") {
        heading = "Needs Review";

        description =
            "One or more nutritional factors have been identified " +
            "and should be reviewed.";

        statusClass = "status-moderate";

    } else if (category === "No Additional Risk Factors Reported") {
        heading = "No Additional Risk Factors Reported";

        description =
            "No additional tracked factors were reported. " +
            "This does not confirm that the person is medically healthy.";

        statusClass = "status-low";

    } else {
        heading = "Screening Not Available";

        description =
            "A screening result has not been calculated for this assessment.";

        statusClass = "status-unknown";
    }

    statusBox.classList.add(statusClass);

    const title = document.createElement("h3");
    title.textContent = heading;

    const message = document.createElement("p");
    message.textContent = description;

    statusBox.appendChild(title);
    statusBox.appendChild(message);
}


// GENERATE RECOMMENDATIONS

function getRecommendations(record) {
    const recommendations = [];
    const factors = getFactors(record);

    const normalizedFactors = factors.map(factor =>
        factor.toLowerCase()
    );

    if (
        normalizedFactors.some(factor =>
            factor.includes("bmi")
        )
    ) {
        recommendations.push(
            "Discuss the BMI finding with a qualified healthcare professional."
        );
    }

    if (
        normalizedFactors.some(factor =>
            factor.includes("weight loss")
        )
    ) {
        recommendations.push(
            "Seek professional review of the reported weight loss and its duration."
        );
    }

    if (
        normalizedFactors.some(factor =>
            factor.includes("appetite") ||
            factor.includes("food intake")
        )
    ) {
        recommendations.push(
            "Discuss appetite and food intake changes with a healthcare professional."
        );
    }

    if (factors.length === 0) {
        const score = getScreeningScore(record);

        if (score === 0) {
            recommendations.push(
                "No additional tracked factors were reported. This does not confirm that the person is medically healthy."
            );
        } else if (score === null) {
            recommendations.push(
                "No screening score is available for this older assessment."
            );
        } else {
            recommendations.push(
                "Factors require review, but detailed factor information is unavailable. Please review the original assessment."
            );
        }
    }

    recommendations.push(
        "This preliminary result is not a medical diagnosis. A qualified healthcare professional should interpret the findings."
    );

    return recommendations;
}


// DISPLAY LATEST ASSESSMENT

function displayLatestAssessment(record) {
    const container = document.getElementById("latestAssessment");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!record) {
        container.textContent = "No assessments available yet.";
        displayScreeningStatus(null);
        return;
    }

    displayScreeningStatus(record);

    const details = [
        ["Assessment ID", record.id ?? record.assessment_id],
        ["Name", record.name],
        ["Age", record.age],
        ["BMI", record.bmi],
        ["BMI Indicator", record.bmi_indicator],
        ["Screening Score", record.screening_score],
        ["Screening Category", record.screening_category],
        ["Date", record.created_at]
    ];

    details.forEach(([label, value]) => {
        addDetail(container, label, value);
    });


    // REASONS IDENTIFIED

    const factors = getFactors(record);

    const reasonsSection = document.createElement("div");
    reasonsSection.className = "assessment-reasons";

    const reasonsHeading = document.createElement("h4");
    reasonsHeading.textContent = "Reasons Identified";

    reasonsSection.appendChild(reasonsHeading);

    const reasonsList = document.createElement("ul");

    if (factors.length > 0) {
        factors.forEach(factor => {
            const item = document.createElement("li");
            item.textContent = factor;
            reasonsList.appendChild(item);
        });

    } else {
        const item = document.createElement("li");
        const score = getScreeningScore(record);

        if (score === 0) {
            item.textContent =
                "No additional tracked factors were reported. This does not confirm medical health.";

        } else if (score === null) {
            item.textContent =
                "This older assessment does not have saved screening factor information.";

        } else {
            item.textContent =
                "Detailed reasons are unavailable for this assessment. A professional review is recommended.";
        }

        reasonsList.appendChild(item);
    }

    reasonsSection.appendChild(reasonsList);
    container.appendChild(reasonsSection);


    // SUGGESTED NEXT STEPS

    const recommendationsSection = document.createElement("div");
    recommendationsSection.className = "assessment-recommendations";

    const recommendationsHeading = document.createElement("h4");
    recommendationsHeading.textContent = "Suggested Next Steps";

    recommendationsSection.appendChild(recommendationsHeading);

    const recommendationsList = document.createElement("ul");

    getRecommendations(record).forEach(recommendation => {
        const item = document.createElement("li");
        item.textContent = recommendation;
        recommendationsList.appendChild(item);
    });

    recommendationsSection.appendChild(recommendationsList);
    container.appendChild(recommendationsSection);
}


// DISPLAY RECENT ASSESSMENTS

function displayRecentAssessments(records) {
    const tableBody = document.getElementById("recentAssessments");

    if (!tableBody) {
        return;
    }

    tableBody.innerHTML = "";

    if (!records.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 6;
        cell.textContent = "No assessment records available.";

        row.appendChild(cell);
        tableBody.appendChild(row);

        return;
    }

    records.slice(0, 5).forEach(record => {
        const row = document.createElement("tr");

        const category = getScreeningCategory(record);

        const screeningResult =
            category === "Not Assessed"
                ? "Not assessed"
                : category;

        const values = [
            record.id ?? record.assessment_id ?? "Not available",
            record.name || "Not provided",
            record.age ?? "Not available",
            record.bmi ?? "Not calculated",
            record.bmi_indicator || "Not calculated",
            screeningResult
        ];

        values.forEach(value => {
            const cell = document.createElement("td");
            cell.textContent = String(value);
            row.appendChild(cell);
        });

        tableBody.appendChild(row);
    });
}


// LOAD DASHBOARD WHEN PAGE OPENS

document.addEventListener("DOMContentLoaded", loadDashboard);
