
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "nutritrack.db")


def get_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age REAL NOT NULL,
            sex TEXT NOT NULL,
            height REAL NOT NULL,
            weight REAL NOT NULL,
            muac REAL,
            weight_loss TEXT,
            weight_loss_duration TEXT,
            appetite TEXT,
            food_intake TEXT,
            symptoms TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    existing_columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(assessments)"
        ).fetchall()
    }

    new_columns = {
        "bmi": "REAL",
        "bmi_indicator": "TEXT",
        "screening_message": "TEXT",
        "weight_loss_duration": "TEXT",
        "screening_score": "INTEGER",
        "screening_category": "TEXT"
    }

    for column_name, column_type in new_columns.items():
        if column_name not in existing_columns:
            connection.execute(
                f"ALTER TABLE assessments ADD COLUMN "
                f"{column_name} {column_type}"
            )

    connection.commit()

    # Calculate BMI for older records without a BMI value
    from backend.prediction import screen_nutritional_indicator

    old_records = connection.execute("""
        SELECT id, age, height, weight
        FROM assessments
        WHERE bmi IS NULL
    """).fetchall()

    for record in old_records:
        try:
            result = screen_nutritional_indicator(
                record["age"],
                record["height"],
                record["weight"]
            )

            connection.execute("""
                UPDATE assessments
                SET bmi = ?,
                    bmi_indicator = ?,
                    screening_message = ?
                WHERE id = ?
            """, (
                result["bmi"],
                result["indicator"],
                result["message"],
                record["id"]
            ))

        except (ValueError, TypeError):
            continue

    connection.commit()
    connection.close()


def save_assessment(data, screening_result=None, nutritional_result=None):
    connection = get_connection()

    screening_result = screening_result or {}
    nutritional_result = nutritional_result or {}

    cursor = connection.execute("""
        INSERT INTO assessments (
            name,
            age,
            sex,
            height,
            weight,
            muac,
            weight_loss,
            weight_loss_duration,
            appetite,
            food_intake,
            symptoms,
            bmi,
            bmi_indicator,
            screening_message,
            screening_score,
            screening_category
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("name") or data.get("assessment_id"),
        float(data["age"]),
        data["sex"],
        float(data["height"]),
        float(data["weight"]),
        float(data["muac"]) if data.get("muac") else None,
        data.get("weight_loss"),
        data.get("weight_loss_duration"),
        data.get("appetite"),
        data.get("food_intake"),
        data.get("symptoms"),
        screening_result.get("bmi"),
        screening_result.get("indicator"),
        screening_result.get("message"),
        nutritional_result.get("screening_score"),
        nutritional_result.get("screening_category")
    ))

    connection.commit()
    assessment_id = cursor.lastrowid
    connection.close()

    return assessment_id


def get_all_assessments():
    connection = get_connection()

    records = connection.execute("""
        SELECT *
        FROM assessments
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return [dict(record) for record in records]


def get_assessment_by_id(assessment_id):
    connection = get_connection()

    record = connection.execute("""
        SELECT *
        FROM assessments
        WHERE id = ?
    """, (assessment_id,)).fetchone()

    connection.close()

    return dict(record) if record else None
