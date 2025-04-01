import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Load the dataset
data = pd.read_csv("machine_failure_data.csv")

# Preprocess the data
# Drop unnecessary columns
columns_to_drop = ["Machine_ID", "Timestamp", "Installation_Date", "Last_Maintenance_Date", "Failure_Type", "Predicted_Failure_Time"]
data = data.drop(columns=columns_to_drop, axis=1)

# Handle missing values
data = data.fillna(0)

# Encode categorical variables
data = pd.get_dummies(data, drop_first=True)

# Split the data into features and target
X = data.drop("Failure_Status", axis=1)
y = data["Failure_Status"]

# Split into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the XGBoost model
model = xgb.XGBClassifier(use_label_encoder=False, eval_metric="logloss")
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy}")
print(classification_report(y_test, y_pred))

# Save the trained model
joblib.dump(model, "xgboost_model.pkl")
print("Model saved as xgboost_model.pkl")
