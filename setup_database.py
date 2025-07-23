#!/usr/bin/env python3
"""
Database Setup Script for Face Recognition Attendance System
This script will drop existing database and recreate everything
"""

import mysql.connector
import sys
from mysql.connector import Error

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Change this to your MySQL username
    'password': '',  # Change this to your MySQL password
    'charset': 'utf8mb4'
}

DATABASE_NAME = 'attendance_system'

def create_connection():
    """Create MySQL connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("✅ Connected to MySQL server")
            return connection
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

def execute_query(connection, query, data=None):
    """Execute a single query"""
    try:
        cursor = connection.cursor()
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        connection.commit()
        return cursor
    except Error as e:
        print(f"❌ Error executing query: {e}")
        return None

def setup_database():
    """Main function to set up the database"""
    connection = create_connection()
    if not connection:
        return False

    try:
        print("🗑️  Dropping existing database if exists...")
        execute_query(connection, f"DROP DATABASE IF EXISTS {DATABASE_NAME}")
        
        print("🏗️  Creating new database...")
        execute_query(connection, f"CREATE DATABASE {DATABASE_NAME}")
        execute_query(connection, f"USE {DATABASE_NAME}")
        
        print("📋 Creating persons table...")
        persons_table = """
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
        )
        """
        execute_query(connection, persons_table)
        
        print("📊 Creating attendance_records table...")
        attendance_table = """
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
        )
        """
        execute_query(connection, attendance_table)
        
        print("📝 Creating recognition_logs table...")
        logs_table = """
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
        )
        """
        execute_query(connection, logs_table)
        
        print("🔐 Creating admin_sessions table...")
        sessions_table = """
        CREATE TABLE admin_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        )
        """
        execute_query(connection, sessions_table)
        
        print("👥 Inserting sample persons...")
        sample_persons = [
            ('John Doe', 'EMP001', 'IT Department', 'Software Developer', 'john.doe@company.com', '+1234567890'),
            ('Jane Smith', 'EMP002', 'HR Department', 'HR Manager', 'jane.smith@company.com', '+1234567891'),
            ('Mike Johnson', 'EMP003', 'Finance', 'Accountant', 'mike.johnson@company.com', '+1234567892')
        ]
        
        insert_person_query = """
        INSERT INTO persons (name, employee_id, department, position, email, phone) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor = connection.cursor()
        cursor.executemany(insert_person_query, sample_persons)
        connection.commit()
        
        print("⏰ Inserting sample attendance records...")
        sample_attendance = [
            (1, 'EMP001', 'check_in', '2025-01-20 08:00:00', 95.5, 0.00),
            (1, 'EMP001', 'check_out', '2025-01-20 17:30:00', 94.2, 0.50),
            (2, 'EMP002', 'check_in', '2025-01-20 08:15:00', 96.8, 0.00),
            (2, 'EMP002', 'check_out', '2025-01-20 17:00:00', 95.1, 0.00),
            (3, 'EMP003', 'check_in', '2025-01-20 08:30:00', 93.7, 0.00),
            (3, 'EMP003', 'check_out', '2025-01-20 18:00:00', 94.9, 1.00)
        ]
        
        insert_attendance_query = """
        INSERT INTO attendance_records (person_id, employee_id, action, timestamp, confidence, overtime_hours) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.executemany(insert_attendance_query, sample_attendance)
        connection.commit()
        
        print("🚀 Creating performance indexes...")
        indexes = [
            "CREATE INDEX idx_persons_employee_id ON persons(employee_id)",
            "CREATE INDEX idx_persons_active ON persons(is_active)",
            "CREATE INDEX idx_attendance_date ON attendance_records(DATE(timestamp))"
        ]
        
        for index in indexes:
            execute_query(connection, index)
        
        print("📋 Showing created tables...")
        cursor = execute_query(connection, "SHOW TABLES")
        if cursor:
            tables = cursor.fetchall()
            for table in tables:
                print(f"   ✅ {table[0]}")
        
        print("\n🎉 Database setup completed successfully!")
        print(f"   📦 Database: {DATABASE_NAME}")
        print("   📊 Tables: persons, attendance_records, recognition_logs, admin_sessions")
        print("   👥 Sample data: 3 employees with attendance records")
        print("   🔍 Indexes: Created for better performance")
        
        return True
        
    except Error as e:
        print(f"❌ Error setting up database: {e}")
        return False
    
    finally:
        if connection.is_connected():
            connection.close()
            print("🔌 MySQL connection closed")

def check_mysql_connection():
    """Check if MySQL is accessible"""
    print("🔍 Checking MySQL connection...")
    connection = create_connection()
    if connection:
        connection.close()
        return True
    return False

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 FACE RECOGNITION ATTENDANCE SYSTEM - DATABASE SETUP")
    print("=" * 60)
    
    # Check MySQL connection first
    if not check_mysql_connection():
        print("\n❌ Cannot connect to MySQL!")
        print("   Please check:")
        print("   1. MySQL server is running")
        print("   2. Username and password in DB_CONFIG")
        print("   3. MySQL connector is installed: pip install mysql-connector-python")
        sys.exit(1)
    
    # Setup database
    if setup_database():
        print("\n✅ Setup completed! Your attendance system is ready to use.")
        print("   🚀 Start your Flask app: python app.py")
    else:
        print("\n❌ Setup failed! Please check the errors above.")
        sys.exit(1)
