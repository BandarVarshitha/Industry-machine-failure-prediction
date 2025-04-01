import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_db_connection():
    """Create and return a database connection."""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Sujatha#12345",
            database="machine_data"
        )
        return conn
    except Error as e:
        logging.error(f"Error connecting to MySQL: {e}")
        return None

def execute_query(conn, query, data=None, many=False):
    """Execute a SQL query with optional data."""
    cursor = None
    try:
        cursor = conn.cursor()
        if many and data:
            cursor.executemany(query, data)
        elif data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        conn.commit()
        return True
    except Error as e:
        logging.error(f"Error executing query: {e}")
        return False
    finally:
        if cursor:
            cursor.close()

def insert_machines_data(conn, df):
    """Insert data into Machines table."""
    query = """
    INSERT INTO Machines (
        Machine_ID, Machine_Type, Installation_Date, Age, Workload, Production_Rate, 
        Operational_Hours, Last_Maintenance_Date, Maintenance_Type, 
        Maintenance_Cost, Maintenance_Duration
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        Machine_Type=VALUES(Machine_Type),
        Installation_Date=VALUES(Installation_Date),
        Age=VALUES(Age),
        Workload=VALUES(Workload),
        Production_Rate=VALUES(Production_Rate),
        Operational_Hours=VALUES(Operational_Hours),
        Last_Maintenance_Date=VALUES(Last_Maintenance_Date),
        Maintenance_Type=VALUES(Maintenance_Type),
        Maintenance_Cost=VALUES(Maintenance_Cost),
        Maintenance_Duration=VALUES(Maintenance_Duration)
    """
    
    # Prepare data
    data = []
    for _, row in df.iterrows():
        data.append((
            row['Machine_ID'],
            row['Machine_Type'],
            row['Installation_Date'],
            row['Age'],
            row['Workload'],
            row['Production_Rate'],
            row['Operational_Hours'],
            row['Last_Maintenance_Date'] if pd.notna(row['Last_Maintenance_Date']) else None,
            row['Maintenance_Type'] if pd.notna(row['Maintenance_Type']) else None,
            row['Maintenance_Cost ($)'] if pd.notna(row['Maintenance_Cost ($)']) else None,
            row['Maintenance_Duration (hrs)'] if pd.notna(row['Maintenance_Duration (hrs)']) else None
        ))
    
    return execute_query(conn, query, data, many=True)

def insert_sensor_data(conn, df):
    """Insert data into SensorData table."""
    query = """
    INSERT INTO SensorData (
        Machine_ID, Timestamp, Temperature, Vibration, Pressure, Humidity, 
        Voltage, Current, Power_Consumption, Ambient_Temperature, 
        Ambient_Humidity, Anomaly_Score, Anomaly_Flag
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    # Prepare data
    data = []
    for _, row in df.iterrows():
        data.append((
            row['Machine_ID'],
            row['Timestamp'],
            row['Temperature (°C)'],
            row['Vibration (mm/s)'],
            row['Pressure (psi)'],
            row['Humidity (%)'],
            row['Voltage (V)'],
            row['Current (A)'],
            row['Power_Consumption (kW)'],
            row['Ambient_Temperature (°C)'],
            row['Ambient_Humidity (%)'],
            row['Anomaly_Score'],
            row['Anomaly_Flag']
        ))
    
    return execute_query(conn, query, data, many=True)

def insert_failure_records(conn, df):
    """Insert data into FailureRecords table."""
    query = """
    INSERT INTO FailureRecords (
        Machine_ID, Failure_Status, Failure_Type, Downtime, 
        Predicted_Failure_Probability, Predicted_Failure_Time
    ) VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    # Prepare data - only rows with failures
    data = []
    for _, row in df[df['Failure_Status'] == 1].iterrows():
        data.append((
            row['Machine_ID'],
            row['Failure_Status'],
            row['Failure_Type'] if pd.notna(row['Failure_Type']) else None,
            row['Downtime (hrs)'] if pd.notna(row['Downtime (hrs)']) else 0,
            row['Predicted_Failure_Probability'] if pd.notna(row['Predicted_Failure_Probability']) else None,
            row['Predicted_Failure_Time'] if pd.notna(row['Predicted_Failure_Time']) else None
        ))
    
    return execute_query(conn, query, data, many=True)

