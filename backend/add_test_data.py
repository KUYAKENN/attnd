import mysql.connector
from datetime import datetime, date

try:
    conn = mysql.connector.connect(
        host='localhost', 
        user='root', 
        password='', 
        database='attendance_system'
    )
    cursor = conn.cursor()
    
    # Add some test attendance records for July 2025
    test_records = [
        (1, '2025-07-22 08:30:00', '2025-07-22 17:00:00', '2025-07-22', 'present', 8.5, 0.5),
        (2, '2025-07-22 09:00:00', '2025-07-22 17:30:00', '2025-07-22', 'present', 8.5, 0.5),
        (3, '2025-07-22 08:45:00', '2025-07-22 17:15:00', '2025-07-22', 'present', 8.5, 0.5),
        (1, '2025-07-21 08:15:00', '2025-07-21 16:45:00', '2025-07-21', 'present', 8.5, 0.5),
        (2, '2025-07-21 09:30:00', '2025-07-21 18:00:00', '2025-07-21', 'late', 8.5, 0.5),
        (3, '2025-07-21 08:30:00', '2025-07-21 17:00:00', '2025-07-21', 'present', 8.5, 0.5),
    ]
    
    for record in test_records:
        person_id, check_in, check_out, date_val, status, total_hours, overtime_hours = record
        
        # Check if record already exists
        cursor.execute('SELECT id FROM attendance_records WHERE person_id = %s AND date = %s', (person_id, date_val))
        existing = cursor.fetchone()
        if existing:
            print(f'Record already exists for person {person_id} on {date_val}')
            continue
            
        cursor.execute('''
            INSERT INTO attendance_records 
            (person_id, check_in_time, check_out_time, date, status, total_hours, overtime_hours, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (person_id, check_in, check_out, date_val, status, total_hours, overtime_hours, 'Main Office'))
        
        print(f'Added attendance record for person {person_id} on {date_val}')
    
    conn.commit()
    
    # Check the results
    cursor.execute('SELECT COUNT(*) FROM attendance_records')
    count = cursor.fetchone()[0]
    print(f'\nTotal attendance records: {count}')
    
    conn.close()
    print('Test data added successfully!')
    
except Exception as e:
    print(f'Error: {e}')
