
def calculate_bmi(height_cm, weight_kg):
    height_cm = float(height_cm)
    weight_kg = float(weight_kg)

    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("Height and weight must be positive.")

    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)


def screen_nutritional_indicator(age, height_cm, weight_kg):
    age = float(age)
    bmi = calculate_bmi(height_cm, weight_kg)

    if age <= 0 or age > 120:
        raise ValueError("Please enter a valid age.")

    if age < 18:
        indicator = "Not classified"
        message = (
            "BMI requires age- and sex-specific growth references "
            "for children and adolescents."
        )
    elif bmi < 18.5:
        indicator = "Low BMI"
        message = "BMI is below the adult reference range."
    elif bmi < 25:
        indicator = "BMI in adult reference range"
        message = "BMI is within the adult reference range."
    elif bmi < 30:
        indicator = "Higher BMI"
        message = "BMI is above the adult reference range."
    else:
        indicator = "High BMI"
        message = "BMI is in the high adult BMI category."

    return {
        "bmi": bmi,
        "indicator": indicator,
        "message": (
            message + " BMI alone cannot diagnose malnutrition."
        )
    }


def assess_nutritional_factors(
    age,
    height_cm,
    weight_kg,
    muac=None,
    weight_loss=None,
    weight_loss_duration=None,
    appetite=None,
    food_intake=None
):
    bmi_result = screen_nutritional_indicator(
        age, height_cm, weight_kg
    )

    score = 0
    factors = []

    if float(age) >= 18 and bmi_result["bmi"] < 18.5:
        score += 2
        factors.append("Low adult BMI")

    if weight_loss == "yes":
        score += 2
        factors.append("Reported unintentional weight loss")

        if weight_loss_duration in (
            "less_than_1_month",
            "1_to_3_months",
            "more_than_3_months"
        ):
            factors.append(
                "Weight loss duration: "
                + weight_loss_duration.replace("_", " ")
            )

    if appetite == "reduced":
        score += 1
        factors.append("Reduced appetite")
    elif appetite == "very_low":
        score += 2
        factors.append("Very low appetite")

    if food_intake == "reduced":
        score += 1
        factors.append("Reduced food intake")
    elif food_intake == "very_low":
        score += 2
        factors.append("Very low food intake")

    muac_value = None

    if muac not in (None, ""):
        muac_value = float(muac)

        if muac_value <= 0:
            raise ValueError("MUAC must be positive.")

    if score == 0:
        category = "No additional factors reported"
    elif score <= 2:
        category = "Factors requiring review"
    else:
        category = "Multiple factors requiring review"

    return {
        "bmi": bmi_result["bmi"],
        "bmi_indicator": bmi_result["indicator"],
        "screening_score": score,
        "screening_category": category,
        "identified_factors": factors,
        "weight_loss_duration": weight_loss_duration,
        "muac_cm": muac_value,
        "message": (
            "This is an educational prototype score, not a validated "
            "clinical screening tool or medical diagnosis. "
            "A qualified healthcare professional should review the findings."
        )
    }
