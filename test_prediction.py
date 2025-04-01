import joblib
import pandas as pd

# Load the trained model
model = joblib.load("xgboost_model.pkl")

# Create a dummy dataset for testing with all required feature names
dummy_data = pd.DataFrame({
    "Age": [5.9],
    "Temperature (°C)": [75.2],
    "Vibration (mm/s)": [2.8],
    "Pressure (psi)": [132.9],
    "Humidity (%)": [44.4],
    "Voltage (V)": [215.9],
    "Current (A)": [19.8],
    "Power_Consumption (kW)": [2.8],
    "Downtime (hrs)": [1.4],
    "Production_Rate": [92.0],
    "Operational_Hours": [8178.0],
    "Maintenance_Cost ($)": [996.0],
    "Maintenance_Duration (hrs)": [3.4],
    "Ambient_Temperature (°C)": [27.2],
    "Ambient_Humidity (%)": [68.7],
    "Anomaly_Score": [0.35],
    "Anomaly_Flag": [0],
    "Predicted_Failure_Probability": [0.26],
    "Machine_Type_Conveyor Belt": [0],
    "Machine_Type_Hydraulic Press": [0],
    "Workload_Low": [1],
    "Workload_Medium": [0],
    "Maintenance_Type_Preventive": [1]
})

# Make predictions
predictions = model.predict(dummy_data)
probabilities = model.predict_proba(dummy_data)

# Display the results
print(f"Prediction: {'Failure' if predictions[0] == 1 else 'No Failure'}")
print(f"Probabilities: {probabilities[0]}")
