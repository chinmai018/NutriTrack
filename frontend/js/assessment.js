
const assessmentForm = document.getElementById("assessmentForm");
const formMessage = document.getElementById("formMessage");

if (assessmentForm) {
    let resultBox = document.getElementById("screeningResult");

    if (!resultBox) {
        resultBox = document.createElement("div");
        resultBox.id = "screeningResult";
        resultBox.className = "disclaimer";
        resultBox.style.display = "none";

        formMessage.insertAdjacentElement("beforebegin", resultBox);
    }

    assessmentForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        formMessage.textContent = "Assessing nutritional information...";
        formMessage.style.color = "#17695f";
        resultBox.style.display = "none";

        const formData = new FormData(assessmentForm);
        const assessmentData = Object.fromEntries(formData.entries());

        try {
            // Save assessment and calculate screening results
            const response = await fetch("/api/assess", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(assessmentData)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || "Assessment failed.");
            }

            const bmi = result.screening_result;
            const nutrition = result.nutritional_result;

            // Display results
            resultBox.innerHTML = "";

            const heading = document.createElement("h3");
            heading.textContent = "Nutritional Screening Results";
            resultBox.appendChild(heading);

            const details = [
                ["Assessment ID", result.assessment_id],
                ["BMI", bmi.bmi],
                ["BMI Indicator", bmi.indicator],
                ["Preliminary Screening Score", nutrition.screening_score],
                ["Screening Category", nutrition.screening_category],
                ["MUAC (cm)", nutrition.muac_cm ?? "Not provided"]
            ];

            details.forEach(([label, value]) => {
                const paragraph = document.createElement("p");
                const strong = document.createElement("strong");

                strong.textContent = label + ": ";
                paragraph.appendChild(strong);
                paragraph.appendChild(
                    document.createTextNode(String(value))
                );

                resultBox.appendChild(paragraph);
            });

            const factorsHeading = document.createElement("h4");
            factorsHeading.textContent = "Identified Factors";
            resultBox.appendChild(factorsHeading);

            if (nutrition.identified_factors.length > 0) {
                const list = document.createElement("ul");

                nutrition.identified_factors.forEach(factor => {
                    const item = document.createElement("li");
                    item.textContent = factor;
                    list.appendChild(item);
                });

                resultBox.appendChild(list);
            } else {
                const paragraph = document.createElement("p");
                paragraph.textContent = "No additional factors reported.";
                resultBox.appendChild(paragraph);
            }

            const disclaimer = document.createElement("p");
            disclaimer.textContent = nutrition.message;
            resultBox.appendChild(disclaimer);

            resultBox.style.display = "block";

            formMessage.textContent = result.message;
            formMessage.style.color = "green";

            assessmentForm.reset();

        } catch (error) {
            formMessage.textContent = error.message;
            formMessage.style.color = "red";
        }
    });
}
