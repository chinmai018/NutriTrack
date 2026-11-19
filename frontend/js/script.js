
let riskChart = null;

async function loadDashboard() {
    try {
        const response = await fetch("/api/dashboard");

        if (!response.ok) {
            throw new Error("Unable to load dashboard data.");
        }

        const data = await response.json();

        // BMI statistics
        document.getElementById("totalAssessments").textContent =
            data.total_assessments ?? 0;

        document.getElementById("lowRisk").textContent =
            data.low_risk ?? 0;

        document.getElementById("moderateRisk").textContent =
            data.moderate_risk ?? 0;

        document.getElementById("highRisk").textContent =
            data.high_risk ?? 0;

        document.getElementById("veryHighRisk").textContent =
            data.very_high_bmi ?? 0;

        // Nutritional screening statistics
        document.getElementById("calculatedScreenings").textContent =
            data.calculated_screenings ?? 0;

        document.getElementById("noAdditionalFactors").textContent =
            data.no_additional_factors ?? 0;

        document.getElementById("factorsRequiringReview").textContent =
            data.factors_requiring_review ?? 0;

        document.getElementById("multipleFactorsRequiringReview").textContent =
            data.multiple_factors_requiring_review ?? 0;

        // Update BMI chart
        updateRiskChart(data);

        // Update latest assessment
        displayLatestAssessment(data.latest_assessment);

        document.getElementById("backendStatus").textContent =
            "Connected";

    } catch (error) {
        console.error("Dashboard error:", error);

        const status = document.getElementById("backendStatus");

        if (status) {
            status.textContent = "Connection error";
        }
    }
}


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


function displayLatestAssessment(record) {
    const container = document.getElementById("latestAssessment");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!record) {
        container.textContent = "No assessments available yet.";
        return;
    }

    const details = [
        ["Assessment ID", record.id],
        ["Name", record.name || "Not provided"],
        ["Age", record.age],
        ["BMI", record.bmi ?? "Not calculated"],
        ["BMI Indicator", record.bmi_indicator || "Not calculated"],
        ["Screening Score", record.screening_score ?? "Not calculated"],
        ["Screening Category", record.screening_category || "Not calculated"],
        ["Date", record.created_at || "Not available"]
    ];

    details.forEach(([label, value]) => {
        const paragraph = document.createElement("p");
        const strong = document.createElement("strong");

        strong.textContent = label + ": ";

        paragraph.appendChild(strong);
        paragraph.appendChild(
            document.createTextNode(String(value))
        );

        container.appendChild(paragraph);
    });
}


// Load dashboard when the page opens
document.addEventListener("DOMContentLoaded", loadDashboard);
