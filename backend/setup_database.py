#!/usr/bin/env python3
"""
Database Setup and Test Script for Face Recognition Attendance System
This script will create the database and test the connection.
"""

import mysql.connector
import sys
import os

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # No password for root
}

DB_NAME = 'attendance_system'

def create_database():
    """Create the attendance_system database if it doesn't exist"""
    try:
        # Connect without specifying database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"✓ Database '{DB_NAME}' created or already exists")
        
        # Use the database
        cursor.execute(f"USE {DB_NAME}")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error creating database: {e}")
        return False

def setup_tables():
    """Create all required tables"""
    try:
        # Connect to the database
        config = DB_CONFIG.copy()
        config['database'] = DB_NAME
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Read and execute SQL file
        sql_file_path = os.path.join(os.path.dirname(__file__), 'database_setup.sql')
        
        if os.path.exists(sql_file_path):
            with open(sql_file_path, 'r', encoding='utf-8') as file:
                sql_commands = file.read()
                
            # Split commands and execute them
            commands = sql_commands.split(';')
            
            for command in commands:
                command = command.strip()
                if command and not command.startswith('--') and not command.startswith('/*'):
                    try:
                        cursor.execute(command)
                    except mysql.connector.Error as e:
                        if "already exists" not in str(e).lower():
                            print(f"Warning: {e}")
            
            conn.commit()
            print("✓ Database tables created successfully")
        else:
            print("❌ database_setup.sql file not found")
            return False
            
        cursor.close()
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error setting up tables: {e}")
        return False

def test_connection():
    """Test database connection and show sample data"""
    try:
        config = DB_CONFIG.copy()
        config['database'] = DB_NAME
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        print("\n🔍 Testing database connection...")
        
        # Test persons table
        cursor.execute("SELECT COUNT(*) as count FROM persons")
        person_count = cursor.fetchone()['count']
        print(f"✓ Persons table: {person_count} records")
        
        # Test face_encodings table
        cursor.execute("SELECT COUNT(*) as count FROM face_encodings")
        encoding_count = cursor.fetchone()['count']
        print(f"✓ Face encodings table: {encoding_count} records")
        
        # Test attendance table
        cursor.execute("SELECT COUNT(*) as count FROM attendance")
        attendance_count = cursor.fetchone()['count']
        print(f"✓ Attendance table: {attendance_count} records")
        
        # Test recognition_logs table
        cursor.execute("SELECT COUNT(*) as count FROM recognition_logs")
        log_count = cursor.fetchone()['count']
        print(f"✓ Recognition logs table: {log_count} records")
        
        # Show sample persons
        print("\n👥 Sample persons:")
        cursor.execute("SELECT id, name, department, status FROM persons LIMIT 3")
        persons = cursor.fetchall()
        for person in persons:
            print(f"  - ID: {person['id']}, Name: {person['name']}, Department: {person['department']}, Status: {person['status']}")
        
        cursor.close()
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Starting database setup for Face Recognition Attendance System...")
    print("=" * 60)
    
    # Check MySQL connection
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        conn.close()
        print("✓ MySQL connection successful")
    except mysql.connector.Error as e:
        print(f"❌ Cannot connect to MySQL: {e}")
        print("\nPlease ensure:")
        print("1. MySQL server is running")
        print("2. Root user has no password (or update the script)")
        print("3. MySQL connector is installed: pip install mysql-connector-python")
        sys.exit(1)
    
    # Create database
    if not create_database():
        sys.exit(1)
    
    # Setup tables
    if not setup_tables():
        sys.exit(1)
    
    # Test connection
    if not test_connection():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Database setup completed successfully!")
    print("\nYou can now start the Flask application:")
    print("  python app.py")
    print("\nDatabase details:")
    print(f"  Host: {DB_CONFIG['host']}")
    print(f"  User: {DB_CONFIG['user']}")
    print(f"  Database: {DB_NAME}")
    print("  Password: (none)")

if __name__ == "__main__":
    main()
