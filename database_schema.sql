-- Face Recognition Attendance System Database Schema
-- MySQL Database Setup for Production

-- Create the database
CREATE DATABASE IF NOT EXISTS attendance_system;
USE attendance_system;

-- Set timezone to ensure consistent timestamps
SET time_zone = '+00:00';

-- ============================================
-- Table: persons
-- ============================================
CREATE TABLE IF NOT EXISTS persons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    department VARCHAR(100),
    position VARCHAR(100),
    status ENUM('active', 'inactive') DEFAULT 'active',
    registration_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    notes TEXT,
    
    INDEX idx_email (email),
    INDEX idx_status (status),
    INDEX idx_department (department),
    INDEX idx_registration_date (registration_date)
);

-- ============================================
-- Table: face_encodings
-- ============================================
CREATE TABLE IF NOT EXISTS face_encodings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT NOT NULL,
    encoding_data JSON NOT NULL,
    encoding_type VARCHAR(50) DEFAULT 'arcface',
    face_angle VARCHAR(20) DEFAULT 'front',
    confidence_score FLOAT DEFAULT 0.0,
    created_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    INDEX idx_person_id (person_id),
    INDEX idx_is_primary (is_primary),
    INDEX idx_created_date (created_date)
);

-- ============================================
-- Table: attendance_records
-- ============================================
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
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    UNIQUE KEY unique_person_date (person_id, date),
    INDEX idx_person_id (person_id),
    INDEX idx_date (date),
    INDEX idx_status (status),
    INDEX idx_check_in_time (check_in_time)
);

-- ============================================
-- Table: recognition_logs
-- ============================================
CREATE TABLE IF NOT EXISTS recognition_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    person_id INT,
    recognition_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confidence_score FLOAT DEFAULT 0.0,
    recognition_type ENUM('check_in', 'check_out', 'verification') DEFAULT 'verification',
    camera_id VARCHAR(50) DEFAULT 'default',
    face_image_path VARCHAR(255),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    ip_address VARCHAR(45),
    
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL,
    INDEX idx_person_id (person_id),
    INDEX idx_recognition_time (recognition_time),
    INDEX idx_success (success),
    INDEX idx_recognition_type (recognition_type)
);

-- ============================================
-- Table: system_settings
-- ============================================
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT,
    setting_type ENUM('string', 'integer', 'float', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_setting_key (setting_key)
);

-- ============================================
-- INSERT DEFAULT DATA
-- ============================================

-- Insert default system settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('recognition_threshold', '0.6', 'float', 'Minimum similarity threshold for face recognition'),
('max_face_encodings', '5', 'integer', 'Maximum number of face encodings per person'),
('work_start_time', '09:00:00', 'string', 'Default work start time'),
('work_end_time', '17:00:00', 'string', 'Default work end time'),
('late_threshold_minutes', '15', 'integer', 'Minutes after start time to mark as late'),
('auto_checkout_enabled', 'false', 'boolean', 'Enable automatic checkout at end of day')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- ============================================
-- SAMPLE DATA (for testing)
-- ============================================

-- Insert a sample employee for testing
INSERT INTO persons (name, email, phone, department, position, status, notes) VALUES
('John Doe', 'john.doe@company.com', '+1234567890', 'Information Technology', 'Software Developer', 'active', 'Sample employee for testing')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Show final status
SELECT 'Database schema created successfully!' as Status;
SELECT COUNT(*) as Total_Tables FROM information_schema.tables WHERE table_schema = 'attendance_system';

-- ============================================================================
-- PERSONS TABLE - Store registered people information
-- ============================================================================
CREATE TABLE IF NOT EXISTS persons (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    department VARCHAR(100),
    position VARCHAR(100),
    status ENUM('active', 'inactive') DEFAULT 'active',
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    notes TEXT,
    
    -- Indexes for better performance
    INDEX idx_name (name),
    INDEX idx_email (email),
    INDEX idx_status (status),
    INDEX idx_department (department)
);

-- ============================================================================
-- FACE_ENCODINGS TABLE - Store face recognition encodings
-- ============================================================================
CREATE TABLE IF NOT EXISTS face_encodings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    person_id INT NOT NULL,
    encoding_data TEXT NOT NULL,  -- JSON string of face encoding array
    encoding_type ENUM('standard', 'enhanced', 'multi_angle') DEFAULT 'standard',
    face_angle ENUM('front', 'left', 'right', 'up', 'down') DEFAULT 'front',
    confidence_score DECIMAL(3,2) DEFAULT 0.80,
    image_path VARCHAR(500),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT FALSE,
    
    -- Foreign key constraint
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_person_id (person_id),
    INDEX idx_encoding_type (encoding_type),
    INDEX idx_face_angle (face_angle),
    INDEX idx_is_primary (is_primary)
);

