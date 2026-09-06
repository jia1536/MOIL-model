import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score

df = pd.read_csv("/home/claude/ml/data/synthetic_forecast.csv")
df = pd.get_dummies(df, columns=["mine_type"])

X = df.drop(columns=["forecast_tonnes"])
y = df["forecast_tonnes"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = GradientBoostingRegressor(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
r2 = r2_score(y_test, preds)
print(f"Forecast model — MAE: {mae:.1f} tonnes  R2: {r2:.4f}")
print("Feature importances:")
for col, imp in sorted(zip(X.columns, model.feature_importances_), key=lambda x: -x[1]):
    print(f"  {col}: {imp:.3f}")

joblib.dump({"model": model, "columns": list(X.columns), "mae": mae, "r2": r2},
            "/home/claude/ml/models/forecast_v1.pkl")
print("\nSaved to ml/models/forecast_v1.pkl")