def insert_maintenance_schedule(conn, df):
    """Insert data into MaintenanceSchedule table."""
    query = """
    INSERT INTO MaintenanceSchedule (
        Machine_ID, Scheduled_Date, Maintenance_Type, Estimated_Cost, Estimated_Duration
    ) VALUES (%s, %s, %s, %s, %s)
    """
    
    # Prepare data - only rows with maintenance records
    data = []
    for _, row in df[pd.notna(df['Last_Maintenance_Date'])].iterrows():
        data.append((
            row['Machine_ID'],
            row['Last_Maintenance_Date'],
            row['Maintenance_Type'] if pd.notna(row['Maintenance_Type']) else 'Unknown',
            row['Maintenance_Cost ($)'] if pd.notna(row['Maintenance_Cost ($)']) else 0,
            row['Maintenance_Duration (hrs)'] if pd.notna(row['Maintenance_Duration (hrs)']) else 0
        ))
    
    return execute_query(conn, query, data, many=True)

def insert_anomaly_detection(conn, df):
    """Insert data into AnomalyDetection table."""
    query = """
    INSERT INTO AnomalyDetection (
        Machine_ID, Timestamp, Anomaly_Score, Anomaly_Flag
    ) VALUES (%s, %s, %s, %s)
    """
    
    # Prepare data
    data = []
    for _, row in df.iterrows():
        data.append((
            row['Machine_ID'],
            row['Timestamp'],
            row['Anomaly_Score'],
            row['Anomaly_Flag']
        ))
    
    return execute_query(conn, query, data, many=True)

def insert_machine_health_indicators(conn, df):
    """Insert data into MachineHealthIndicators table."""
    query = """
    INSERT INTO MachineHealthIndicators (
        Machine_ID, Timestamp, Health_Score, Failure_Probability
    ) VALUES (%s, %s, %s, %s)
    """
    
    # Calculate health score (1 - anomaly score)
    df['Health_Score'] = 1 - df['Anomaly_Score']
    
    # Prepare data
    data = []
    for _, row in df.iterrows():
        data.append((
            row['Machine_ID'],
            row['Timestamp'],
            row['Health_Score'],
            row['Predicted_Failure_Probability'] if pd.notna(row['Predicted_Failure_Probability']) else 0
        ))
    
    return execute_query(conn, query, data, many=True)

def insert_failure_trends(conn, df):
    """Insert aggregated failure trends data."""
    query = """
    INSERT INTO FailureTrends (
        Machine_Type, Timestamp, Failure_Rate
    ) VALUES (%s, %s, %s)
    """
    
    # Calculate failure rate by machine type and timestamp
    df['Date'] = pd.to_datetime(df['Timestamp']).dt.date
    failure_rates = df.groupby(['Machine_Type', 'Date'])['Failure_Status'].mean().reset_index()
    
    # Prepare data
    data = []
    for _, row in failure_rates.iterrows():
        data.append((
            row['Machine_Type'],
            row['Date'],
            row['Failure_Status']
        ))
    
    return execute_query(conn, query, data, many=True)

def main():
    # Load the dataset
    try:
        df = pd.read_csv('machine_failure_data.csv')
        logging.info("Dataset loaded successfully")
    except Exception as e:
        logging.error(f"Error loading dataset: {e}")
        return

    # Create database connection
    conn = create_db_connection()
    if not conn:
        return

    try:
        # Insert data into each table
        logging.info("Inserting data into Machines table...")
        if insert_machines_data(conn, df):
            logging.info("Machines data inserted successfully")
        
        logging.info("Inserting data into SensorData table...")
        if insert_sensor_data(conn, df):
            logging.info("SensorData inserted successfully")
        
        logging.info("Inserting data into FailureRecords table...")
        if insert_failure_records(conn, df):
            logging.info("FailureRecords inserted successfully")
        
        logging.info("Inserting data into MaintenanceSchedule table...")
        if insert_maintenance_schedule(conn, df):
            logging.info("MaintenanceSchedule inserted successfully")
        
        logging.info("Inserting data into AnomalyDetection table...")
        if insert_anomaly_detection(conn, df):
            logging.info("AnomalyDetection inserted successfully")
        
        logging.info("Inserting data into MachineHealthIndicators table...")
        if insert_machine_health_indicators(conn, df):
            logging.info("MachineHealthIndicators inserted successfully")
        
        logging.info("Inserting data into FailureTrends table...")
        if insert_failure_trends(conn, df):
            logging.info("FailureTrends inserted successfully")
            
    except Exception as e:
        logging.error(f"Error during data insertion: {e}")
    finally:
        if conn:
            conn.close()
            logging.info("Database connection closed")

if __name__ == "__main__":
    main()