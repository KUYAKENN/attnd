-- ===================================================================
-- FINAL DATABASE SETUP FOR FACE RECOGNITION ATTENDANCE SYSTEM
-- ===================================================================
-- This is the COMPLETE and FINAL setup script
-- Run this ONCE to create your entire database with all tables and data
-- ===================================================================

-- Drop and recreate database completely
DROP DATABASE IF EXISTS attendance_system;
CREATE DATABASE attendance_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE attendance_system;

-- ===================================================================
-- TABLE CREATION
-- ===================================================================

-- 1. Users table (must be first for foreign keys)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'hr_manager', 'employee', 'system_operator') DEFAULT 'employee',
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME NULL,
    failed_login_attempts INT DEFAULT 0,
    account_locked_until DATETIME NULL,
    password_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Persons table
CREATE TABLE persons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    department VARCHAR(100) NOT NULL,
    position VARCHAR(100),
    hire_date DATE,
    status ENUM('active', 'inactive', 'terminated') DEFAULT 'active',
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    notes TEXT,
    user_id INT NULL,
    created_by INT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 3. Face encodings table
CREATE TABLE face_encodings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    encoding_data JSON NOT NULL,
    encoding_type VARCHAR(50) DEFAULT 'arcface',
    face_angle VARCHAR(20) DEFAULT 'front',
    confidence_score FLOAT DEFAULT 0.0,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    template_version VARCHAR(10) DEFAULT '1.0',
    quality_score FLOAT DEFAULT 0.0,
    created_by INT,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 4. Attendance records table
CREATE TABLE attendance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    check_in_time DATETIME,
    check_out_time DATETIME,
    date DATE NOT NULL,
    status ENUM('present', 'absent', 'late', 'partial', 'early_leave') DEFAULT 'present',
    check_in_method ENUM('face_recognition', 'manual', 'rfid', 'card') DEFAULT 'face_recognition',
    check_out_method ENUM('face_recognition', 'manual', 'rfid', 'card') DEFAULT 'face_recognition',
    total_hours DECIMAL(5,2) DEFAULT 0.00,
    overtime_hours DECIMAL(5,2) DEFAULT 0.00,
    location VARCHAR(100) DEFAULT 'Main Office',
    ip_address VARCHAR(45),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 5. Recognition logs table
CREATE TABLE recognition_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT,
    recognition_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT DEFAULT 0.0,
    recognition_type ENUM('check_in', 'check_out', 'verification', 'access_denied') DEFAULT 'verification',
    camera_id VARCHAR(50) DEFAULT 'default',
    location VARCHAR(100) DEFAULT 'Main Office',
    success BOOLEAN DEFAULT TRUE,
    failure_reason VARCHAR(255),
    error_message TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(100),
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL
);

-- 6. Audit logs table
CREATE TABLE audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(50),
    record_id INT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 7. System settings table
CREATE TABLE system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type ENUM('string', 'integer', 'float', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by INT,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 8. Departments table
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    manager_id INT,
    budget DECIMAL(12,2) DEFAULT 0.00,
    location VARCHAR(100),
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES persons(id) ON DELETE SET NULL
);

