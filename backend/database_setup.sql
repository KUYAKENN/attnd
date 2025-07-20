-- MySQL Database Setup for Face Recognition Attendance System
-- Run this script in MySQL to create the database and tables

-- Create database
CREATE DATABASE IF NOT EXISTS attendance_system;
USE attendance_system;

-- Create persons table
CREATE TABLE IF NOT EXISTS persons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    department VARCHAR(100),
    position VARCHAR(100),
    status ENUM('active', 'inactive') DEFAULT 'active',
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    notes TEXT,
    INDEX idx_name (name),
    INDEX idx_status (status),
    INDEX idx_department (department)
);

-- Create face_encodings table
CREATE TABLE IF NOT EXISTS face_encodings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    encoding_data TEXT NOT NULL,
    encoding_type VARCHAR(50) DEFAULT 'arcface',
    face_angle VARCHAR(20) DEFAULT 'front',
    confidence_score FLOAT DEFAULT 0.0,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    INDEX idx_person_id (person_id),
    INDEX idx_is_primary (is_primary)
);

-- Create attendance table
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    person_name VARCHAR(255) NOT NULL,
    check_in_time DATETIME NOT NULL,
    check_out_time DATETIME NULL,
    date_recorded DATE NOT NULL,
    confidence_score FLOAT DEFAULT 0.0,
    detection_method ENUM('auto', 'manual') DEFAULT 'auto',
    status ENUM('present', 'late', 'absent') DEFAULT 'present',
    created_by VARCHAR(100) DEFAULT 'system',
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    INDEX idx_person_id (person_id),
    INDEX idx_date_recorded (date_recorded),
    INDEX idx_check_in_time (check_in_time),
    INDEX idx_status (status)
);

-- Create recognition_logs table for monitoring
CREATE TABLE IF NOT EXISTS recognition_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NULL,
    recognition_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT DEFAULT 0.0,
    detection_status ENUM('recognized', 'unknown', 'error') DEFAULT 'unknown',
    processing_time_ms INT DEFAULT 0,
    face_coordinates JSON,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL,
    INDEX idx_recognition_time (recognition_time),
    INDEX idx_detection_status (detection_status),
    INDEX idx_person_id (person_id)
);

-- Insert sample data
INSERT INTO persons (name, email, phone, department, position, status, notes) VALUES
('John Doe', 'john.doe@company.com', '+1234567890', 'Engineering', 'Software Developer', 'active', 'Senior developer'),
('Jane Smith', 'jane.smith@company.com', '+1234567891', 'Human Resources', 'HR Manager', 'active', 'HR team lead'),
('Mike Johnson', 'mike.johnson@company.com', '+1234567892', 'Marketing', 'Marketing Specialist', 'active', 'Digital marketing expert');

-- Insert sample face encodings (placeholder data)
INSERT INTO face_encodings (person_id, encoding_data, encoding_type, face_angle, confidence_score, is_primary) VALUES
(1, '[]', 'arcface', 'front', 0.95, TRUE),
(2, '[]', 'arcface', 'front', 0.92, TRUE),
(3, '[]', 'arcface', 'front', 0.88, TRUE);

-- Insert sample attendance for today
INSERT INTO attendance (person_id, person_name, check_in_time, date_recorded, confidence_score, detection_method, status, created_by) VALUES
(1, 'John Doe', NOW(), CURDATE(), 0.92, 'auto', 'present', 'face_recognition_system'),
(2, 'Jane Smith', DATE_SUB(NOW(), INTERVAL 30 MINUTE), CURDATE(), 0.89, 'auto', 'present', 'face_recognition_system');

-- Show created tables
SHOW TABLES;

-- Display sample data
SELECT 'Persons Table:' as Info;
SELECT * FROM persons;

SELECT 'Face Encodings Table:' as Info;
SELECT * FROM face_encodings;

SELECT 'Attendance Table:' as Info;
SELECT * FROM attendance;

SELECT 'Recognition Logs Table:' as Info;
SELECT * FROM recognition_logs;

COMMIT;
