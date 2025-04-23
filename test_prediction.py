import joblib
import pandas as pd

# Load the trained model
model = joblib.load("xgboost_model.pkl")

# Create a dummy dataset for testing with all required feature names
dummy_data = pd.DataFrame({
    "Age": [2.0],
    "Temperature (°C)": [60.0],
    "Vibration (mm/s)": [0.8],
    "Pressure (psi)": [110.0],
    "Humidity (%)": [40.0],
    "Voltage (V)": [220.0],
    "Current (A)": [10.0],
    "Power_Consumption (kW)": [1.5],
    "Downtime (hrs)": [0.5],
    "Production_Rate": [200.0],
    "Operational_Hours": [5000.0],
    "Ambient_Temperature (°C)": [25.0],
    "Ambient_Humidity (%)": [50.0],
    "Anomaly_Score": [0.05],
    "Anomaly_Flag": [0],
    "Predicted_Failure_Probability": [0.1],
    "Machine_Type_Conveyor Belt": [1],
    "Machine_Type_Hydraulic Press": [0],
    "Workload_Low": [1],
    "Workload_Medium": [0],
    "Maintenance_Type_Preventive": [1]
})

# Drop unnecessary columns to match training features (only if they exist)
columns_to_drop = ["Maintenance_Cost ($)", "Maintenance_Duration (hrs)"]
dummy_data = dummy_data.drop([col for col in columns_to_drop if col in dummy_data.columns], axis=1)

# Make predictions
predictions = model.predict(dummy_data)
probabilities = model.predict_proba(dummy_data)

# Debug: Log raw predictions and probabilities
print(f"Raw Predictions: {predictions}")
print(f"Raw Probabilities: {probabilities}")

# Define a threshold for failure classification (adjust as needed)
failure_threshold = 0.5

# Display the results
failure_probability = probabilities[0][1]  # Assuming index 1 corresponds to failure
print(f"Prediction: {'Failure' if failure_probability >= failure_threshold else 'No Failure'}")
print(f"Failure Probability: {failure_probability}")
