import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost', 
        user='root', 
        password='', 
        database='attendance_system'
    )
    cursor = conn.cursor()
    
    # Add missing columns to attendance_records table
    missing_columns = [
        "ADD COLUMN overtime_hours DECIMAL(5,2) DEFAULT 0.00 AFTER total_hours",
        "ADD COLUMN location VARCHAR(100) DEFAULT 'Main Office' AFTER overtime_hours",
        "ADD COLUMN ip_address VARCHAR(45) AFTER location",
        "ADD COLUMN created_by INT AFTER updated_at"
    ]
    
    for column_sql in missing_columns:
        try:
            full_sql = f"ALTER TABLE attendance_records {column_sql}"
            cursor.execute(full_sql)
            print(f"Added column: {column_sql}")
        except mysql.connector.Error as e:
            print(f"Column might already exist or error: {e}")
    
    conn.commit()
    
    # Check the updated structure
    cursor.execute('DESCRIBE attendance_records')
    results = cursor.fetchall()
    print('\nUpdated attendance_records structure:')
    for row in results:
        print(f'{row[0]}: {row[1]}')
    
    conn.close()
    print('\nDatabase update completed successfully!')
    
except Exception as e:
    print(f'Error: {e}')
