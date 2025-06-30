from flask import Flask, render_template, request
import pandas as pd
import requests
import joblib
from deep_translator import GoogleTranslator
from twilio.rest import Client
from datetime import datetime
import os, threading, webbrowser, logging

# ====== Logging Setup ======
logging.basicConfig(filename='flood_system.log', level=logging.INFO, format='%(asctime)s: %(message)s')

app = Flask(__name__)

# ====== Config ======
API_KEY = "b8e81941f42d67da73e92763756bcb2b"
TWILIO_SID = "AC042ff8d0d4dd593f9535bcda488ae74b"
TWILIO_AUTH_TOKEN = "564ee789804a8ff8e6bed8530ecf6521"
TWILIO_PHONE = "+18454128344"

# ====== Load Data ======
flood_data = pd.read_csv("flood_data.csv")
flood_data.columns = flood_data.columns.str.strip().str.lower()

user_data = pd.read_csv("user_data.csv")
user_data.columns = user_data.columns.str.strip().str.lower()

# ====== Load Model ======
if not os.path.exists("flood_model.pkl"):
    raise FileNotFoundError("❌ flood_model.pkl not found. Train and save the model first.")

with open("flood_model.pkl", "rb") as file:
    flood_model = joblib.load(file)

# ====== Utility Functions ======
def fetch_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    res = requests.get(url).json()
    logging.info(f"🌦️ API response for {city}: {res}")

    if "main" not in res or "wind" not in res:
        raise Exception(f"No weather data found for {city}")

    rainfall = res.get("rain", {}).get("1h", 0)
    humidity = res["main"]["humidity"]
    wind_speed = res["wind"]["speed"]
    temperature = res["main"]["temp"]
    description = res["weather"][0]["description"].title()

    return {
        "rainfall": rainfall,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "temperature": temperature,
        "description": description
    }

def send_alert_sms(name, phone, message, lang="en", real=False):
    try:
        translated = GoogleTranslator(source='auto', target=lang).translate(message)
    except Exception as e:
        translated = message + f" [Translation failed: {e}]"

    full_message = f"Dear {name}, {translated}"

    if real:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(to=phone, from_=TWILIO_PHONE, body=full_message)

    return {
        "name": name,
        "phone": phone,
        "city": "",
        "message": full_message
    }

# ====== Routes ======
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check_flood", methods=["POST"])
def check_flood_risk():
    status = []
    flood_detected = False
    cities = user_data["city"].dropna().unique()

    for city in cities:
        try:
            logging.info(f"🔍 Checking weather for {city}")
            weather = fetch_weather(city)

            input_data = pd.DataFrame([[weather["rainfall"], weather["humidity"], weather["wind_speed"]]],
                          columns=["rainfall", "humidity", "wind_speed"])
            prediction = flood_model.predict(input_data)
            predicted_type, predicted_effect = prediction[0]

            if predicted_effect.lower() in ["severe", "extreme"]:
                flood_detected = True
                affected_users = user_data[user_data["city"].str.lower() == city.lower()]
                for _, row in affected_users.iterrows():
                    name = row.get("name", "Resident")
                    phone = row.get("phone")
                    lang = row.get("lang", "en")
                    msg = f"⚠️ {predicted_type.title()} flood with {predicted_effect.title()} risk in your area. Stay safe."
                    sms_info = send_alert_sms(name, phone, msg, lang=lang)
                    sms_info.update({
                        "city": city,
                        "flood_type": predicted_type,
                        "flood_risk": predicted_effect
                    })
                    status.append(sms_info)
            else:
                status.append({
                    "name": "System",
                    "phone": "-",
                    "city": city,
                    "flood_type": predicted_type,
                    "flood_risk": predicted_effect,
                    "message": f"✅ No flood risk in {city}. Type: {predicted_type}, Risk: {predicted_effect}"
                })
        except Exception as e:
            logging.error(f"❌ Error checking {city}: {e}")
            status.append({
                "name": "System",
                "phone": "-",
                "city": city,
                "flood_type": "Error",
                "flood_risk": "N/A",
                "message": f"❌ Error in {city}: {str(e)}"
            })

    if flood_detected:
        return render_template("affected.html", status=status)
    else:
        timestamp = datetime.now().strftime("%A, %d %B %Y %I:%M %p")
        return render_template("no_flood.html", status=status, timestamp=timestamp)

@app.route("/send_result_alerts", methods=["POST"])
def send_result_alerts():
    affected_cities = request.form.getlist("affected_cities")
    status = []

    for city in affected_cities:
        try:
            logging.info(f"📦 Processing alerts for city: {city}")
            weather = fetch_weather(city)
            input_data = pd.DataFrame([[weather["rainfall"], weather["humidity"], weather["wind_speed"]]],
                          columns=["rainfall", "humidity", "wind_speed"])
            predicted_type, predicted_effect = flood_model.predict(input_data)[0]

            affected_users = user_data[user_data["city"].str.lower() == city.lower()]
            for _, row in affected_users.iterrows():
                name = row.get("name", "Resident")
                phone = row.get("phone")
                lang = row.get("lang", "en")
                msg = f"⚠️ {predicted_type.title()} flood with {predicted_effect.title()} risk in your area. Stay alert and move to safer places if needed."
                sms_info = send_alert_sms(name, phone, msg, lang=lang, real=True)
                sms_info.update({
                    "city": city,
                    "flood_type": predicted_type,
                    "flood_risk": predicted_effect
                })
                status.append(sms_info)

        except Exception as e:
            logging.error(f"❌ Error in result alerts for {city}: {e}")
            status.append({
                "name": "System",
                "phone": "-",
                "city": city,
                "flood_type": "Error",
                "flood_risk": "N/A",
                "message": f"❌ Could not process city '{city}': {str(e)}"
            })

    return render_template("result.html", status=status)

@app.route("/city_weather", methods=["GET", "POST"])
def city_weather():
    selected_city = None
    weather = None
    error = None
    timestamp = None
    city_list = sorted(user_data["city"].dropna().unique())

    if request.method == "POST":
        selected_city = request.form.get("city")
        try:
            weather = fetch_weather(selected_city)
            timestamp = datetime.now().strftime("%A, %d %B %Y %I:%M %p")
        except Exception as e:
            error = str(e)

    return render_template("city_weather.html",
                           cities=city_list,
                           selected_city=selected_city,
                           weather=weather,
                           error=error,
                           timestamp=timestamp)

# ====== Auto Open Browser ======
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

# ====== Run App ======
if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()
    app.run(debug=True)