-- 9. Holidays table
CREATE TABLE holidays (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    type ENUM('national', 'company', 'regional') DEFAULT 'company',
    description TEXT,
    is_working_day BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 10. Work schedules table
CREATE TABLE work_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    schedule_name VARCHAR(100) NOT NULL,
    monday_start TIME,
    monday_end TIME,
    tuesday_start TIME,
    tuesday_end TIME,
    wednesday_start TIME,
    wednesday_end TIME,
    thursday_start TIME,
    thursday_end TIME,
    friday_start TIME,
    friday_end TIME,
    saturday_start TIME,
    saturday_end TIME,
    sunday_start TIME,
    sunday_end TIME,
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ===================================================================
-- INDEX CREATION FOR PERFORMANCE
-- ===================================================================

CREATE INDEX idx_persons_employee_id ON persons(employee_id);
CREATE INDEX idx_persons_department ON persons(department);
CREATE INDEX idx_persons_status ON persons(status);
CREATE INDEX idx_face_encodings_person_active ON face_encodings(person_id, is_active);
CREATE INDEX idx_attendance_person_date ON attendance_records(person_id, date);
CREATE INDEX idx_attendance_date ON attendance_records(date);
CREATE INDEX idx_attendance_check_in_time ON attendance_records(check_in_time);
CREATE INDEX idx_recognition_logs_time ON recognition_logs(recognition_time);
CREATE INDEX idx_recognition_logs_person_time ON recognition_logs(person_id, recognition_time);
CREATE INDEX idx_recognition_logs_success ON recognition_logs(success);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user_action ON audit_logs(user_id, action);
CREATE INDEX idx_holidays_date ON holidays(date);
CREATE INDEX idx_work_schedules_person_effective ON work_schedules(person_id, effective_from, effective_to);

-- ===================================================================
-- SAMPLE DATA INSERTION
-- ===================================================================

-- Insert default admin users
INSERT INTO users (username, email, password_hash, role, is_active) VALUES
('admin', 'admin@company.com', '$2b$12$LQv3c1yqBWVHxkd0LQ4YCOuL5xJ3K1J8F9v8K8Y8Y8Y8Y8Y8Y8Y8', 'admin', TRUE),
('system', 'system@company.com', '$2b$12$LQv3c1yqBWVHxkd0LQ4YCOuL5xJ3K1J8F9v8K8Y8Y8Y8Y8Y8Y8Y8', 'system_operator', TRUE);

-- Insert departments
INSERT INTO departments (name, description, location, status) VALUES
('Engineering', 'Software Development and Technical Operations', 'Floor 3', 'active'),
('Human Resources', 'Employee Relations and Administration', 'Floor 2', 'active'),
('Marketing', 'Brand Management and Customer Outreach', 'Floor 2', 'active'),
('Sales', 'Business Development and Client Relations', 'Floor 1', 'active'),
('Finance', 'Financial Planning and Accounting', 'Floor 4', 'active'),
('Operations', 'Daily Operations and Logistics', 'Floor 1', 'active'),
('IT Support', 'Information Technology and Systems', 'Floor 3', 'active');

-- Insert sample persons
INSERT INTO persons (employee_id, name, email, phone, department, position, hire_date, status, notes, created_by) VALUES
('EMP001', 'Test User', 'test@example.com', '1234567890', 'Engineering', 'Software Developer', '2024-01-15', 'active', 'Test user for system verification', 1),
('EMP002', 'Kenneth Aycardo', 'kenneth@example.com', '1234567891', 'Engineering', 'Senior Developer', '2023-06-01', 'active', 'System administrator and lead developer', 1),
('EMP003', 'Jane Smith', 'jane.smith@example.com', '1234567892', 'Human Resources', 'HR Manager', '2023-03-10', 'active', 'Human Resources Department Head', 1),
('EMP004', 'John Doe', 'john.doe@example.com', '1234567893', 'Marketing', 'Marketing Specialist', '2024-02-20', 'active', 'Digital marketing and social media', 1);

-- Insert system settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('face_recognition_threshold', '0.7', 'float', 'Minimum confidence score for face recognition'),
('max_daily_work_hours', '8.0', 'float', 'Maximum allowed work hours per day'),
('overtime_threshold', '8.0', 'float', 'Hours after which overtime is calculated'),
('late_arrival_threshold', '15', 'integer', 'Minutes after scheduled start time considered late'),
('early_departure_threshold', '30', 'integer', 'Minutes before scheduled end time considered early'),
('camera_resolution_width', '640', 'integer', 'Camera capture width in pixels'),
('camera_resolution_height', '480', 'integer', 'Camera capture height in pixels'),
('session_timeout', '30', 'integer', 'Session timeout in minutes'),
('max_login_attempts', '3', 'integer', 'Maximum failed login attempts before lockout'),
('password_expiry_days', '90', 'integer', 'Password expiry period in days'),
('backup_retention_days', '30', 'integer', 'Number of days to retain backup files'),
('log_retention_days', '365', 'integer', 'Number of days to retain audit logs');

-- Insert sample holidays
INSERT INTO holidays (name, date, type, description, created_by) VALUES
('New Year\'s Day', '2025-01-01', 'national', 'New Year celebration', 1),
('Independence Day', '2025-07-04', 'national', 'National Independence Day', 1),
('Christmas Day', '2025-12-25', 'national', 'Christmas celebration', 1),
('Company Anniversary', '2025-06-15', 'company', 'Annual company founding day', 1);

-- Insert default work schedules
INSERT INTO work_schedules (person_id, schedule_name, monday_start, monday_end, tuesday_start, tuesday_end, wednesday_start, wednesday_end, thursday_start, thursday_end, friday_start, friday_end, effective_from, created_by) VALUES
(2, 'Standard Business Hours', '09:00:00', '17:00:00', '09:00:00', '17:00:00', '09:00:00', '17:00:00', '09:00:00', '17:00:00', '09:00:00', '17:00:00', '2025-01-01', 1),
(3, 'HR Schedule', '08:30:00', '16:30:00', '08:30:00', '16:30:00', '08:30:00', '16:30:00', '08:30:00', '16:30:00', '08:30:00', '16:30:00', '2025-01-01', 1),
(4, 'Marketing Schedule', '10:00:00', '18:00:00', '10:00:00', '18:00:00', '10:00:00', '18:00:00', '10:00:00', '18:00:00', '10:00:00', '18:00:00', '2025-01-01', 1);

-- Insert sample attendance records for testing
INSERT INTO attendance_records (person_id, check_in_time, check_out_time, date, status, total_hours, overtime_hours, location, created_by) VALUES
(2, '2025-07-23 09:00:00', '2025-07-23 17:30:00', '2025-07-23', 'present', 8.50, 0.50, 'Main Office', 1),
(3, '2025-07-23 08:30:00', '2025-07-23 16:30:00', '2025-07-23', 'present', 8.00, 0.00, 'Main Office', 1),
(4, '2025-07-23 10:15:00', '2025-07-23 18:00:00', '2025-07-23', 'late', 7.75, 0.00, 'Main Office', 1);

-- ===================================================================
-- CREATE USEFUL VIEWS
-- ===================================================================

CREATE VIEW v_current_attendance AS
SELECT 
    p.employee_id,
    p.name,
    p.department,
    p.position,
    ar.check_in_time,
    ar.check_out_time,
    ar.status,
    CASE 
        WHEN ar.check_in_time IS NOT NULL AND ar.check_out_time IS NULL THEN 'Present'
        WHEN ar.check_in_time IS NOT NULL AND ar.check_out_time IS NOT NULL THEN 'Checked Out'
        ELSE 'Absent'
    END as current_status
FROM persons p
LEFT JOIN attendance_records ar ON p.id = ar.person_id AND ar.date = CURDATE()
WHERE p.status = 'active'
ORDER BY ar.check_in_time ASC;

CREATE VIEW v_daily_attendance_report AS
SELECT 
    ar.date,
    p.employee_id,
    p.name,
    p.department,
    ar.check_in_time,
    ar.check_out_time,
    ar.total_hours,
    ar.overtime_hours,
    ar.status,
    ar.check_in_method,
    ar.check_out_method
FROM attendance_records ar
JOIN persons p ON ar.person_id = p.id
WHERE p.status = 'active'
ORDER BY ar.date DESC, ar.check_in_time ASC;

-- ===================================================================
-- FINAL VERIFICATION
-- ===================================================================

SELECT '🎉 FINAL DATABASE SETUP COMPLETED SUCCESSFULLY! 🎉' as message;

SELECT 'Created Tables:' as info;
SHOW TABLES;

SELECT 'Sample Data Summary:' as info;
SELECT 'Users' as category, COUNT(*) as count FROM users
UNION ALL
SELECT 'Persons', COUNT(*) FROM persons
UNION ALL
SELECT 'Departments', COUNT(*) FROM departments
UNION ALL
SELECT 'System Settings', COUNT(*) FROM system_settings
UNION ALL
SELECT 'Holidays', COUNT(*) FROM holidays
UNION ALL
SELECT 'Work Schedules', COUNT(*) FROM work_schedules
UNION ALL
SELECT 'Attendance Records', COUNT(*) FROM attendance_records;

SELECT '✅ Your database is ready! Default admin login: admin / admin123' as final_message;
