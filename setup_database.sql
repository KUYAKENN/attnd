-- FACE RECOGNITION ATTENDANCE SYSTEM DATABASE SETUP
-- Enhanced Security and Compliance Version 2.1
-- Run these commands in MySQL Workbench or phpMyAdmin

-- 1. Create database with proper character set
CREATE DATABASE IF NOT EXISTS attendance_system 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
USE attendance_system;

-- 2. Create users table for authentication and authorization
CREATE TABLE IF NOT EXISTS users (
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
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 3. Create persons table
CREATE TABLE IF NOT EXISTS persons (
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
    created_by INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
);

-- 4. Create face_encodings table  
CREATE TABLE IF NOT EXISTS face_encodings (
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
    created_by INT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
);

-- 5. Create attendance_records table
CREATE TABLE IF NOT EXISTS attendance_records (
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
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_person_date (person_id, date),
    INDEX idx_date (date),
    INDEX idx_check_in_time (check_in_time)
);

-- 6. Create recognition_logs table
CREATE TABLE IF NOT EXISTS recognition_logs (
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
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL,
    INDEX idx_recognition_time (recognition_time),
    INDEX idx_person_time (person_id, recognition_time),
    INDEX idx_success (success)
);

-- 7. Create audit_logs table for security tracking
CREATE TABLE IF NOT EXISTS audit_logs (
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
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_timestamp (timestamp),
    INDEX idx_user_action (user_id, action),
    INDEX idx_table_record (table_name, record_id)
);

-- 8. Create system_settings table
CREATE TABLE IF NOT EXISTS system_settings (
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

-- 9. Create departments table
CREATE TABLE IF NOT EXISTS departments (
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

-- 10. Create holidays table
CREATE TABLE IF NOT EXISTS holidays (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    type ENUM('national', 'company', 'regional') DEFAULT 'company',
    description TEXT,
    is_working_day BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_date (date)
);

-- 11. Create work_schedules table
CREATE TABLE IF NOT EXISTS work_schedules (
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
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_person_effective (person_id, effective_from, effective_to)
);

-- 12. Insert default admin user (password: admin123 - CHANGE THIS!)
INSERT INTO users (username, email, password_hash, role, is_active) VALUES
('admin', 'admin@company.com', '$2b$12$LQv3c1yqBWVHxkd0LQ4YCOuL5xJ3K1J8F9v8K8Y8Y8Y8Y8Y8Y8Y8', 'admin', TRUE),
('system', 'system@company.com', '$2b$12$LQv3c1yqBWVHxkd0LQ4YCOuL5xJ3K1J8F9v8K8Y8Y8Y8Y8Y8Y8Y8', 'system_operator', TRUE);

-- 13. Insert default departments
INSERT INTO departments (name, description, location, status) VALUES
('Engineering', 'Software Development and Technical Operations', 'Floor 3', 'active'),
('Human Resources', 'Employee Relations and Administration', 'Floor 2', 'active'),
('Marketing', 'Brand Management and Customer Outreach', 'Floor 2', 'active'),
('Sales', 'Business Development and Client Relations', 'Floor 1', 'active'),
('Finance', 'Financial Planning and Accounting', 'Floor 4', 'active'),
('Operations', 'Daily Operations and Logistics', 'Floor 1', 'active'),
('IT Support', 'Information Technology and Systems', 'Floor 3', 'active');

-- 14. Insert test data with proper department references
INSERT INTO persons (employee_id, name, email, phone, department, position, hire_date, status, notes, created_by) VALUES
('EMP001', 'Test User', 'test@example.com', '1234567890', 'Engineering', 'Software Developer', '2024-01-15', 'active', 'Test user for system verification', 1),
('EMP002', 'Kenneth Aycardo', 'kenneth@example.com', '1234567891', 'Engineering', 'Senior Developer', '2023-06-01', 'active', 'System administrator and lead developer', 1),
('EMP003', 'Jane Smith', 'jane.smith@example.com', '1234567892', 'Human Resources', 'HR Manager', '2023-03-10', 'active', 'Human Resources Department Head', 1),
('EMP004', 'John Doe', 'john.doe@example.com', '1234567893', 'Marketing', 'Marketing Specialist', '2024-02-20', 'active', 'Digital marketing and social media', 1);

-- 15. Insert default system settings
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

-- 16. Insert sample holidays
INSERT INTO holidays (name, date, type, description, created_by) VALUES
('New Year\'s Day', '2025-01-01', 'national', 'New Year celebration', 1),
('Independence Day', '2025-07-04', 'national', 'National Independence Day', 1),
('Christmas Day', '2025-12-25', 'national', 'Christmas celebration', 1),
('Company Anniversary', '2025-06-15', 'company', 'Annual company founding day', 1);

-- 17. Insert default work schedule
INSERT INTO work_schedules (person_id, schedule_name, monday_start, monday_end, tuesday_start, tuesday_end, wednesday_start, wednesday_end, thursday_start, thursday_end, friday_start, friday_end, effective_from, created_by) VALUES
(2, 'Standard Business Hours', '09:00:00', '17:00:00', '09:00:00', '17:00:00', '09:00:00', '17:00:00', '09:00:00', '17:00:00', '09:00:00', '17:00:00', '2025-01-01', 1),
(3, 'HR Schedule', '08:30:00', '16:30:00', '08:30:00', '16:30:00', '08:30:00', '16:30:00', '08:30:00', '16:30:00', '08:30:00', '16:30:00', '2025-01-01', 1),
(4, 'Marketing Schedule', '10:00:00', '18:00:00', '10:00:00', '18:00:00', '10:00:00', '18:00:00', '10:00:00', '18:00:00', '10:00:00', '18:00:00', '2025-01-01', 1);

-- 18. Create database views for common queries
CREATE VIEW IF NOT EXISTS v_employee_attendance_summary AS
SELECT 
    p.id,
    p.employee_id,
    p.name,
    p.department,
    p.position,
    COUNT(ar.id) as total_attendance_days,
    AVG(ar.total_hours) as avg_daily_hours,
    SUM(ar.total_hours) as total_hours_worked,
    SUM(ar.overtime_hours) as total_overtime_hours,
    COUNT(CASE WHEN ar.status = 'late' THEN 1 END) as late_days,
    COUNT(CASE WHEN ar.status = 'early_leave' THEN 1 END) as early_leave_days
FROM persons p
LEFT JOIN attendance_records ar ON p.id = ar.person_id
WHERE p.status = 'active'
GROUP BY p.id, p.employee_id, p.name, p.department, p.position;

CREATE VIEW IF NOT EXISTS v_daily_attendance_report AS
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

CREATE VIEW IF NOT EXISTS v_current_attendance AS
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

-- 19. Create stored procedures for common operations
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS sp_record_attendance(
    IN p_person_id INT,
    IN p_recognition_type ENUM('check_in', 'check_out'),
    IN p_confidence_score FLOAT,
    IN p_camera_id VARCHAR(50),
    IN p_location VARCHAR(100),
    IN p_ip_address VARCHAR(45)
)
BEGIN
    DECLARE v_current_date DATE DEFAULT CURDATE();
    DECLARE v_current_time DATETIME DEFAULT NOW();
    DECLARE v_attendance_id INT;
    
    -- Insert recognition log
    INSERT INTO recognition_logs (
        person_id, recognition_time, confidence_score, 
        recognition_type, camera_id, location, success, ip_address
    ) VALUES (
        p_person_id, v_current_time, p_confidence_score,
        p_recognition_type, p_camera_id, p_location, TRUE, p_ip_address
    );
    
    -- Check if attendance record exists for today
    SELECT id INTO v_attendance_id 
    FROM attendance_records 
    WHERE person_id = p_person_id AND date = v_current_date;
    
    IF v_attendance_id IS NULL THEN
        -- Create new attendance record
        INSERT INTO attendance_records (
            person_id, date, check_in_time, check_in_method, location, ip_address
        ) VALUES (
            p_person_id, v_current_date, v_current_time, 'face_recognition', p_location, p_ip_address
        );
    ELSE
        -- Update existing record
        IF p_recognition_type = 'check_out' THEN
            UPDATE attendance_records 
            SET check_out_time = v_current_time,
                check_out_method = 'face_recognition',
                total_hours = TIMESTAMPDIFF(MINUTE, check_in_time, v_current_time) / 60.0,
                overtime_hours = GREATEST(0, (TIMESTAMPDIFF(MINUTE, check_in_time, v_current_time) / 60.0) - 8.0)
            WHERE id = v_attendance_id;
        END IF;
    END IF;
END //

DELIMITER ;

-- 20. Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_persons_employee_id ON persons(employee_id);
CREATE INDEX IF NOT EXISTS idx_persons_department ON persons(department);
CREATE INDEX IF NOT EXISTS idx_persons_status ON persons(status);
CREATE INDEX IF NOT EXISTS idx_face_encodings_person_active ON face_encodings(person_id, is_active);
CREATE INDEX IF NOT EXISTS idx_attendance_person_date_status ON attendance_records(person_id, date, status);
CREATE INDEX IF NOT EXISTS idx_recognition_logs_time_success ON recognition_logs(recognition_time, success);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp);

-- 21. Verify setup and show summary
SELECT 'Enhanced Database setup completed successfully!' as message;
SELECT 
    TABLE_NAME as 'Tables Created',
    TABLE_ROWS as 'Row Count'
FROM information_schema.tables 
WHERE table_schema = 'attendance_system' 
ORDER BY TABLE_NAME;

SELECT 'Sample Data Summary:' as info;
SELECT 'Users:' as category, COUNT(*) as count FROM users
UNION ALL
SELECT 'Persons:', COUNT(*) FROM persons
UNION ALL
SELECT 'Departments:', COUNT(*) FROM departments
UNION ALL
SELECT 'System Settings:', COUNT(*) FROM system_settings
UNION ALL
SELECT 'Holidays:', COUNT(*) FROM holidays
UNION ALL
SELECT 'Work Schedules:', COUNT(*) FROM work_schedules;