-- ============================================================================
-- ATTENDANCE TABLE - Store attendance records
-- ============================================================================
CREATE TABLE IF NOT EXISTS attendance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    person_id INT NOT NULL,
    person_name VARCHAR(255) NOT NULL,  -- Denormalized for faster queries
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_out_time TIMESTAMP NULL,
    date_recorded DATE NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    detection_method ENUM('auto', 'manual', 'override') DEFAULT 'auto',
    image_path VARCHAR(500),
    location_id INT,
    status ENUM('present', 'late', 'early_leave', 'absent') DEFAULT 'present',
    notes TEXT,
    created_by VARCHAR(100) DEFAULT 'system',
    
    -- Foreign key constraint
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    
    -- Composite unique constraint to prevent duplicate entries per day
    UNIQUE KEY unique_person_date (person_id, date_recorded),
    
    -- Indexes for better performance
    INDEX idx_person_id (person_id),
    INDEX idx_date_recorded (date_recorded),
    INDEX idx_person_name (person_name),
    INDEX idx_status (status),
    INDEX idx_check_in_time (check_in_time),
    INDEX idx_confidence_score (confidence_score)
);

-- ============================================================================
-- LOCATIONS TABLE - Store detection locations/cameras
-- ============================================================================
CREATE TABLE IF NOT EXISTS locations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    camera_id VARCHAR(100),
    coordinates TEXT,  -- Store coordinates as text instead of JSON for compatibility
    status ENUM('active', 'inactive', 'maintenance') DEFAULT 'active',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_name (name),
    INDEX idx_status (status)
);

-- ============================================================================
-- RECOGNITION_LOGS TABLE - Detailed logs of all recognition attempts
-- ============================================================================
CREATE TABLE IF NOT EXISTS recognition_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    person_id INT,
    person_name VARCHAR(255),
    recognition_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score DECIMAL(3,2) NOT NULL,
    detection_status ENUM('recognized', 'unknown', 'low_confidence', 'failed') NOT NULL,
    image_path VARCHAR(500),
    location_id INT,
    processing_time_ms INT,  -- How long recognition took
    face_coordinates TEXT,   -- Bounding box coordinates as text
    notes TEXT,
    
    -- Foreign key constraints (nullable for unknown persons)
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL,
    
    -- Indexes
    INDEX idx_person_id (person_id),
    INDEX idx_recognition_time (recognition_time),
    INDEX idx_detection_status (detection_status),
    INDEX idx_confidence_score (confidence_score)
);

-- ============================================================================
-- SYSTEM_SETTINGS TABLE - Store application configuration
-- ============================================================================
CREATE TABLE IF NOT EXISTS system_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    data_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by VARCHAR(100) DEFAULT 'system',
    
    -- Index
    INDEX idx_setting_key (setting_key),
    INDEX idx_category (category)
);

-- ============================================================================
-- INSERT DEFAULT DATA
-- ============================================================================

-- Insert default location
INSERT INTO locations (name, description, status) VALUES 
('Main Entrance', 'Primary entrance camera', 'active'),
('Office Floor 1', 'Office area monitoring', 'active')
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- Insert default system settings
INSERT INTO system_settings (setting_key, setting_value, data_type, description, category) VALUES 
('confidence_threshold', '0.6', 'number', 'Minimum confidence score for face recognition', 'recognition'),
('max_faces_per_person', '5', 'number', 'Maximum face encodings per person', 'recognition'),
('attendance_grace_period', '15', 'number', 'Grace period in minutes for late arrival', 'attendance'),
('auto_checkout_time', '18:00', 'string', 'Automatic checkout time if not manually checked out', 'attendance'),
('image_retention_days', '30', 'number', 'Number of days to keep captured images', 'storage'),
('enable_realtime_detection', 'true', 'boolean', 'Enable real-time face detection', 'features'),
('working_hours_start', '09:00', 'string', 'Standard working hours start time', 'attendance'),
('working_hours_end', '17:00', 'string', 'Standard working hours end time', 'attendance')
ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value);

-- ============================================================================
-- ADDITIONAL INDEXES FOR PERFORMANCE OPTIMIZATION
-- ============================================================================

-- Additional composite indexes for common query patterns
CREATE INDEX idx_attendance_date_person ON attendance(date_recorded, person_id);
CREATE INDEX idx_recognition_time_status ON recognition_logs(recognition_time, detection_status);
CREATE INDEX idx_person_status_name ON persons(status, name);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Show completion message
SELECT 
'✅ Face Recognition Database Schema Created Successfully!' as Status,
'All tables and indexes have been created.' as Message,
'Ready to use with your Flask application!' as NextStep;

-- Show created tables
SHOW TABLES;

-- Show table structures
DESCRIBE persons;
DESCRIBE face_encodings;
DESCRIBE attendance;
DESCRIBE locations;
DESCRIBE recognition_logs;
DESCRIBE system_settings;
