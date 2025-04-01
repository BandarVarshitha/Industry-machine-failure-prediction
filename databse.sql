CREATE TABLE Machines (
    Machine_ID VARCHAR(50) PRIMARY KEY,
    Machine_Type VARCHAR(50),
    Installation_Date DATE,
    Age FLOAT,
    Workload VARCHAR(50),
    Production_Rate INT,
    Operational_Hours INT,
    Last_Maintenance_Date DATE,
    Maintenance_Type VARCHAR(50),
    Maintenance_Cost FLOAT,
    Maintenance_Duration FLOAT,
    Industry VARCHAR(50)
);

CREATE TABLE SensorData (
    Sensor_ID INT AUTO_INCREMENT PRIMARY KEY,
    Machine_ID VARCHAR(50),
    Timestamp DATETIME,
    Temperature FLOAT,
    Vibration FLOAT,
    Pressure FLOAT,
    Humidity FLOAT,
    Voltage FLOAT,
    Current FLOAT,
    Power_Consumption FLOAT,
    Ambient_Temperature FLOAT,
    Ambient_Humidity FLOAT,
    Anomaly_Score FLOAT,
    Anomaly_Flag INT,
    FOREIGN KEY (Machine_ID) REFERENCES Machines(Machine_ID)
);

CREATE TABLE FailureRecords (
    Failure_ID INT AUTO_INCREMENT PRIMARY KEY,
    Machine_ID VARCHAR(50),
    Failure_Status INT,
    Failure_Type VARCHAR(50),
    Downtime FLOAT,
    Predicted_Failure_Probability FLOAT,
    Predicted_Failure_Time DATETIME,
    FOREIGN KEY (Machine_ID) REFERENCES Machines(Machine_ID)
);

CREATE TABLE MaintenanceSchedule (
    Maintenance_ID INT AUTO_INCREMENT PRIMARY KEY,
    Machine_ID VARCHAR(50),
    Scheduled_Date DATE,
    Maintenance_Type VARCHAR(50),
    Estimated_Cost FLOAT,
    Estimated_Duration FLOAT,
    FOREIGN KEY (Machine_ID) REFERENCES Machines(Machine_ID)
);

CREATE TABLE AnomalyDetection (
    Anomaly_ID INT AUTO_INCREMENT PRIMARY KEY,
    Machine_ID VARCHAR(50),
    Timestamp DATETIME,
    Anomaly_Score FLOAT,
    Anomaly_Flag INT,
    FOREIGN KEY (Machine_ID) REFERENCES Machines(Machine_ID)
);

CREATE TABLE MachineHealthIndicators (
    Health_ID INT AUTO_INCREMENT PRIMARY KEY,
    Machine_ID VARCHAR(50),
    Timestamp DATETIME,
    Health_Score FLOAT,
    Failure_Probability FLOAT,
    FOREIGN KEY (Machine_ID) REFERENCES Machines(Machine_ID)
);

CREATE TABLE FailureTrends (
    Trend_ID INT AUTO_INCREMENT PRIMARY KEY,
    Machine_Type VARCHAR(50),
    Timestamp DATETIME,
    Failure_Rate FLOAT
);

-- Insert records into MaintenanceSchedule
INSERT INTO MaintenanceSchedule (Machine_ID, Scheduled_Date, Maintenance_Type, Estimated_Cost, Estimated_Duration)
VALUES
('Machine_001', '2024-03-15', 'Preventive', 500, 2.5),
('Machine_002', '2024-03-16', 'Corrective', 800, 3.0),
('Machine_003', '2024-03-17', 'Preventive', 450, 2.0),
('Machine_006', '2024-03-18', 'Preventive', 600, 3.0),
('Machine_007', '2024-03-19', 'Corrective', 750, 2.5),
('Machine_008', '2024-03-20', 'Preventive', 500, 2.0),
('Machine_009', '2024-03-21', 'Corrective', 850, 3.5),
('Machine_010', '2024-03-22', 'Preventive', 400, 1.5);

