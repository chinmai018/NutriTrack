
import os
from flask import Flask, render_template, jsonify, request

from backend.database import (
    initialize_database,
    save_assessment,
    get_connection,
    get_all_assessments
)

from backend.prediction import (
    screen_nutritional_indicator,
    assess_nutritional_factors
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(
    __name__,
    template_folder=FRONTEND_DIR,
    static_folder=FRONTEND_DIR,
    static_url_path="/static"
)

initialize_database()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/assessment")
def assessment():
    return render_template("assessment.html")


@app.route("/records")
def records():
    return render_template("records.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/dashboard")
def dashboard():
    connection = get_connection()

    total = connection.execute(
        "SELECT COUNT(*) FROM assessments"
    ).fetchone()[0]

    low_bmi = connection.execute("""
        SELECT COUNT(*) FROM assessments
        WHERE bmi_indicator = 'Low BMI'
    """).fetchone()[0]

    normal_bmi = connection.execute("""
        SELECT COUNT(*) FROM assessments
        WHERE bmi_indicator = 'BMI in adult reference range'
    """).fetchone()[0]

    higher_bmi = connection.execute("""
        SELECT COUNT(*) FROM assessments
        WHERE bmi_indicator = 'Higher BMI'
    """).fetchone()[0]

    high_bmi = connection.execute("""
        SELECT COUNT(*) FROM assessments
        WHERE bmi_indicator = 'High BMI'
    """).fetchone()[0]

    no_additional_factors = connection.execute("""
        SELECT COUNT(*) FROM assessments
        WHERE screening_category = 'No additional factors reported'
    """).fetchone()[0]

    factors_requiring_review = connection.execute("""
        SELECT COUNT(*) FROM assessments
        WHERE screening_category = 'Factors requiring review'
    """).fetchone()[0]

    multiple_factors_requiring_review = connection.execute("""
        SELECT COUNT(*) FROM assessments
        WHERE screening_category = 'Multiple factors requiring review'
    """).fetchone()[0]

    calculated_screenings = connection.execute("""
        SELECT COUNT(*) FROM assessments
        WHERE screening_score IS NOT NULL
    """).fetchone()[0]

    latest = connection.execute("""
        SELECT id, name, age, bmi, bmi_indicator, created_at,
               screening_score, screening_category
        FROM assessments
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()

    connection.close()

    return jsonify({
        "total_assessments": total,
        "low_risk": low_bmi,
        "moderate_risk": normal_bmi,
        "high_risk": higher_bmi,
        "very_high_bmi": high_bmi,
        "no_additional_factors": no_additional_factors,
        "factors_requiring_review": factors_requiring_review,
        "multiple_factors_requiring_review": multiple_factors_requiring_review,
        "calculated_screenings": calculated_screenings,
        "latest_assessment": dict(latest) if latest else None
    })


@app.route("/api/assessments")
def assessment_records():
    return jsonify(get_all_assessments())


@app.route("/api/screen", methods=["POST"])
def screen_assessment():
    data = request.get_json(silent=True) or {}

    try:
        result = screen_nutritional_indicator(
            data["age"],
            data["height"],
            data["weight"]
        )
        return jsonify(result)

    except (KeyError, ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400


@app.route("/api/assess", methods=["POST"])
def submit_assessment():
    data = request.get_json(silent=True) or {}

    required_fields = ["age", "sex", "height", "weight"]

    for field in required_fields:
        if data.get(field) is None or str(data[field]).strip() == "":
            return jsonify({
                "error": f"Please provide {field}."
            }), 400

    try:
        age = float(data["age"])
        height = float(data["height"])
        weight = float(data["weight"])

        if not 0 < age <= 120:
            raise ValueError("Please enter a valid age.")

        if not 0 < height <= 250:
            raise ValueError("Please enter a valid height.")

        if not 0 < weight <= 500:
            raise ValueError("Please enter a valid weight.")

        screening_result = screen_nutritional_indicator(
            age, height, weight
        )

        nutritional_result = assess_nutritional_factors(
            age=age,
            height_cm=height,
            weight_kg=weight,
            muac=data.get("muac"),
            weight_loss=data.get("weight_loss"),
            weight_loss_duration=data.get("weight_loss_duration"),
            appetite=data.get("appetite"),
            food_intake=data.get("food_intake")
        )

        assessment_id = save_assessment(
            data,
            screening_result,
            nutritional_result
        )

    except (ValueError, TypeError, KeyError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({
        "message": "Assessment saved successfully!",
        "assessment_id": assessment_id,
        "screening_result": screening_result,
        "nutritional_result": nutritional_result
    }), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
