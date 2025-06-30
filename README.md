# flood_predict_alert
A Flask-based web application that predicts flood risks using real-time weather data and a trained machine learning model. The system sends multilingual SMS alerts to users in high-risk areas via Twilio.

 Features
🌦️ Real-Time Weather Fetching via OpenWeatherMap API

🤖 Flood Prediction using a pre-trained ML model (flood_model.pkl)

📲 SMS Alerts through Twilio with language translation (Google Translate API)

📋 User and City Management via user_data.csv

📈 City-specific Weather Dashboard

🛠️ Automatic Logging and browser launch on app start

🧰 Technologies
Flask (Python web framework)

Pandas (data handling)

Joblib (model loading)

Twilio (SMS alerts)

Google Translator (multilingual support)

OpenWeatherMap API (weather data)

🚀 Getting Started
Clone the repo

Add your own OpenWeatherMap API key and Twilio credentials

Ensure flood_model.pkl, flood_data.csv, and user_data.csv exist

Run python app.py and the app will open in your brows
