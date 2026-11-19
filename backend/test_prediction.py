from backend.prediction import screen_nutritional_indicator

result = screen_nutritional_indicator(
    age=25,
    height_cm=170,
    weight_kg=60
)

print("BMI TEST RESULT")
print("----------------")
print("BMI:", result["bmi"])
print("Indicator:", result["indicator"])
print("Message:", result["message"])