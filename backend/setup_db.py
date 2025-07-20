import mysql.connector
import sys

def setup_database():
    """Setup the complete database schema"""
    try:
        # Database configuration - connect without specifying database first
        config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',  # Update if you have a password
            'charset': 'utf8mb4'
        }
        
        print("Connecting to MySQL...")
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        print("✅ Connected to MySQL!")
        
        # Create database
        print("Creating database...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS attendance_system")
        cursor.execute("USE attendance_system")
        print("✅ Database 'attendance_system' ready!")
        
        # Create tables
        print("Creating tables...")
        
        # 1. Persons table
        cursor.execute("""
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
        )
        """)
        print("✅ Created 'persons' table")
        
        # 2. Face encodings table
        cursor.execute("""
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
        )
        """)
        print("✅ Created 'face_encodings' table")
        
        # 3. Attendance records table
        cursor.execute("""
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
        )
        """)
        print("✅ Created 'attendance_records' table")
        
        # 4. Recognition logs table
        cursor.execute("""
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
        )
        """)
        print("✅ Created 'recognition_logs' table")
        
        # Insert test data
        print("Inserting test data...")
        cursor.execute("""
        INSERT IGNORE INTO persons (name, email, phone, department, position, status, notes) VALUES
        ('Test User', 'test@example.com', '1234567890', 'IT', 'Developer', 'active', 'Test user for system verification')
        """)
        
        conn.commit()
        print("✅ Test data inserted!")
        
        # Verify setup
        print("\nVerifying setup...")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Created tables: {[table[0] for table in tables]}")
        
        cursor.execute("SELECT COUNT(*) FROM persons")
        count = cursor.fetchone()[0]
        print(f"Persons table contains: {count} records")
        
        cursor.execute("SELECT id, name, email, department FROM persons")
        persons = cursor.fetchall()
        for person in persons:
            print(f"  - ID: {person[0]}, Name: {person[1]}, Email: {person[2]}, Dept: {person[3]}")
        
        conn.close()
        print("\n🎉 Database setup completed successfully!")
        print("You can now test the registration system!")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ General Error: {e}")
        return False

if __name__ == "__main__":
    setup_database()
