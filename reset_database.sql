-- ATTENDANCE SYSTEM - COMPLETE DATABASE RESET
-- Drop existing database and recreate everything

-- Drop existing database if it exists
DROP DATABASE IF EXISTS attendance_system;

-- Create new database
CREATE DATABASE attendance_system;
USE attendance_system;

-- Create persons table
CREATE TABLE persons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    department VARCHAR(100),
    position VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    face_encoding LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create attendance_records table
CREATE TABLE attendance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    employee_id VARCHAR(50) NOT NULL,
    action ENUM('check_in', 'check_out') NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence FLOAT,
    overtime_hours DECIMAL(5,2) DEFAULT 0.00,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    INDEX idx_person_timestamp (person_id, timestamp),
    INDEX idx_employee_id (employee_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_action (action)
);

-- Create recognition_logs table
CREATE TABLE recognition_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT,
    employee_id VARCHAR(50),
    confidence FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_path VARCHAR(500),
    status ENUM('success', 'failed', 'low_confidence') DEFAULT 'success',
    notes TEXT,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL,
    INDEX idx_timestamp (timestamp),
    INDEX idx_status (status),
    INDEX idx_employee_id (employee_id)
);

-- Create admin_sessions table for authentication
CREATE TABLE admin_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Insert sample data
INSERT INTO persons (name, employee_id, department, position, email, phone) VALUES
('John Doe', 'EMP001', 'IT Department', 'Software Developer', 'john.doe@company.com', '+1234567890'),
('Jane Smith', 'EMP002', 'HR Department', 'HR Manager', 'jane.smith@company.com', '+1234567891'),
('Mike Johnson', 'EMP003', 'Finance', 'Accountant', 'mike.johnson@company.com', '+1234567892');

-- Insert sample attendance records
INSERT INTO attendance_records (person_id, employee_id, action, timestamp, confidence, overtime_hours) VALUES
(1, 'EMP001', 'check_in', '2025-01-20 08:00:00', 95.5, 0.00),
(1, 'EMP001', 'check_out', '2025-01-20 17:30:00', 94.2, 0.50),
(2, 'EMP002', 'check_in', '2025-01-20 08:15:00', 96.8, 0.00),
(2, 'EMP002', 'check_out', '2025-01-20 17:00:00', 95.1, 0.00),
(3, 'EMP003', 'check_in', '2025-01-20 08:30:00', 93.7, 0.00),
(3, 'EMP003', 'check_out', '2025-01-20 18:00:00', 94.9, 1.00);

-- Create performance indexes
CREATE INDEX idx_persons_employee_id ON persons(employee_id);
CREATE INDEX idx_persons_active ON persons(is_active);
CREATE INDEX idx_attendance_date ON attendance_records(DATE(timestamp));

-- Show created tables
SHOW TABLES;

-- Verify table structures
SELECT 'Database reset completed successfully!' as Status;
