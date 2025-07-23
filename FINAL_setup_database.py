#!/usr/bin/env python3
"""
🚀 FINAL DATABASE SETUP SCRIPT
Face Recognition Attendance System
This script will setup your complete database with ONE command
"""

import mysql.connector
import sys
import os
from datetime import datetime

# ===================================================================
# DATABASE CONFIGURATION
# ===================================================================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Change if you have a password
}

print("=" * 70)
print("🎯 FINAL DATABASE SETUP - FACE RECOGNITION ATTENDANCE SYSTEM")
print("=" * 70)

def setup_complete_database():
    """Setup the entire database from the FINAL SQL file"""
    try:
        print("🔌 Connecting to MySQL...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("📄 Reading FINAL setup script...")
        sql_file = 'FINAL_setup_database.sql'
        
        if not os.path.exists(sql_file):
            print(f"❌ ERROR: {sql_file} not found in current directory!")
            print("   Make sure both this Python script and the SQL file are in the same folder.")
            return False
            
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        print("⚡ Executing FINAL database setup...")
        print("   This will drop existing database and create everything fresh...")
        
        # Execute the complete script
        results = cursor.execute(sql_script, multi=True)
        
        # Process all results
        for result in results:
            if result.with_rows:
                try:
                    rows = result.fetchall()
                    if rows:
                        for row in rows:
                            if isinstance(row, tuple) and len(row) > 0:
                                print(f"   ✓ {' | '.join(str(x) for x in row)}")
                except:
                    pass
        
        conn.commit()
        print("\n🎉 DATABASE SETUP COMPLETED SUCCESSFULLY!")
        
        cursor.close()
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Script Error: {e}")
        return False

def test_database_connection():
    """Test the database and show summary"""
    try:
        print("\n🔍 TESTING DATABASE CONNECTION...")
        
        config = DB_CONFIG.copy()
        config['database'] = 'attendance_system'
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # Test basic connection
        cursor.execute("SELECT DATABASE() as current_db")
        db_info = cursor.fetchone()
        print(f"   ✅ Connected to database: {db_info['current_db']}")
        
        # Count tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"   ✅ Created {len(tables)} tables")
        
        # Count sample data
        test_queries = [
            ("Users", "SELECT COUNT(*) as count FROM users"),
            ("Persons", "SELECT COUNT(*) as count FROM persons"),
            ("Departments", "SELECT COUNT(*) as count FROM departments"),
            ("System Settings", "SELECT COUNT(*) as count FROM system_settings"),
            ("Holidays", "SELECT COUNT(*) as count FROM holidays"),
            ("Work Schedules", "SELECT COUNT(*) as count FROM work_schedules"),
            ("Attendance Records", "SELECT COUNT(*) as count FROM attendance_records")
        ]
        
        for name, query in test_queries:
            cursor.execute(query)
            result = cursor.fetchone()
            print(f"   ✅ {name}: {result['count']} records")
        
        # Show sample employees
        print("\n👥 SAMPLE EMPLOYEES:")
        cursor.execute("SELECT employee_id, name, department, position FROM persons WHERE status = 'active'")
        employees = cursor.fetchall()
        for emp in employees:
            print(f"   • {emp['employee_id']}: {emp['name']} - {emp['position']} ({emp['department']})")
        
        cursor.close()
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Test Failed: {e}")
        return False

def main():
    """Main execution function"""
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check MySQL connection first
    try:
        print("🔧 Checking MySQL connection...")
        conn = mysql.connector.connect(**DB_CONFIG)
        conn.close()
        print("   ✅ MySQL connection successful")
    except mysql.connector.Error as e:
        print(f"❌ Cannot connect to MySQL: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("   1. Make sure MySQL/MariaDB is running")
        print("   2. Check username/password in script")
        print("   3. Install: pip install mysql-connector-python")
        print("   4. Try: mysql -u root -p (to test manually)")
        return False
    
    # Setup database
    if not setup_complete_database():
        print("\n❌ SETUP FAILED!")
        return False
    
    # Test database
    if not test_database_connection():
        print("\n❌ DATABASE TEST FAILED!")
        return False
    
    # Success message
    print("\n" + "=" * 70)
    print("🎉 FINAL DATABASE SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("📋 QUICK START GUIDE:")
    print("   • Database: attendance_system")
    print("   • Admin Login: admin / admin123")
    print("   • Web Interface: Run your Flask app now!")
    print("   • API Ready: All endpoints should work")
    print("   • Sample Data: 4 employees with test records")
    print("=" * 70)
    print(f"✅ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 You can now start your Flask application!")
        sys.exit(0)
    else:
        print("\n💥 Setup failed. Check the errors above.")
        sys.exit(1)
