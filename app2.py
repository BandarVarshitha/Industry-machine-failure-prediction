import mysql.connector
from flask import Flask, request, jsonify, render_template
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Load the trained model
try:
    model = joblib.load('equipment_failure_model.pkl')
    logging.info("Model loaded successfully")
except Exception as e:
    logging.error(f"Error loading model: {e}")
    raise

# Database connection function (aligned with machine_training.py)
def create_db_connection():
    """Create and return a database connection with dictionary cursor."""
    try:
        logging.info("Attempting to connect to the database...")
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Sujatha#12345",
            database="machine_data"
        )
        logging.info("Database connection established successfully.")
        return conn
    except mysql.connector.Error as e:  # Corrected the typo here
        logging.error(f"Error connecting to MySQL: {e}")
        return None

# Home page
@app.route('/')
@app.route('/dashboard')
def dashboard():
    """Render the Dashboard page."""
    return render_template('dashboard.html')


@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/prediction')
def prediction():
    return render_template('Prediction.html')

@app.route('/maintenance')
def maintenance():
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed")
        return render_template('Maintenance.html', 
                               maintenance_schedule=[],
                               operational_count=0,
                               preventive_count=0,
                               due_count=0,
                               critical_count=0,
                               urgent_alerts=[],
                               warnings=[])

    try:
        cursor = conn.cursor(dictionary=True)

        # Fetch maintenance schedule
        query_schedule = """
        SELECT Machine_ID, Maintenance_Type, DATE_FORMAT(Scheduled_Date, '%Y-%m-%d') AS Scheduled_Date, 
               Estimated_Cost, Estimated_Duration
        FROM MaintenanceSchedule
        WHERE Scheduled_Date >= CURDATE()
        ORDER BY Scheduled_Date ASC
        """
        cursor.execute(query_schedule)
        maintenance_schedule = cursor.fetchall()

        # Fetch operational count
        query_operational = """
        SELECT COUNT(*) AS operational_count
        FROM Machines
        WHERE Machine_ID NOT IN (
            SELECT Machine_ID FROM FailureRecords WHERE Failure_Status = 1
        )
        """
        cursor.execute(query_operational)
        operational_count = cursor.fetchone()['operational_count'] or 0

        # Fetch preventive maintenance count
        query_preventive = """
        SELECT COUNT(*) AS preventive_count
        FROM MaintenanceSchedule
        WHERE Maintenance_Type = 'Preventive'
          AND Scheduled_Date >= CURDATE()
        """
        cursor.execute(query_preventive)
        preventive_count = cursor.fetchone()['preventive_count'] or 0

        # Fetch due maintenance count
        query_due = """
        SELECT COUNT(*) AS due_count
        FROM MaintenanceSchedule
        WHERE Scheduled_Date < CURDATE()
        """
        cursor.execute(query_due)
        due_count = cursor.fetchone()['due_count'] or 0

        # Fetch critical maintenance count
        query_critical = """
        SELECT COUNT(*) AS critical_count
        FROM FailureRecords
        WHERE Failure_Status = 1
        """
        cursor.execute(query_critical)
        critical_count = cursor.fetchone()['critical_count'] or 0

        # Fetch urgent alerts
        query_urgent_alerts = """
        SELECT Machine_ID, Failure_Type
        FROM FailureRecords
        WHERE Failure_Status = 1
        ORDER BY Predicted_Failure_Time DESC
        LIMIT 5
        """
        cursor.execute(query_urgent_alerts)
        urgent_alerts = cursor.fetchall()

        # Fetch warnings
        query_warnings = """
        SELECT Machine_ID, Failure_Type
        FROM FailureRecords
        WHERE Failure_Status = 0 AND Predicted_Failure_Probability > 0.7
        ORDER BY Predicted_Failure_Probability DESC
        LIMIT 5
        """
        cursor.execute(query_warnings)
        warnings = cursor.fetchall()

        cursor.close()

        return render_template('Maintenance.html', 
                               maintenance_schedule=maintenance_schedule or [],
                               operational_count=operational_count,
                               preventive_count=preventive_count,
                               due_count=due_count,
                               critical_count=critical_count,
                               urgent_alerts=urgent_alerts or [],
                               warnings=warnings or [])
    except Exception as e:
        logging.error(f"Error fetching maintenance data: {e}")
        return render_template('Maintenance.html', 
                               maintenance_schedule=[],
                               operational_count=0,
                               preventive_count=0,
                               due_count=0,
                               critical_count=0,
                               urgent_alerts=[],
                               warnings=[])
    finally:
        if conn:
            conn.close()

@app.route('/trends')
def trends():
    return render_template('Trends.html')

@app.route('/failure')
def failure():
    return render_template('Failure.html')

@app.route('/equipment_status_page')
def equipment_status_page():
    return render_template('Equipment_status.html')