-- Update the Scheduled_Date with non-sequential dates and months
UPDATE MaintenanceSchedule
SET Scheduled_Date = '2024-05-15'
WHERE Machine_ID = 'Machine_001';

UPDATE MaintenanceSchedule
SET Scheduled_Date = '2024-06-20'
WHERE Machine_ID = 'Machine_002';

UPDATE MaintenanceSchedule
SET Scheduled_Date = '2024-07-10'
WHERE Machine_ID = 'Machine_003';

UPDATE MaintenanceSchedule
SET Scheduled_Date = '2024-08-05'
WHERE Machine_ID = 'Machine_006';

UPDATE MaintenanceSchedule
SET Scheduled_Date = '2024-09-25'
WHERE Machine_ID = 'Machine_007';

UPDATE MaintenanceSchedule
SET Scheduled_Date = '2024-10-15'
WHERE Machine_ID = 'Machine_008';

UPDATE MaintenanceSchedule
SET Scheduled_Date = '2024-11-30'
WHERE Machine_ID = 'Machine_009';

UPDATE MaintenanceSchedule
SET Scheduled_Date = '2024-12-20'
WHERE Machine_ID = 'Machine_010';

-- Verify the updated data
SELECT * FROM MaintenanceSchedule WHERE Scheduled_Date >= CURDATE();

-- Verify that the MaintenanceSchedule table has valid data
SELECT Machine_ID, Scheduled_Date, Maintenance_Type, Estimated_Cost, Estimated_Duration
FROM MaintenanceSchedule Estimated_Cost, Estimated_Duration
WHERE Scheduled_Date >= CURDATE()
ORDER BY Scheduled_Date ASC;

-- Insert records into MaintenanceSchedule for testing
INSERT INTO MaintenanceSchedule (Machine_ID, Scheduled_Date, Maintenance_Type, Estimated_Cost, Estimated_Duration)
VALUES
('Machine_001', '2025-04-01', 'Preventive', 500, 2.5),
('Machine_002', '2025-04-02', 'Corrective', 800, 3.0),
('Machine_003', '2025-04-03', 'Preventive', 450, 2.0);

-- Insert records into FailureRecords for urgent alerts
INSERT INTO FailureRecords (Machine_ID, Failure_Status, Failure_Type, Downtime, Predicted_Failure_Probability, Predicted_Failure_Time)
VALUES
('Machine_005', 1, 'Bearing Failure', 2.1, 0.87, '2024-03-20 14:39:28'),
('Machine_009', 1, 'Electrical Failure', 1.4, 0.85, '2024-03-14 14:58:00'),
('Machine_021', 1, 'Overheating', 2.1, 0.90, '2024-03-13 04:14:22'),
('Machine_011', 1, 'Motor Failure', 3.0, 0.88, '2024-03-22 10:00:00'),
('Machine_012', 1, 'Overheating', 2.5, 0.92, '2024-03-21 15:30:00'),
('Machine_013', 1, 'Electrical Failure', 1.8, 0.85, '2024-03-20 12:45:00'),
('Machine_014', 1, 'Bearing Failure', 2.2, 0.89, '2024-03-19 09:15:00'),
('Machine_015', 1, 'Overheating', 2.7, 0.91, '2024-03-18 14:00:00');

-- Insert records into FailureRecords for warnings
INSERT INTO FailureRecords (Machine_ID, Failure_Status, Failure_Type, Downtime, Predicted_Failure_Probability, Predicted_Failure_Time)
VALUES
('Machine_015', 0, 'Electrical Failure', 0, 0.75, NULL),
('Machine_027', 0, 'Bearing Failure', 0, 0.72, NULL),
('Machine_037', 0, 'Overheating', 0, 0.78, NULL),
('Machine_016', 0, 'Electrical Failure', 0, 0.74, NULL),
('Machine_017', 0, 'Bearing Failure', 0, 0.73, NULL),
('Machine_018', 0, 'Overheating', 0, 0.76, NULL),
('Machine_019', 0, 'Motor Failure', 0, 0.75, NULL),
('Machine_020', 0, 'Overheating', 0, 0.77, NULL);

