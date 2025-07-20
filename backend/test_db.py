import mysql.connector
import sys

def test_database_connection():
    """Test database connection and setup"""
    try:
        # Database configuration
        config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',  # Update if you have a password
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
        
        print("Testing MySQL connection...")
        
        # Test basic connection
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        print("✅ MySQL connection successful!")
        
        # Check if database exists
        cursor.execute("SHOW DATABASES LIKE 'attendance_system'")
        db_exists = cursor.fetchone()
        
        if not db_exists:
            print("❌ Database 'attendance_system' does not exist!")
            print("Creating database...")
            cursor.execute("CREATE DATABASE attendance_system")
            print("✅ Database 'attendance_system' created!")
        else:
            print("✅ Database 'attendance_system' exists!")
        
        # Switch to attendance_system database
        cursor.execute("USE attendance_system")
        
        # Check tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        required_tables = ['persons', 'face_encodings', 'attendance_records', 'recognition_logs']
        existing_tables = [table[0] for table in tables]
        
        print(f"\nExisting tables: {existing_tables}")
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            print("Please run the setup_database.sql script!")
        else:
            print("✅ All required tables exist!")
        
        # Test insert/select
        try:
            cursor.execute("SELECT COUNT(*) FROM persons")
            count = cursor.fetchone()[0]
            print(f"✅ Persons table accessible, contains {count} records")
        except Exception as e:
            print(f"❌ Error accessing persons table: {e}")
        
        conn.close()
        print("\n🎉 Database test completed!")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure MySQL/XAMPP is running")
        print("2. Check if username/password is correct")
        print("3. Verify MySQL is running on port 3306")
        return False
    except Exception as e:
        print(f"❌ General Error: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()
