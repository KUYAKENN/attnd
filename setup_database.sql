-- QUICK SETUP SCRIPT FOR ATTENDANCE SYSTEM DATABASE
-- Run these commands in MySQL Workbench or phpMyAdmin

-- 1. Create database
CREATE DATABASE IF NOT EXISTS attendance_system;
USE attendance_system;

-- 2. Create persons table
CREATE TABLE IF NOT EXISTS persons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    department VARCHAR(100),
    position VARCHAR(100),
    status ENUM('active', 'inactive') DEFAULT 'active',
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    notes TEXT
);

-- 3. Create face_encodings table  
CREATE TABLE IF NOT EXISTS face_encodings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    encoding_data JSON NOT NULL,
    encoding_type VARCHAR(50) DEFAULT 'arcface',
    face_angle VARCHAR(20) DEFAULT 'front',
    confidence_score FLOAT DEFAULT 0.0,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
);

-- 4. Create attendance_records table
CREATE TABLE IF NOT EXISTS attendance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    check_in_time DATETIME,
    check_out_time DATETIME,
    date DATE NOT NULL,
    status ENUM('present', 'absent', 'late', 'partial') DEFAULT 'present',
    check_in_method ENUM('face_recognition', 'manual', 'rfid') DEFAULT 'face_recognition',
    check_out_method ENUM('face_recognition', 'manual', 'rfid') DEFAULT 'face_recognition',
    total_hours DECIMAL(4,2) DEFAULT 0.00,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
);

-- 5. Create recognition_logs table
CREATE TABLE IF NOT EXISTS recognition_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT,
    recognition_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT DEFAULT 0.0,
    recognition_type ENUM('check_in', 'check_out', 'verification') DEFAULT 'verification',
    camera_id VARCHAR(50) DEFAULT 'default',
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL
);

-- 6. Insert test data
INSERT INTO persons (name, email, phone, department, position, status, notes) VALUES
('Test User', 'test@example.com', '1234567890', 'IT', 'Developer', 'active', 'Test user for system verification'),
('Kenneth Aycardo', 'kenneth@example.com', '1234567891', 'Engineering', 'Senior Developer', 'active', 'System administrator');

-- 7. Verify setup
SELECT 'Database setup completed successfully!' as message;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'attendance_system';
SELECT * FROM persons;