-- Insert records into SensorData for anomaly detection (warnings)
INSERT INTO SensorData (Machine_ID, Timestamp, Temperature, Vibration, Pressure, Humidity, Voltage, Current, Power_Consumption, Ambient_Temperature, Ambient_Humidity, Anomaly_Score, Anomaly_Flag)
VALUES
('Machine_015', '2024-03-10 10:00:00', 85.0, 5.0, 120.0, 60.0, 220.0, 15.0, 3.5, 25.0, 65.0, 0.78, 1),
('Machine_027', '2024-03-10 11:00:00', 90.0, 6.0, 125.0, 55.0, 225.0, 16.0, 4.0, 26.0, 70.0, 0.72, 1),
('Machine_037', '2024-03-10 12:00:00', 88.0, 4.5, 130.0, 58.0, 230.0, 14.0, 3.8, 27.0, 68.0, 0.75, 1),
('Machine_016', '2024-03-11 10:00:00', 87.0, 5.5, 122.0, 60.0, 220.0, 14.0, 3.6, 26.0, 66.0, 0.74, 1),
('Machine_017', '2024-03-11 11:00:00', 88.0, 6.0, 125.0, 58.0, 225.0, 15.0, 4.1, 27.0, 67.0, 0.73, 1),
('Machine_018', '2024-03-11 12:00:00', 89.0, 4.8, 130.0, 59.0, 230.0, 13.0, 3.9, 28.0, 68.0, 0.76, 1),
('Machine_019', '2024-03-11 13:00:00', 86.0, 5.2, 128.0, 57.0, 222.0, 12.0, 3.7, 25.0, 65.0, 0.75, 1),
('Machine_020', '2024-03-11 14:00:00', 85.0, 5.0, 126.0, 56.0, 221.0, 11.0, 3.8, 24.0, 64.0, 0.77, 1);

-- Add the Industry column to the Machines table if it doesn't exist
ALTER TABLE Machines ADD COLUMN Industry VARCHAR(50);

-- Populate the Industry column with sample data
UPDATE Machines
SET Industry = CASE
    WHEN Machine_ID LIKE 'Machine_0%' THEN 'Manufacturing'
    WHEN Machine_ID LIKE 'Machine_1%' THEN 'Energy'
    WHEN Machine_ID LIKE 'Machine_2%' THEN 'Automotive'
    ELSE 'General'
END;

-- Verify the changes
SELECT Machine_ID, Industry FROM Machines;

-- Verify data in Machines table
SELECT * FROM Machines;

-- Verify data in FailureRecords table
SELECT * FROM FailureRecords;

-- Verify data in SensorData table
SELECT * FROM SensorData;

-- Verify data in MaintenanceSchedule table
SELECT * FROM MaintenanceSchedule;

SELECT * FROM Machines;
TRUNCATE TABLE Machines;
SELECT * FROM FailureRecords;
TRUNCATE TABLE FailureRecords;
SELECT * FROM FailureTrends;
TRUNCATE TABLE FailureTrends;
SELECT * FROM MachineHealthIndicators;
TRUNCATE TABLE MachineHealthIndicators;
SELECT * FROM AnomalyDetection;
TRUNCATE TABLE AnomalyDetection;
SELECT * FROM MaintenanceSchedule;
TRUNCATE TABLE MaintenanceSchedule;
SELECT * FROM SensorData;
TRUNCATE TABLE SensorData;
SET foreign_key_checks = 1;

SHOW TABLES;

SELECT * FROM machine_status;
DESC machine_status;

-- Create SensorContributions table
CREATE TABLE SensorContributions (
    Sensor_ID INT AUTO_INCREMENT PRIMARY KEY,
    Sensor_Name VARCHAR(50),
    Contribution_Percentage FLOAT
);

-- Insert sample data into SensorContributions
INSERT INTO SensorContributions (Sensor_Name, Contribution_Percentage)
VALUES
('Temperature', 35.5),
('Vibration', 25.0),
('Pressure', 20.0),
('Humidity', 10.5),
('Power Consumption', 9.0);