# API Endpoints (updated to match machine_training.py data structure)
@app.route('/api/machine-data', methods=['GET'])
def get_machine_data():
    """Get machine data from the Machines table"""
    conn = create_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        query = """
        SELECT Machine_ID, Machine_Type, Age, Workload, Production_Rate, 
               Operational_Hours, Last_Maintenance_Date
        FROM Machines
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching machine data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/sensor-data', methods=['GET'])
def get_sensor_data():
    """Get recent sensor data"""
    conn = create_db_connection()

    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Machine_ID, Timestamp, Temperature, Vibration, Pressure, 
               Humidity, Power_Consumption, Anomaly_Score, Anomaly_Flag
        FROM SensorData
        ORDER BY Timestamp DESC
        LIMIT 100
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching sensor data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/predict', methods=['POST'])
def predict():
    """Make failure predictions based on input data."""
    try:
        # Check if request is JSON
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        # Parse input data from the request
        data = request.get_json()
        logging.info(f"Received data for prediction: {data}")

        # Validate input fields
        required_fields = [
            'age', 'temperature', 'vibration', 'pressure', 'humidity', 
            'voltage', 'current', 'power_consumption', 'downtime', 
            'production_rate', 'operational_hours', 'ambient_temperature', 
            'ambient_humidity', 'anomaly_score', 'anomaly_flag', 
            'predicted_failure_probability', 'machine_type', 'workload',
            'maintenance_type'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            error_message = f"Missing required fields: {', '.join(missing_fields)}"
            logging.error(f"Validation failed. Missing fields: {missing_fields}")
            return jsonify({"error": error_message}), 400

        # Replace None values with default values and validate non-negative inputs
        for field in required_fields:
            if data.get(field) is None:
                if field in ['anomaly_flag']:  # Integer fields
                    data[field] = 0
                elif field in ['machine_type', 'workload', 'maintenance_type']:  # Categorical fields
                    data[field] = 'Unknown'
                else:  # Numerical fields
                    data[field] = 0.0
            elif isinstance(data[field], (int, float)) and data[field] < 0:
                error_message = f"Invalid value for {field}: {data[field]}. Must be non-negative."
                logging.error(error_message)
                return jsonify({"error": error_message}), 400

        # Log parsed data for debugging
        logging.info(f"Parsed data: {data}")

        # Create DataFrame with expected features
        try:
            input_data = pd.DataFrame([{
                'Age': float(data['age']),
                'Temperature (°C)': float(data['temperature']),
                'Vibration (mm/s)': float(data['vibration']),
                'Pressure (psi)': float(data['pressure']),
                'Humidity (%)': float(data['humidity']),
                'Voltage (V)': float(data['voltage']),
                'Current (A)': float(data['current']),
                'Power_Consumption (kW)': float(data['power_consumption']),
                'Downtime (hrs)': float(data['downtime']),
                'Production_Rate': float(data['production_rate']),
                'Operational_Hours': float(data['operational_hours']),
                'Ambient_Temperature (°C)': float(data['ambient_temperature']),
                'Ambient_Humidity (%)': float(data['ambient_humidity']),
                'Anomaly_Score': float(data['anomaly_score']),
                'Anomaly_Flag': int(data['anomaly_flag']),
                'Predicted_Failure_Probability': float(data['predicted_failure_probability']),
                'Machine_Type_' + data['machine_type']: 1,
                'Workload_' + data['workload']: 1,
                'Maintenance_Type_' + data['maintenance_type']: 1
            }])

            # Ensure all expected columns are present (add missing with 0)
            expected_columns = [
                'Age', 'Temperature (°C)', 'Vibration (mm/s)', 'Pressure (psi)', 
                'Humidity (%)', 'Voltage (V)', 'Current (A)', 'Power_Consumption (kW)',
                'Downtime (hrs)', 'Production_Rate', 'Operational_Hours',
                'Ambient_Temperature (°C)', 'Ambient_Humidity (%)', 'Anomaly_Score',
                'Anomaly_Flag', 'Predicted_Failure_Probability',
                'Machine_Type_Conveyor Belt', 'Machine_Type_Hydraulic Press',
                'Workload_Low', 'Workload_Medium', 'Workload_High',
                'Maintenance_Type_Preventive', 'Maintenance_Type_Corrective'
            ]
            
            for col in expected_columns:
                if col not in input_data.columns:
                    input_data[col] = 0

            # Reorder columns to match training data
            input_data = input_data[expected_columns]

        except Exception as e:
            logging.error(f"Error creating DataFrame: {str(e)}")
            return jsonify({"error": f"Invalid input data: {str(e)}"}), 400

        # Log the aligned DataFrame
        logging.info(f"Aligned Input DataFrame: {input_data.to_dict()}")

        # Make prediction using the loaded model
        try:
            # Replace this with your actual model prediction code
            # prediction = model.predict(input_data)[0]
            # probability = model.predict_proba(input_data)[0][1] * 100
            
            # For demo purposes - replace with actual model calls
            prediction = 1 if float(data['anomaly_score']) > 0.5 else 0
            probability = float(data['predicted_failure_probability'])
            
        except Exception as e:
            logging.error(f"Error during model prediction: {str(e)}")
            return jsonify({"error": f"Model prediction failed: {str(e)}"}), 500

        # Determine reasons for failure based on input features
        reasons = []
        if data.get("temperature") > 80:
            reasons.append("High operating temperature.")
        if data.get("vibration") > 2.0:
            reasons.append("Excessive vibration levels.")
        if data.get("pressure") > 150:
            reasons.append("High system pressure.")
        if data.get("humidity") > 70:
            reasons.append("High humidity levels.")
        if data.get("downtime") > 5:
            reasons.append("Extended recent downtime.")
        if not reasons:
            reasons.append("No specific reasons identified.")

        # Return prediction result
        return jsonify({
            "prediction": int(prediction),
            "probability": round(probability, 2),  # Already in percentage
            "reasons": " ".join(reasons)
        })

    except Exception as e:
        logging.error(f"Unexpected error in /predict: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500



@app.route('/api/failure-records', methods=['GET'])
def get_failure_records():
    """Get failure records from database"""
    conn = create_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        query = """
        SELECT fr.Machine_ID, m.Machine_Type, fr.Failure_Type, fr.Downtime,
               fr.Predicted_Failure_Probability, fr.Predicted_Failure_Time
        FROM FailureRecords fr
        JOIN Machines m ON fr.Machine_ID = m.Machine_ID
        ORDER BY fr.Predicted_Failure_Time DESC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching failure records: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/maintenance-schedule', methods=['GET'])
