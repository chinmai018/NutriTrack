
import os
import json
from io import BytesIO
from xml.sax.saxutils import escape

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    send_file
)

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)

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


# -------------------------------
# WEB PAGES
# -------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/assessment")
def assessment():
    return render_template("assessment.html")


@app.route("/records")
def records():
    return render_template("records.html")


# -------------------------------
# HEALTH CHECK
# -------------------------------

@app.route("/api/health")
def health():
    return jsonify({"status": "healthy"})


# -------------------------------
# DASHBOARD STATISTICS
# -------------------------------

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
        "multiple_factors_requiring_review":
            multiple_factors_requiring_review,
        "calculated_screenings": calculated_screenings,
        "latest_assessment": dict(latest) if latest else None
    })


# -------------------------------
# ASSESSMENT RECORDS
# -------------------------------

@app.route("/api/assessments")
def assessment_records():
    return jsonify(get_all_assessments())


# -------------------------------
# BMI SCREENING
# -------------------------------

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


# -------------------------------
# SUBMIT ASSESSMENT
# -------------------------------

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


# -------------------------------
# PDF ASSESSMENT REPORT
# -------------------------------

@app.route("/api/assessment/<int:assessment_id>/report")
def download_assessment_report(assessment_id):

    connection = get_connection()

    record = connection.execute(
        "SELECT * FROM assessments WHERE id = ?",
        (assessment_id,)
    ).fetchone()

    connection.close()

    if record is None:
        return jsonify({
            "error": "Assessment record not found."
        }), 404

    record = dict(record)

    # Read saved nutritional factors
    factors = record.get("identified_factors") or []

    if isinstance(factors, str):
        try:
            factors = json.loads(factors)
        except (json.JSONDecodeError, TypeError):
            factors = [factors] if factors else []

    if not isinstance(factors, list):
        factors = []

    # Prepare PDF in memory
    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "NutriTrackTitle",
        parent=styles["Title"],
        fontSize=21,
        textColor=colors.HexColor("#244b45"),
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        "NutriTrackSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15
    )

    heading_style = ParagraphStyle(
        "NutriTrackHeading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#244b45"),
        spaceBefore=12,
        spaceAfter=8
    )

    normal_style = styles["BodyText"]

    story = []

    # Report heading
    story.append(
        Paragraph("NutriTrack", title_style)
    )

    story.append(
        Paragraph(
            "Intelligent Malnutrition Analysis and Early Risk Identification System",
            subtitle_style
        )
    )

    story.append(
        Paragraph("NUTRITIONAL ASSESSMENT REPORT", heading_style)
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#70b7a9")
        )
    )

    story.append(Spacer(1, 12))

    # Patient information
    story.append(
        Paragraph("1. Assessment Details", heading_style)
    )

    patient_data = [
        ["Assessment ID", str(record.get("id", "Not available"))],
        ["Name", str(record.get("name") or "Not provided")],
        ["Age", str(record.get("age") or "Not available")],
        ["Sex", str(record.get("sex") or "Not available")],
        ["Height (cm)", str(record.get("height") or "Not available")],
        ["Weight (kg)", str(record.get("weight") or "Not available")],
        ["MUAC (cm)", str(record.get("muac") or "Not recorded")],
        ["Assessment Date", str(record.get("created_at") or "Not available")]
    ]

    patient_table = Table(
        patient_data,
        colWidths=[48 * mm, 112 * mm]
    )

    patient_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#edf5f2")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#263238")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8e2df")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    story.append(patient_table)

    # BMI information
    story.append(
        Paragraph("2. BMI Screening Results", heading_style)
    )

    bmi_data = [
        ["BMI", str(record.get("bmi") or "Not calculated")],
        ["BMI Indicator", str(record.get("bmi_indicator") or "Not available")],
        [
            "Screening Message",
            str(record.get("screening_message") or "Not available")
        ]
    ]

    bmi_table = Table(
        [
            [Paragraph(escape(row[0]), normal_style),
             Paragraph(escape(row[1]), normal_style)]
            for row in bmi_data
        ],
        colWidths=[48 * mm, 112 * mm]
    )

    bmi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#edf5f2")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8e2df")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))

    story.append(bmi_table)

    # Nutritional screening
    story.append(
        Paragraph("3. Nutritional Screening Results", heading_style)
    )

    screening_data = [
        ["Screening Score", str(
            record.get("screening_score")
            if record.get("screening_score") is not None
            else "Not assessed"
        )],
        ["Screening Category", str(
            record.get("screening_category") or "Not assessed"
        )],
        ["Weight Loss Reported", str(
            record.get("weight_loss") or "Not recorded"
        )],
        ["Weight Loss Duration", str(
            record.get("weight_loss_duration") or "Not recorded"
        )],
        ["Appetite", str(record.get("appetite") or "Not recorded")],
        ["Food Intake", str(record.get("food_intake") or "Not recorded")]
    ]

    screening_table = Table(
        [
            [Paragraph(escape(row[0]), normal_style),
             Paragraph(escape(row[1]), normal_style)]
            for row in screening_data
        ],
        colWidths=[48 * mm, 112 * mm]
    )

    screening_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#edf5f2")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8e2df")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))

    story.append(screening_table)

    # Identified factors
    story.append(
        Paragraph("4. Reasons Identified", heading_style)
    )

    if factors:
        for factor in factors:
            story.append(
                Paragraph(
                    "• " + escape(str(factor)),
                    normal_style
                )
            )
            story.append(Spacer(1, 4))
    else:
        story.append(
            Paragraph(
                "No saved nutritional factor details are available for this assessment.",
                normal_style
            )
        )

    # Recommendations
    story.append(
        Paragraph("5. Suggested Next Steps", heading_style)
    )

    recommendations = []

    factor_text = " ".join(
        str(factor).lower() for factor in factors
    )

    if "weight loss" in factor_text:
        recommendations.append(
            "Discuss the reported weight loss and its duration with a healthcare professional."
        )

    if "appetite" in factor_text or "food intake" in factor_text:
        recommendations.append(
            "Discuss appetite and food intake changes with a healthcare professional."
        )

    if "bmi" in factor_text:
        recommendations.append(
            "Discuss the BMI finding with a qualified healthcare professional."
        )

    if not recommendations:
        recommendations.append(
            "Review the assessment findings with a qualified healthcare professional if there are concerns."
        )

    for recommendation in recommendations:
        story.append(
            Paragraph(
                "• " + escape(recommendation),
                normal_style
            )
        )
        story.append(Spacer(1, 4))

    # Disclaimer
    story.append(
        Paragraph("Important Disclaimer", heading_style)
    )

    disclaimer = (
        "NutriTrack provides preliminary nutritional screening information "
        "for educational and early risk identification purposes. The BMI "
        "indicator and screening score are not a medical diagnosis and do "
        "not independently establish whether a person is healthy or "
        "malnourished. A qualified healthcare professional should interpret "
        "the findings and decide whether further assessment is required."
    )

    story.append(
        Paragraph(escape(disclaimer), normal_style)
    )

    story.append(Spacer(1, 18))

    story.append(
        Paragraph(
            "Generated by NutriTrack",
            subtitle_style
        )
    )

    # Generate PDF
    document.build(story)

    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"NutriTrack_Assessment_{assessment_id}.pdf"
    )


# -------------------------------
# START APPLICATION
# -------------------------------

if __name__ == "__main__":
    print("Frontend folder:", FRONTEND_DIR)
    print("CSS file:", os.path.join(FRONTEND_DIR, "css", "style.css"))
    print(
        "CSS exists:",
        os.path.isfile(
            os.path.join(FRONTEND_DIR, "css", "style.css")
        )
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