-- Create TemperatureImpact table
CREATE TABLE TemperatureImpact (
    Impact_ID INT AUTO_INCREMENT PRIMARY KEY,
    Temperature FLOAT,
    Performance_Score FLOAT
);

-- Insert sample data into TemperatureImpact
INSERT INTO TemperatureImpact (Temperature, Performance_Score)
VALUES
(50, 90),
(60, 85),
(70, 80),
(80, 70),
(90, 60);

-- Create FailureForecasting table
CREATE TABLE FailureForecasting (
    Forecast_ID INT AUTO_INCREMENT PRIMARY KEY,
    Timestamp DATETIME,
    Failure_Probability FLOAT
);

-- Insert sample data into FailureForecasting
INSERT INTO FailureForecasting (Timestamp, Failure_Probability)
VALUES
('2025-03-01 00:00:00', 0.1),
('2025-03-02 00:00:00', 0.15),
('2025-03-03 00:00:00', 0.2),
('2025-03-04 00:00:00', 0.25),
('2025-03-05 00:00:00', 0.3);

-- Create IndustryFailureRates table
CREATE TABLE IndustryFailureRates (
    Industry_ID INT AUTO_INCREMENT PRIMARY KEY,
    Industry VARCHAR(50),
    Failure_Rate FLOAT
);

-- Insert sample data into IndustryFailureRates
INSERT INTO IndustryFailureRates (Industry, Failure_Rate)
VALUES
('Manufacturing', 15.0),
('Energy', 20.0),
('Automotive', 10.0),
('Healthcare', 5.0),
('Aerospace', 8.0);

-- Create WorkloadFailureProbability table
CREATE TABLE WorkloadFailureProbability (
    Workload_ID INT AUTO_INCREMENT PRIMARY KEY,
    Workload_Level VARCHAR(50),
    Failure_Probability FLOAT
);

-- Insert sample data into WorkloadFailureProbability
INSERT INTO WorkloadFailureProbability (Workload_Level, Failure_Probability)
VALUES
('Low', 0.05),
('Medium', 0.15),
('High', 0.25),
('Very High', 0.35);

-- Create PreventiveMaintenance table
CREATE TABLE PreventiveMaintenance (
    Maintenance_ID INT AUTO_INCREMENT PRIMARY KEY,
    Time_Interval INT,
    Failure_Rate FLOAT
);

-- Insert sample data into PreventiveMaintenance
INSERT INTO PreventiveMaintenance (Time_Interval, Failure_Rate)
VALUES
(30, 5.0),
(60, 10.0),
(90, 15.0),
(120, 20.0);

-- Create DeepLearningFailureDetection table
CREATE TABLE DeepLearningFailureDetection (
    Detection_ID INT AUTO_INCREMENT PRIMARY KEY,
    Timestamp DATETIME,
    Prediction_Score FLOAT
);

-- Insert sample data into DeepLearningFailureDetection
INSERT INTO DeepLearningFailureDetection (Timestamp, Prediction_Score)
VALUES
('2025-03-01 00:00:00', 0.1),
('2025-03-02 00:00:00', 0.2),
('2025-03-03 00:00:00', 0.3),
('2025-03-04 00:00:00', 0.4),
('2025-03-05 00:00:00', 0.5);

-- Verify the data
SELECT * FROM SensorContributions;
SELECT * FROM TemperatureImpact;
SELECT * FROM FailureForecasting;
SELECT * FROM IndustryFailureRates;
SELECT * FROM WorkloadFailureProbability;
SELECT * FROM PreventiveMaintenance;
SELECT * FROM DeepLearningFailureDetection;

SELECT * FROM MaintenanceSchedule WHERE Scheduled_Date >= CURDATE();




FROM MaintenanceSchedule;SELECT Machine_ID, Scheduled_Date-- Verify the Date Format in the Scheduled_Date Column


SELECT CURDATE() AS CurrentDate;-- Check the current date in the database
SELECT * FROM MaintenanceSchedule;