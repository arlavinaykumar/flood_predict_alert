import pandas as pd
import joblib

# ===== Load the model =====
try:
    model = joblib.load("flood_model.pkl")
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    exit()

# ===== Test with sample data =====
# Sample format: [rainfall, humidity, wind_speed]
sample_input = pd.DataFrame([[120, 85, 15]], columns=["rainfall", "humidity", "wind_speed"])

try:
    prediction = model.predict(sample_input)
    flood_type, flood_effect = prediction[0]
    print(f"📈 Prediction on sample data:")
    print(f"   ➤ Flood Type: {flood_type}")
    print(f"   ➤ Flood Effect: {flood_effect}")
except Exception as e:
    print(f"❌ Error during prediction: {e}")
