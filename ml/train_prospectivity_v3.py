"""
train_prospectivity_v3.py — same RF pattern as train_prospectivity_v2.py,
trained on synthetic_prospectivity_v3.csv which includes the 3 new columns:
thickness_m, ore_grade_mn_pct, water_table_depth_m.

Run generate_prospectivity_data_v3.py first to produce the training CSV.
"""
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

df = pd.read_csv("data/synthetic_prospectivity_v3.csv")
df = df.drop(columns=["state"])
df = pd.get_dummies(df, columns=["geology_type"])

X = df.drop(columns=["prospectivity_score"])
y = df["prospectivity_score"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestRegressor(n_estimators=250, random_state=42)
model.fit(X_train, y_train)

preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
r2 = r2_score(y_test, preds)
print(f"Prospectivity v3 model — MAE: {mae:.4f}  R2: {r2:.4f}")
print("Feature importances:")
for col, imp in sorted(zip(X.columns, model.feature_importances_), key=lambda x: -x[1]):
    print(f"  {col}: {imp:.3f}")

joblib.dump({"model": model, "columns": list(X.columns), "mae": mae, "r2": r2},
            "models/prospectivity_v3.pkl")
print("\nSaved to models/prospectivity_v3.pkl")
