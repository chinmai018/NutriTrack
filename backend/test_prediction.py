
import unittest

from backend.prediction import screen_nutritional_indicator


class TestNutritionalScreening(unittest.TestCase):

    def test_bmi_calculation(self):
        result = screen_nutritional_indicator(
            age=25,
            height_cm=170,
            weight_kg=60
        )

        self.assertAlmostEqual(result["bmi"], 20.76, places=2)

    def test_adult_bmi_reference_range(self):
        result = screen_nutritional_indicator(
            age=25,
            height_cm=170,
            weight_kg=60
        )

        self.assertEqual(
            result["indicator"],
            "BMI in adult reference range"
        )

    def test_low_bmi_category(self):
        result = screen_nutritional_indicator(
            age=25,
            height_cm=170,
            weight_kg=50
        )

        self.assertEqual(result["indicator"], "Low BMI")


if __name__ == "__main__":
    unittest.main()
