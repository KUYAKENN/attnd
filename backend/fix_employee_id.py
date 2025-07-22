import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost', 
        user='root', 
        password='', 
        database='attendance_system'
    )
    cursor = conn.cursor()
    
    # Update existing persons with employee_id values
    cursor.execute('UPDATE persons SET employee_id = CONCAT("EMP", LPAD(id, 3, "0"))')
    conn.commit()
    
    print(f'Updated {cursor.rowcount} records with employee_id')
    
    # Check the results
    cursor.execute('SELECT id, employee_id, name FROM persons')
    results = cursor.fetchall()
    print('Current persons:')
    for row in results:
        print(f'ID: {row[0]}, Employee ID: {row[1]}, Name: {row[2]}')
    
    conn.close()
    print('Database update completed successfully!')
    
except Exception as e:
    print(f'Error: {e}')