def get_maintenance_schedule():
    """Get maintenance schedule from database."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/maintenance-schedule")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT ms.Machine_ID, m.Machine_Type, ms.Scheduled_Date, 
               ms.Maintenance_Type, ms.Estimated_Cost, ms.Estimated_Duration
        FROM MaintenanceSchedule ms
        JOIN Machines m ON ms.Machine_ID = m.Machine_ID
        WHERE ms.Scheduled_Date >= CURDATE()
        ORDER BY ms.Scheduled_Date ASC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/maintenance-schedule")
            return jsonify([])

        logging.info(f"Data fetched for /api/maintenance-schedule: {result}")
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching maintenance schedule: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/health-indicators', methods=['GET'])
def get_health_indicators():
    """Get machine health indicators"""
    conn = create_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        query = """
        SELECT mhi.Machine_ID, m.Machine_Type, mhi.Health_Score, 
               mhi.Failure_Probability, mhi.Timestamp
        FROM MachineHealthIndicators mhi
        JOIN Machines m ON mhi.Machine_ID = m.Machine_ID
        ORDER BY mhi.Timestamp DESC
        LIMIT 50
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching health indicators: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/failure-trends', methods=['GET'])
def get_failure_trends():
    """Get aggregated failure trends grouped by month."""
    conn = create_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT DATE_FORMAT(Predicted_Failure_Time, '%Y-%m') as Month, 
               AVG(Failure_Status) * 100 AS Failure_Rate
        FROM FailureRecords
        WHERE Predicted_Failure_Time IS NOT NULL
        GROUP BY DATE_FORMAT(Predicted_Failure_Time, '%Y-%m')
        ORDER BY Month ASC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            return jsonify([])

        # Ensure the response is in the correct format
        formatted_result = [{"Month": row["Month"], "Failure_Rate": row["Failure_Rate"]} for row in result]
        return jsonify(formatted_result)
    except Exception as e:
        logging.error(f"Error fetching failure trends: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/failure-rate-by-machine-type', methods=['GET'])
def get_failure_rate_by_machine_type():
    """Fetch failure rates by machine type."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/failure-rate-by-machine-type")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT m.Machine_Type, 
               ROUND(AVG(fr.Failure_Status) * 100, 2) AS failure_rate
        FROM FailureRecords fr
        JOIN Machines m ON fr.Machine_ID = m.Machine_ID
        GROUP BY m.Machine_Type
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/failure-rate-by-machine-type")
            return jsonify({"machine_types": [], "failure_rates": []})

        logging.info(f"Data fetched for /api/failure-rate-by-machine-type: {result}")
        machine_types = [row['Machine_Type'] for row in result]
        failure_rates = [row['failure_rate'] for row in result]

        return jsonify({"machine_types": machine_types, "failure_rates": failure_rates})
    except Exception as e:
        logging.error(f"Error fetching failure rates by machine type: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/maintenance-effectiveness', methods=['GET'])
def get_maintenance_effectiveness():
    """Fetch maintenance effectiveness metrics."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/maintenance-effectiveness")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT 'Preventive' AS metric, COUNT(*) AS value
        FROM MaintenanceSchedule
        WHERE Maintenance_Type = 'Preventive'
        UNION ALL
        SELECT 'Corrective', COUNT(*)
        FROM MaintenanceSchedule
        WHERE Maintenance_Type = 'Corrective'
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/maintenance-effectiveness")
            return jsonify({"metrics": [], "values": []})

        logging.info(f"Data fetched for /api/maintenance-effectiveness: {result}")
        metrics = [row['metric'] for row in result]
        values = [row['value'] for row in result]

        return jsonify({"metrics": metrics, "values": values})
    except Exception as e:
        logging.error(f"Error fetching maintenance effectiveness metrics: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/maintenance-effectiveness-mtbf', methods=['GET'])
def get_maintenance_effectiveness_mtbf():
    """Fetch MTBF improvement data for maintenance effectiveness."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/maintenance-effectiveness-mtbf")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT DATE_FORMAT(Scheduled_Date, '%Y-%m') AS timestamp,
               AVG(MTBF_Before) AS mtbf_before,
               AVG(MTBF_After) AS mtbf_after
        FROM MaintenanceEffectiveness
        GROUP BY DATE_FORMAT(Scheduled_Date, '%Y-%m')
        ORDER BY timestamp ASC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/maintenance-effectiveness-mtbf")
            return jsonify({"timestamps": [], "mtbf_values": []})

        timestamps = [row['timestamp'] for row in result]
        mtbf_values = [row['mtbf_after'] for row in result]

        return jsonify({"timestamps": timestamps, "mtbf_values": mtbf_values})
    except Exception as e:
        logging.error(f"Error fetching MTBF improvement data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/failure-probability-vs-maintenance', methods=['GET'])
def get_failure_probability_vs_maintenance():
    """Fetch failure probability vs. time since last maintenance."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/failure-probability-vs-maintenance")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT DATEDIFF(CURDATE(), m.Last_Maintenance_Date) AS time_since_maintenance,
               ROUND(AVG(fr.Predicted_Failure_Probability) * 100, 2) AS failure_probability
        FROM Machines m
        JOIN FailureRecords fr ON m.Machine_ID = fr.Machine_ID
        WHERE m.Last_Maintenance_Date IS NOT NULL
        GROUP BY time_since_maintenance
        ORDER BY time_since_maintenance
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            return jsonify({"time_since_maintenance": [], "failure_probabilities": []})

        time_since_maintenance = [row['time_since_maintenance'] for row in result]
        failure_probabilities = [row['failure_probability'] for row in result]

        return jsonify({"time_since_maintenance": time_since_maintenance, "failure_probabilities": failure_probabilities})
    except Exception as e:
        logging.error(f"Error fetching failure probability vs. maintenance data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/historical-patterns', methods=['GET'])
def get_historical_patterns():
    """Fetch historical failure patterns grouped by daily intervals."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/historical-patterns")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT DATE_FORMAT(Predicted_Failure_Time, '%Y-%m-%d') AS day,
               COUNT(*) AS failure_count
        FROM FailureRecords
        WHERE Predicted_Failure_Time IS NOT NULL
        GROUP BY DATE_FORMAT(Predicted_Failure_Time, '%Y-%m-%d')
        ORDER BY day ASC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/historical-patterns")
            return jsonify({"timestamps": [], "failure_counts": []})

        logging.info(f"Data fetched for /api/historical-patterns: {result}")
        timestamps = [row['day'] for row in result]
        failure_counts = [row['failure_count'] for row in result]

        return jsonify({"timestamps": timestamps, "failure_counts": failure_counts})
    except Exception as e:
        logging.error(f"Error fetching historical patterns: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/failure-probability', methods=['GET'])
def get_failure_probability():
    """Fetch failure probability for the gauge chart."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/failure-probability")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT AVG(Predicted_Failure_Probability) AS probability
        FROM FailureRecords
        WHERE Failure_Status = 1
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()

        probability = result['probability'] * 100 if result and result['probability'] else 0
        return jsonify({"probability": probability})
    except Exception as e:
        logging.error(f"Error fetching failure probability: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/at-risk-machines', methods=['GET'])
def get_at_risk_machines():
    """Fetch the top 5 at-risk machines."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/at-risk-machines")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Machine_ID, Failure_Type, Predicted_Failure_Time
        FROM FailureRecords
        WHERE Failure_Status = 1
        ORDER BY Predicted_Failure_Probability DESC
        LIMIT 5
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching at-risk machines: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/failure-type-distribution', methods=['GET'])
def get_failure_type_distribution():
    """Fetch failure type distribution for the pie chart."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/failure-type-distribution")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Failure_Type AS label, COUNT(*) AS value
        FROM FailureRecords
        WHERE Failure_Status = 1
        GROUP BY Failure_Type
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        labels = [row['label'] for row in result]
        values = [row['value'] for row in result]

        return jsonify({"labels": labels, "values": values})
    except Exception as e:
        logging.error(f"Error fetching failure type distribution: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/sensor-trend-correlations', methods=['GET'])
def get_sensor_trend_correlations():
    """Fetch sensor trend correlations before failures."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/sensor-trend-correlations")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT DATE_FORMAT(s.Timestamp, '%Y-%m-%d %H:00:00') AS HourlyInterval, 
               AVG(s.Temperature) AS AvgTemperature, 
               AVG(s.Vibration) AS AvgVibration, 
               AVG(s.Pressure) AS AvgPressure, 
               AVG(s.Humidity) AS AvgHumidity, 
               AVG(s.Power_Consumption) AS AvgPowerConsumption
        FROM SensorData s
        WHERE s.Machine_ID IN (
            SELECT DISTINCT fr.Machine_ID
            FROM FailureRecords fr
            WHERE fr.Failure_Status = 1
        )
        GROUP BY DATE_FORMAT(s.Timestamp, '%Y-%m-%d %H:00:00')
        ORDER BY HourlyInterval ASC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/sensor-trend-correlations")
            return jsonify({"sensors": []})

        # Prepare data for the graph
        timestamps = [row['HourlyInterval'] for row in result]
        sensors = {
            "Temperature": [row['AvgTemperature'] for row in result],
            "Vibration": [row['AvgVibration'] for row in result],
            "Pressure": [row['AvgPressure'] for row in result],
            "Humidity": [row['AvgHumidity'] for row in result],
            "Power_Consumption": [row['AvgPowerConsumption'] for row in result]
        }

        # Format data for the frontend
        sensor_data = [{"name": sensor, "timestamps": timestamps, "values": values} for sensor, values in sensors.items()]

        return jsonify({"sensors": sensor_data})
    except Exception as e:
        logging.error(f"Error fetching sensor trend correlations: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/machine-health-overview', methods=['GET'])
def get_machine_health_overview():
    """Fetch real-time machine health overview."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/machine-health-overview")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT 
            COUNT(*) AS total_machines,
            SUM(CASE WHEN fr.Failure_Status = 0 AND fr.Predicted_Failure_Probability > 0.7 THEN 1 ELSE 0 END) AS warning_machines,
            SUM(CASE WHEN fr.Failure_Status = 1 THEN 1 ELSE 0 END) AS critical_machines,
            SUM(CASE WHEN fr.Failure_Status = 0 AND (fr.Predicted_Failure_Probability <= 0.7 OR fr.Predicted_Failure_Probability IS NULL) THEN 1 ELSE 0 END) AS normal_machines
        FROM Machines m
        LEFT JOIN FailureRecords fr ON m.Machine_ID = fr.Machine_ID
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/machine-health-overview")
            return jsonify({"total_machines": 0, "warning_machines": 0, "critical_machines": 0, "normal_machines": 0})

        logging.info(f"Data fetched for /api/machine-health-overview: {result}")
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching machine health overview: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/machine-status', methods=['GET'])
def get_machine_status():
    """Fetch machine status for the table."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/machine-status")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT 
            m.Machine_ID,
            m.Machine_Type AS Type,
            CASE 
                WHEN fr.Failure_Status = 1 THEN 'Critical'
                WHEN fr.Failure_Status = 0 AND fr.Predicted_Failure_Probability > 0.7 THEN 'Warning'
                ELSE 'Normal'
            END AS Current_Status,
            m.Last_Maintenance_Date AS Last_Maintenance,
            ROUND(fr.Predicted_Failure_Probability * 100, 2) AS Predicted_Failure_Probability,
            DATE_ADD(m.Last_Maintenance_Date, INTERVAL 30 DAY) AS Next_Recommended_Maintenance
        FROM Machines m
        LEFT JOIN FailureRecords fr ON m.Machine_ID = fr.Machine_ID
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/machine-status")
            return jsonify([])

        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching machine status: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/temperature-distribution', methods=['GET'])
def get_temperature_distribution():
    """Fetch temperature distribution for the gauge chart."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/temperature-distribution")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT AVG(Temperature) AS average_temperature,
               MIN(Temperature) AS min_temperature,
               MAX(Temperature) AS max_temperature
        FROM SensorData
        WHERE Timestamp >= NOW() - INTERVAL 1 DAY
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()

        if not result or result['average_temperature'] is None:
            logging.warning("No data found for /api/temperature-distribution")
            return jsonify({"average_temperature": 0, "min_temperature": 0, "max_temperature": 100})

        logging.info(f"Data fetched for /api/temperature-distribution: {result}")
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching temperature distribution: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/sensor-contribution', methods=['GET'])
def get_sensor_contribution():
    """Fetch sensor contribution to failure prediction."""
    conn = create_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Sensor_Name AS x, ROUND(AVG(Anomaly_Score) * 100, 2) AS y
        FROM SensorData
        GROUP BY Sensor_Name
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return jsonify({"x": [row['x'] for row in result], "y": [row['y'] for row in result]})
    except Exception as e:
        logging.error(f"Error fetching sensor contribution: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/forecasting-failure', methods=['GET'])
def get_forecasting_failure():
    """Fetch time-series data for forecasting failures."""
    conn = create_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Timestamp AS x, Predicted_Failure_Probability AS y
        FROM FailureRecords
        WHERE Predicted_Failure_Probability IS NOT NULL
        ORDER BY Timestamp
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return jsonify({"x": [row['x'] for row in result], "y": [row['y'] for row in result]})
    except Exception as e:
        logging.error(f"Error fetching forecasting failure data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/optimal-maintenance-time', methods=['GET'])
def get_optimal_maintenance_time():
    """Fetch data for optimal preventive maintenance intervals."""
    conn = create_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT DATEDIFF(CURDATE(), Last_Maintenance_Date) AS x, 
               ROUND(AVG(Predicted_Failure_Probability) * 100, 2) AS y
        FROM Machines
        JOIN FailureRecords ON Machines.Machine_ID = FailureRecords.Machine_ID
        WHERE Last_Maintenance_Date IS NOT NULL
        GROUP BY x
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return jsonify({"x": [row['x'] for row in result], "y": [row['y'] for row in result]})
    except Exception as e:
        logging.error(f"Error fetching preventive maintenance data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/temperature-impact', methods=['GET'])
def get_temperature_impact():
    """Fetch data for temperature impact on machine performance."""
    conn = create_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Temperature AS x, ROUND(AVG(Anomaly_Score) * 100, 2) AS y
        FROM SensorData
        GROUP BY Temperature
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return jsonify({"x": [row['x'] for row in result], "y": [row['y'] for row in result]})
    except Exception as e:
        logging.error(f"Error fetching temperature impact data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/industry-failure-rates', methods=['GET'])
def get_industry_failure_rates():
    """Fetch failure rates by industry."""
    conn = create_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Industry AS x, ROUND(AVG(Predicted_Failure_Probability) * 100, 2) AS y
        FROM Machines
        JOIN FailureRecords ON Machines.Machine_ID = FailureRecords.Machine_ID
        GROUP BY Industry
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return jsonify({"x": [row['x'] for row in result], "y": [row['y'] for row in result]})
    except Exception as e:
        logging.error(f"Error fetching industry failure rates: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/workload-failure-probability', methods=['GET'])
def get_workload_failure_probability():
    """Fetch workload levels vs failure probabilities."""
    conn = create_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Workload AS x, ROUND(AVG(Predicted_Failure_Probability) * 100, 2) AS y
        FROM Machines
        JOIN FailureRecords ON Machines.Machine_ID = FailureRecords.Machine_ID
        GROUP BY Workload
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return jsonify({"x": [row['x'] for row in result], "y": [row['y'] for row in result]})
    except Exception as e:
        logging.error(f"Error fetching workload failure probability: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/deep-learning-failure', methods=['GET'])
def get_deep_learning_failure():
    """Fetch deep learning failure detection data."""
    conn = create_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Timestamp AS x, Predicted_Failure_Probability AS y
        FROM FailureRecords
        WHERE Predicted_Failure_Probability IS NOT NULL
        ORDER BY Timestamp
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return jsonify({"x": [row['x'] for row in result], "y": [row['y'] for row in result]})
    except Exception as e:
        logging.error(f"Error fetching deep learning failure data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/upcoming-maintenance', methods=['GET'])
def get_upcoming_maintenance():
    """Fetch upcoming maintenance schedule."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/upcoming-maintenance")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Machine_ID, DATE_FORMAT(Scheduled_Date, '%Y-%m-%d') AS Scheduled_Date, 
               Maintenance_Type, Estimated_Cost, Estimated_Duration
        FROM MaintenanceSchedule
        WHERE Scheduled_Date >= CURDATE()
        ORDER BY Scheduled_Date ASC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/upcoming-maintenance")
            return jsonify([])

        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching upcoming maintenance: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/maintenance-cost-distribution', methods=['GET'])
def get_maintenance_cost_distribution():
    """Fetch maintenance cost distribution."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/maintenance-cost-distribution")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Maintenance_Type AS label, SUM(Estimated_Cost) AS value
        FROM MaintenanceSchedule
        WHERE Scheduled_Date >= CURDATE()
        GROUP BY Maintenance_Type
        """
        logging.info(f"Executing query: {query}")
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        labels = [row['label'] for row in result]
        values = [row['value'] for row in result]
        return jsonify({"labels": labels, "values": values})
    except Exception as e:
        logging.error(f"Error fetching maintenance cost distribution: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/maintenance-duration-distribution', methods=['GET'])
def get_maintenance_duration_distribution():
    """Fetch maintenance duration distribution."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/maintenance-duration-distribution")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Estimated_Duration AS label, COUNT(*) AS value
        FROM MaintenanceSchedule
        WHERE Scheduled_Date >= CURDATE()
        GROUP BY Estimated_Duration
        ORDER BY Estimated_Duration
        """
        logging.info(f"Executing query: {query}")
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        labels = [row['label'] for row in result]
        values = [row['value'] for row in result]
        return jsonify({"labels": labels, "values": values})
    except Exception as e:
        logging.error(f"Error fetching maintenance duration distribution: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/maintenance-backlog', methods=['GET'])
def get_maintenance_backlog():
    """Fetch maintenance backlog prioritized by risk."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/maintenance-backlog")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT m.Machine_Type, fr.Failure_Type, 
               ROUND(fr.Predicted_Failure_Probability * 100, 2) AS Predicted_Failure_Probability,
               CASE
                   WHEN fr.Predicted_Failure_Probability > 0.85 THEN 'High'
                   WHEN fr.Predicted_Failure_Probability > 0.7 THEN 'Medium'
                   ELSE 'Low'
               END AS Risk_Level
        FROM FailureRecords fr
        JOIN Machines m ON fr.Machine_ID = m.Machine_ID
        WHERE fr.Failure_Status = 1
        ORDER BY fr.Predicted_Failure_Probability DESC
        """
        logging.info(f"Executing query: {query}")
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching maintenance backlog: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/maintenance-impact', methods=['GET'])
def get_maintenance_impact():
    """Fetch data for maintenance impact (downtime reduction) using existing tables."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/maintenance-impact")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT ms.Maintenance_Type, 
               AVG(fr.Downtime) AS avg_downtime_before, 
               AVG(ms.Estimated_Duration) AS avg_downtime_after
        FROM MaintenanceSchedule ms
        LEFT JOIN FailureRecords fr ON ms.Machine_ID = fr.Machine_ID
        WHERE fr.Downtime IS NOT NULL AND ms.Estimated_Duration IS NOT NULL
        GROUP BY ms.Maintenance_Type
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for maintenance impact")
            return jsonify({"labels": [], "before": [], "after": []})

        # Format the response to include both Preventive and Corrective data
        response = {
            "labels": [row["Maintenance_Type"] for row in result],
            "before": [row["avg_downtime_before"] for row in result],
            "after": [row["avg_downtime_after"] for row in result]
        }
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error fetching maintenance impact data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/cost-benefit-analysis', methods=['GET'])
def get_cost_benefit_analysis():
    """Fetch cost-benefit analysis data."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/cost-benefit-analysis")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT ms.Estimated_Cost AS cost,
               COALESCE(SUM(fr.Downtime), 0) AS downtime_prevented
        FROM MaintenanceSchedule ms
        LEFT JOIN FailureRecords fr ON ms.Machine_ID = fr.Machine_ID
        WHERE ms.Scheduled_Date >= CURDATE()
        GROUP BY ms.Estimated_Cost
        """
        logging.info(f"Executing query: {query}")
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/cost-benefit-analysis")
            return jsonify({"costs": [], "downtime_prevented": []})

        costs = [row['cost'] for row in result]
        downtime_prevented = [row['downtime_prevented'] for row in result]

        logging.info(f"Data fetched for /api/cost-benefit-analysis: {result}")
        return jsonify({"costs": costs, "downtime_prevented": downtime_prevented})
    except Exception as e:
        logging.error(f"Error fetching cost-benefit analysis data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/predict-schedule-dates', methods=['POST'])
def predict_schedule_dates():
    """Predict the next maintenance schedule dates based on existing data."""
    conn = create_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        # Fetch existing maintenance data
        query = """
        SELECT Machine_ID, Scheduled_Date, Maintenance_Type
        FROM MaintenanceSchedule
        ORDER BY Scheduled_Date ASC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        maintenance_data = cursor.fetchall()

        # Predict next schedule dates
        predictions = []
        for record in maintenance_data:
            machine_id = record['Machine_ID']
            last_date = record['Scheduled_Date']
            maintenance_type = record['Maintenance_Type']

            # Example logic: Add 30 days for preventive maintenance, 60 days for corrective
            if (maintenance_type == 'Preventive'):
                next_date = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
            elif (maintenance_type == 'Corrective'):
                next_date = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=60)).strftime('%Y-%m-%d')
            else:
                next_date = None

            if next_date:
                predictions.append({
                    "Machine_ID": machine_id,
                    "Next_Scheduled_Date": next_date,
                    "Maintenance_Type": maintenance_type
                })

        cursor.close()
        return jsonify(predictions)
    except Exception as e:
        logging.error(f"Error predicting schedule dates: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/upcoming-maintenance-calendar', methods=['GET'])
def get_upcoming_maintenance_calendar():
    """Fetch upcoming maintenance schedule for calendar view."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/upcoming-maintenance-calendar")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Machine_ID, DATE_FORMAT(Scheduled_Date, '%Y-%m-%d') AS Scheduled_Date, 
               Maintenance_Type, 
               COALESCE(Estimated_Cost, 0) AS Estimated_Cost, 
               COALESCE(Estimated_Duration, 0) AS Estimated_Duration
        FROM MaintenanceSchedule
        WHERE Scheduled_Date >= CURDATE()
        ORDER BY Scheduled_Date ASC
        """
        logging.info(f"Executing query: {query}")
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/upcoming-maintenance-calendar")
            return jsonify([])

        logging.info(f"Data fetched for /api/upcoming-maintenance-calendar: {result}")
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching upcoming maintenance calendar: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/maintenance-cost-tracker', methods=['GET'])
def get_maintenance_cost_tracker():
    """Fetch maintenance cost tracker data."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/maintenance-cost-tracker")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT DATE_FORMAT(Scheduled_Date, '%Y-%m') AS month,
               SUM(Estimated_Cost) AS total_cost
        FROM MaintenanceSchedule
        WHERE Scheduled_Date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        GROUP BY DATE_FORMAT(Scheduled_Date, '%Y-%m')
        ORDER BY month ASC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/maintenance-cost-tracker")
            return jsonify({"labels": [], "values": []})

        labels = [row['month'] for row in result]
        values = [row['total_cost'] for row in result]

        # Ensure x-axis intervals are consistent and sorted
        all_months = pd.date_range(start=pd.to_datetime(labels[0]), end=pd.to_datetime(labels[-1]), freq='MS').strftime('%Y-%m').tolist()
        values_dict = dict(zip(labels, values))
        adjusted_values = [values_dict.get(month, 0) for month in all_months]

        logging.info(f"Data fetched for /api/maintenance-cost-tracker: {result}")
        return jsonify({"labels": all_months, "values": adjusted_values})
    except Exception as e:
        logging.error(f"Error fetching maintenance cost tracker data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/pressure-trend', methods=['GET'])
def get_pressure_trend():
    """Fetch pressure readings trend for the most recent day available."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/pressure-trend")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        # First get the most recent date in the dataset
        max_date_query = "SELECT MAX(DATE(Timestamp)) AS max_date FROM SensorData"
        cursor = conn.cursor(dictionary=True)
        cursor.execute(max_date_query)
        max_date_result = cursor.fetchone()
        
        if not max_date_result or not max_date_result['max_date']:
            logging.warning("No data found in SensorData table")
            return jsonify({"timestamps": [], "pressure_readings": []})

        max_date = max_date_result['max_date']
        
        # Then get hourly averages for that date
        hourly_query = """
        SELECT 
            DATE_FORMAT(Timestamp, '%Y-%m-%d %H:00:00') AS Hourly_Timestamp,
            AVG(Pressure) AS Average_Pressure
        FROM SensorData
        WHERE DATE(Timestamp) = %s
        GROUP BY Hourly_Timestamp
        ORDER BY Hourly_Timestamp ASC
        """
        cursor.execute(hourly_query, (max_date,))
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning(f"No data found for the most recent date: {max_date}")
            return jsonify({"timestamps": [], "pressure_readings": []})

        timestamps = [row['Hourly_Timestamp'] for row in result]
        pressure_readings = [float(row['Average_Pressure']) for row in result]

        return jsonify({
            "timestamps": timestamps,
            "pressure_readings": pressure_readings,
            "date": str(max_date)  # Optional: send the date being displayed
        })
    except Exception as e:
        logging.error(f"Error fetching pressure trend: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/temperature-failure-probability', methods=['GET'])
def get_temperature_failure_probability():
    """Fetch temperature vs failure probability data."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/temperature-failure-probability")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Temperature, AVG(Predicted_Failure_Probability) AS Failure_Probability
        FROM SensorData sd
        JOIN FailureRecords fr ON sd.Machine_ID = fr.Machine_ID
        WHERE fr.Failure_Status = 1
        GROUP BY Temperature
        ORDER BY Temperature ASC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/temperature-failure-probability")
            return jsonify({"temperatures": [], "failure_probabilities": []})

        temperatures = [row['Temperature'] for row in result]
        failure_probabilities = [row['Failure_Probability'] for row in result]

        return jsonify({"temperatures": temperatures, "failure_probabilities": failure_probabilities})
    except Exception as e:
        logging.error(f"Error fetching temperature vs failure probability: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/workload-failure-rates', methods=['GET'])
def get_workload_failure_rates():
    """Fetch failure rates by workload level."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/workload-failure-rates")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT Workload, ROUND(AVG(Predicted_Failure_Probability) * 100, 2) AS Failure_Rate
        FROM Machines m
        JOIN FailureRecords fr ON m.Machine_ID = fr.Machine_ID
        GROUP BY Workload
        ORDER BY Workload ASC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/workload-failure-rates")
            return jsonify({"workload_levels": [], "failure_rates": []})

        workload_levels = [row['Workload'] for row in result]
        failure_rates = [row['Failure_Rate'] for row in result]

        return jsonify({"workload_levels": workload_levels, "failure_rates": failure_rates})
    except Exception as e:
        logging.error(f"Error fetching workload failure rates: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
            
@app.route('/api/vibration-heatmap', methods=['GET'])
def get_vibration_heatmap():
    """Fetch vibration levels heatmap data grouped by Machine Type."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/vibration-heatmap")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        # Get the most recent date
        max_date_query = "SELECT MAX(DATE(Timestamp)) AS max_date FROM SensorData"
        cursor = conn.cursor(dictionary=True)
        cursor.execute(max_date_query)
        max_date_result = cursor.fetchone()
        
        if not max_date_result or not max_date_result['max_date']:
            logging.warning("No data found in SensorData table")
            return jsonify({"timestamps": [], "machine_types": [], "vibration_levels": []})

        max_date = max_date_result['max_date']
        
        # Get vibration data grouped by machine type and hour
        query = """
        SELECT 
            DATE_FORMAT(Timestamp, '%Y-%m-%d %H:00:00') AS Hourly_Timestamp,
            Machine_Type,
            AVG(`Vibration (mm/s)`) AS Average_Vibration
        FROM SensorData
        WHERE DATE(Timestamp) = %s
        GROUP BY Hourly_Timestamp, Machine_Type
        ORDER BY Hourly_Timestamp ASC, Machine_Type ASC
        """
        cursor.execute(query, (max_date,))
        result = cursor.fetchall()
        cursor.close()

        if not result:
            return jsonify({
                "timestamps": [], 
                "machine_types": [], 
                "vibration_levels": [], 
                "date": str(max_date)
            })

        # Process data for heatmap
        timestamps = sorted(list({row['Hourly_Timestamp'] for row in result}))
        machine_types = sorted(list({row['Machine_Type'] for row in result}))
        
        # Create vibration matrix (timestamps x machine_types)
        vibration_levels = []
        for timestamp in timestamps:
            row = []
            for machine_type in machine_types:
                # Find matching record or use 0 if no data
                value = next(
                    (float(r['Average_Vibration']) 
                    for r in result 
                    if r['Hourly_Timestamp'] == timestamp 
                    and r['Machine_Type'] == machine_type
                ), 0)
                row.append(value)
            vibration_levels.append(row)

        return jsonify({
            "timestamps": timestamps,
            "machine_types": machine_types,
            "vibration_levels": vibration_levels,
            "date": str(max_date)
        })
    except Exception as e:
        logging.error(f"Error fetching vibration heatmap data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()                   
@app.route('/api/feature-importance', methods=['GET'])
def get_feature_importance():
    query = """
        SELECT 'Pressure' AS Feature, AVG(Pressure) AS Importance
        FROM SensorData
        UNION ALL
        SELECT 'Temperature', AVG(Temperature)
        FROM SensorData
        UNION ALL
        SELECT 'Vibration', AVG(Vibration)
        FROM SensorData
        ORDER BY Importance DESC
    """
    try:
        conn = create_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            return jsonify({"error": "No feature importance data found"}), 404

        data = {
            "features": [row['Feature'] for row in rows],
            "importance": [row['Importance'] for row in rows]
        }
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error fetching feature importance data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/time-series-forecasting', methods=['GET'])
def get_time_series_forecasting():
    query = """
        SELECT DATE_FORMAT(Timestamp, '%Y-%m-%d') AS Date, AVG(Temperature) AS ForecastedValue
        FROM SensorData
        GROUP BY DATE_FORMAT(Timestamp, '%Y-%m-%d')
        ORDER BY Date ASC
    """
    try:
        conn = create_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            return jsonify({"error": "No time-series forecasting data found"}), 404

        data = {
            "timestamps": [row['Date'] for row in rows],
            "values": [row['ForecastedValue'] for row in rows]
        }
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error fetching time-series forecasting data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/anomaly-detection', methods=['GET'])
def get_anomaly_detection():
    """Fetch anomaly detection data."""
    conn = create_db_connection()
    if not conn:
        logging.error("Database connection failed for /api/anomaly-detection")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        query = """
        SELECT DATE_FORMAT(Timestamp, '%Y-%m-%d %H:00:00') AS hour,
               AVG(Anomaly_Score) AS anomaly_score
        FROM SensorData
        WHERE Anomaly_Score IS NOT NULL
        GROUP BY DATE_FORMAT(Timestamp, '%Y-%m-%d %H:00:00')
        ORDER BY hour ASC
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if not result:
            logging.warning("No data found for /api/anomaly-detection")
            return jsonify({"timestamps": [], "values": []})

        timestamps = [row['hour'] for row in result]
        values = [row['anomaly_score'] for row in result]

        return jsonify({"timestamps": timestamps, "values": values})
    except Exception as e:
        logging.error(f"Error fetching anomaly detection data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/confusion-matrix', methods=['GET'])
def get_confusion_matrix():
    # Replace with mock data as the required table/columns are missing
    try:
        data = {
            "matrix": [[50, 10], [5, 35]],
            "labels": ["Normal", "Failure"]
        }
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error fetching confusion matrix data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/roc-curve', methods=['GET'])
def get_roc_curve():
    # Replace with mock data as the required table/columns are missing
    try:
        data = {
            "fpr": [0.0, 0.1, 0.2, 0.3, 0.4, 1.0],
            "tpr": [0.0, 0.4, 0.6, 0.8, 0.9, 1.0]
        }
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error fetching ROC curve data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """Handle requests for favicon.ico to prevent 404 errors."""
    return '', 204


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle unexpected exceptions."""
    logging.error(f"Unexpected error: {e}")
    return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True)