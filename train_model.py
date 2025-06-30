# train_model.py
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.multioutput import MultiOutputClassifier
import joblib

df = pd.read_csv("flood_data.csv")
X = df[["rainfall", "humidity", "wind_speed"]]
y = df[["flood_type", "flood_effect"]]

model = MultiOutputClassifier(DecisionTreeClassifier(random_state=0))
model.fit(X, y)

joblib.dump(model, "flood_model.pkl")
print("✅ Model saved using joblib")
