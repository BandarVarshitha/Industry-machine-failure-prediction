# import pandas as pd
# import xgboost as xgb
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import accuracy_score, classification_report
# import joblib

# # Load the dataset
# data = pd.read_csv("machine_failure_data.csv")
# print("Columns in dataset:", data.columns.tolist())

# # Preprocess the data
# columns_to_drop = [
#     "Machine_ID", "Timestamp", "Installation_Date", "Last_Maintenance_Date", 
#     "Failure_Type", "Predicted_Failure_Time"
# ]
# columns_to_drop = [col for col in columns_to_drop if col in data.columns]
# data = data.drop(columns=columns_to_drop, axis=1)

# # Handle missing values
# data = data.fillna(0)

# # Handle negative values
# numerical_columns = data.select_dtypes(include=['float64', 'int64']).columns
# for col in numerical_columns:
#     if (data[col] < 0).any():
#         print(f"Warning: Negative values in {col}. Replacing with 0.")
#         data[col] = data[col].clip(lower=0)

# # Encode categorical variables
# data = pd.get_dummies(data, columns=['Machine_Type', 'Workload', 'Maintenance_Type'], drop_first=True)

# # Split features and target
# X = data.drop("Failure_Status", axis=1)
# y = data["Failure_Status"]

# # Save feature names
# print("Training columns:", X.columns.tolist())
# joblib.dump(X.columns.tolist(), "feature_names.pkl")

# # Split data
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# # Train model
# model = xgb.XGBClassifier(use_label_encoder=False, eval_metric="logloss")
# model.fit(X_train, y_train)

# # Evaluate
# y_pred = model.predict(X_test)
# print(f"Accuracy: {accuracy_score(y_test, y_pred)}")
# print(classification_report(y_test, y_pred))

# # Save model
# joblib.dump(model, "xgboost_model.pkl")
# print("Model saved.")

import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Load the dataset
data = pd.read_csv("machine_failure_data.csv")
print("Columns in dataset:", data.columns.tolist())

# Preprocess the data
columns_to_drop = [
    "Machine_ID", "Timestamp", "Installation_Date", "Last_Maintenance_Date", 
    "Failure_Type", "Predicted_Failure_Time"
]
columns_to_drop = [col for col in columns_to_drop if col in data.columns]
data = data.drop(columns=columns_to_drop, axis=1)

# Handle missing values
data = data.fillna(0)

# Handle negative values
numerical_columns = data.select_dtypes(include=['float64', 'int64']).columns
for col in numerical_columns:
    if (data[col] < 0).any():
        print(f"Warning: Negative values in {col}. Replacing with 0.")
        data[col] = data[col].clip(lower=0)

# Encode categorical variables
data = pd.get_dummies(data, columns=['Machine_Type', 'Workload', 'Maintenance_Type'], drop_first=True)

# Split features and target
X = data.drop("Failure_Status", axis=1)
y = data["Failure_Status"]

# Save feature names
print("Training columns:", X.columns.tolist())
joblib.dump(X.columns.tolist(), "feature_names.pkl")

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Save test set
joblib.dump(X_test, "X_test.pkl")
joblib.dump(y_test, "y_test.pkl")
print("Test set saved as X_test.pkl and y_test.pkl")

# Train model
model = xgb.XGBClassifier(use_label_encoder=False, eval_metric="logloss")
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred)}")
print(classification_report(y_test, y_pred))

# Save model
joblib.dump(model, "xgboost_model.pkl")
print("Model saved.")