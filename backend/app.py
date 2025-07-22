# Flask Backend API for Face Recognition Attendance System with ArcFace
import os
import cv2
import numpy as np
import json
import base64
import datetime
from io import BytesIO
from PIL import Image
import mysql.connector
from sklearn.metrics.pairwise import cosine_similarity
import insightface
from insightface.app import FaceAnalysis
from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
import pandas as pd
from io import BytesIO
import xlsxwriter

app = Flask(__name__)
CORS(app)

# Initialize ArcFace model
face_app = FaceAnalysis(allowed_modules=['detection', 'recognition'])
face_app.prepare(ctx_id=0, det_size=(640, 640))

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Update this if you have a password
    'database': 'attendance_system',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def get_db_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

def decode_base64_image(base64_string):
    """Decode base64 image to OpenCV format"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Convert to PIL Image
        pil_image = Image.open(BytesIO(image_data))
        
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        return cv_image
    except Exception as e:
        print(f"Error decoding image: {e}")
        return None

def extract_face_encoding(image):
    """Extract face encoding using ArcFace"""
    try:
        faces = face_app.get(image)
        
        if len(faces) == 0:
            return None, "No face detected"
        
        if len(faces) > 1:
            return None, "Multiple faces detected. Please ensure only one face is visible."
        
        face = faces[0]
        
        # Get face embedding (512-dimensional vector)
        embedding = face.embedding
        
        # Check if embedding is valid
        if embedding is None:
            return None, "Failed to extract face features. Please try with better lighting."
        
        # Get face bounding box and landmarks for validation
        bbox = face.bbox
        landmarks = face.landmark_2d_106
        
        # Validate bbox and landmarks
        if bbox is None:
            return None, "Failed to detect face boundaries."
        
        if landmarks is None:
            landmarks = []  # Set empty list if landmarks not available
        
        # Calculate face quality score based on size and position
        face_width = bbox[2] - bbox[0]
        face_height = bbox[3] - bbox[1]
        face_area = face_width * face_height
        image_area = image.shape[0] * image.shape[1]
        face_ratio = face_area / image_area
        
        # Quality checks
        if face_ratio < 0.05:  # Face too small
            return None, "Face too small. Please move closer to the camera."
        
        if face_width < 100 or face_height < 100:  # Face resolution too low
            return None, "Face resolution too low. Please ensure good lighting."
        
        return {
            'embedding': embedding.tolist(),
            'bbox': bbox.tolist(),
            'landmarks': landmarks.tolist() if len(landmarks) > 0 else [],
            'confidence': float(face.det_score) if hasattr(face, 'det_score') and face.det_score is not None else 0.0,
            'face_area': face_area,
            'quality_score': min(1.0, face_ratio * 10)  # Normalize quality score
        }, None
        
    except Exception as e:
        print(f"Error extracting face encoding: {e}")
        return None, f"Error processing face: {str(e)}"

def find_matching_person(target_embedding, threshold=0.6):
    """Find matching person in database using cosine similarity"""
    try:
        conn = get_db_connection()
        if not conn:
            return None, 0.0
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fe.person_id, fe.encoding_data, p.name, p.status 
            FROM face_encodings fe
            JOIN persons p ON fe.person_id = p.id
            WHERE fe.is_primary = true AND p.status = 'active'
        """)
        
        encodings = cursor.fetchall()
        conn.close()
        
        if not encodings:
            return None, 0.0
        
        best_match_id = None
        best_similarity = 0.0
        best_person_name = None
        
        target_embedding = np.array(target_embedding).reshape(1, -1)
        
        for person_id, encoding_data, person_name, status in encodings:
            try:
                stored_embedding = np.array(json.loads(encoding_data)).reshape(1, -1)
                similarity = cosine_similarity(target_embedding, stored_embedding)[0][0]
                
                if similarity > best_similarity and similarity >= threshold:
                    best_similarity = similarity
                    best_match_id = person_id
                    best_person_name = person_name
                    
            except Exception as e:
                print(f"Error comparing embedding for person {person_id}: {e}")
                continue
        
        return (best_match_id, best_person_name) if best_match_id else (None, None), best_similarity
        
    except Exception as e:
        print(f"Error finding matching person: {e}")
        return None, 0.0

def record_attendance(person_id, person_name, confidence_score, face_data, mode='check_in'):
    """Record attendance in database with proper validation"""
    try:
        conn = get_db_connection()
        if not conn:
            return {'success': False, 'error': 'Database connection failed'}
        
        cursor = conn.cursor()
        today = datetime.date.today()
        
        if mode == 'check_in':
            # Check if already checked in today
            check_query = "SELECT id, check_in_time FROM attendance_records WHERE person_id = %s AND date = %s AND check_in_time IS NOT NULL AND check_out_time IS NULL"
            cursor.execute(check_query, (person_id, today))
            existing = cursor.fetchone()
            
            if existing:
                conn.close()
                print(f"Person {person_name} already checked in today")
                return {
                    'success': False, 
                    'error': 'already_checked_in',
                    'message': f'{person_name}, you have already checked in today. Your check-in time was {existing[1].strftime("%H:%M:%S")}.'
                }
            
            # Record actual check-in time
            actual_time = datetime.datetime.now()
            
            # Insert new check-in record
            insert_query = """
                INSERT INTO attendance_records (person_id, check_in_time, date, check_in_method, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (person_id, actual_time, today, 'face_recognition', 'present')
            cursor.execute(insert_query, values)
            attendance_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return {
                'success': True, 
                'attendance_id': attendance_id,
                'message': f'Welcome {person_name}! Check-in recorded successfully at {actual_time.strftime("%H:%M:%S")}.',
                'timestamp': actual_time.isoformat()
            }
            
        else:  # check_out
            # Find today's open check-in record
            check_query = """
                SELECT id, check_in_time FROM attendance_records 
                WHERE person_id = %s AND date = %s AND check_in_time IS NOT NULL AND check_out_time IS NULL
                ORDER BY check_in_time DESC LIMIT 1
            """
            cursor.execute(check_query, (person_id, today))
            record = cursor.fetchone()
            
            if not record:
                conn.close()
                print(f"No valid check-in found for {person_name} today")
                return {
                    'success': False,
                    'error': 'no_checkin',
                    'message': f'{person_name}, you did not check in today or you have already checked out. Unable to process check-out.'
                }
            
            check_in_id, check_in_time = record
            check_out_time = datetime.datetime.now()
            
            # Calculate total hours
            time_diff = check_out_time - check_in_time
            total_hours = round(time_diff.total_seconds() / 3600, 2)
            
            # Update the record with check-out time
            update_query = """
                UPDATE attendance_records 
                SET check_out_time = %s, check_out_method = %s, total_hours = %s
                WHERE id = %s
            """
            values = (check_out_time, 'face_recognition', total_hours, check_in_id)
            cursor.execute(update_query, values)
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'attendance_id': check_in_id,
                'message': f'Goodbye {person_name}! Check-out recorded successfully at {check_out_time.strftime("%H:%M:%S")}. Total hours worked: {total_hours}.',
                'total_hours': total_hours,
                'timestamp': check_out_time.isoformat()
            }
        
    except Exception as e:
        print(f"Error recording attendance: {e}")
        return {'success': False, 'error': str(e)}

def log_recognition_attempt(person_id, confidence_score, status, face_data):
    """Log recognition attempt for monitoring"""
    try:
        conn = get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        # Map status to success boolean and recognition type
        success = 1 if status in ['recognized', 'validation_failed'] else 0
        recognition_type = 'verification'  # Default type
        error_message = None
        
        if status == 'validation_failed':
            error_message = 'Attendance validation failed'
        elif status == 'unknown':
            error_message = 'Face not recognized'
        
        log_query = """
            INSERT INTO recognition_logs (person_id, recognition_time, confidence_score, recognition_type, success, error_message)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        log_values = (
            person_id,
            datetime.datetime.now(),
            confidence_score,
            recognition_type,
            success,
            error_message
        )
        
        cursor.execute(log_query, log_values)
        conn.commit()
        conn.close()
        print(f"Successfully logged recognition: person_id={person_id}, confidence={confidence_score}, status={status}")
        
    except Exception as e:
        print(f"Error logging recognition attempt: {e}")

# API Routes

@app.route('/api/persons', methods=['GET'])
def get_persons():
    """Get all registered persons"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM persons ORDER BY registration_date DESC")
        persons = cursor.fetchall()
        conn.close()
        
        # Convert datetime objects to strings
        for person in persons:
            if person.get('registration_date'):
                person['registration_date'] = person['registration_date'].isoformat()
            if person.get('last_updated'):
                person['last_updated'] = person['last_updated'].isoformat()
        
        return jsonify(persons)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/persons', methods=['POST'])
def create_person():
    """Create a new person with face encoding"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        
        if not data.get('face_image'):
            return jsonify({'error': 'Face image is required'}), 400
        
        # Decode and process face image
        cv_image = decode_base64_image(data['face_image'])
        if cv_image is None:
            return jsonify({'error': 'Invalid image format'}), 400
        
        # Extract face encoding
        face_data, error = extract_face_encoding(cv_image)
        if error:
            return jsonify({'error': error}), 400
        
        # Save to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Insert person
        person_query = """
            INSERT INTO persons (name, email, phone, department, position, status, registration_date, last_updated, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        person_values = (
            data.get('name'),
            data.get('email'),
            data.get('phone'),
            data.get('department'),
            data.get('position'),
            data.get('status', 'active'),
            datetime.datetime.now(),
            datetime.datetime.now(),
            data.get('notes', '')
        )
        
        cursor.execute(person_query, person_values)
        person_id = cursor.lastrowid
        
        # Insert face encoding
        encoding_query = """
            INSERT INTO face_encodings (person_id, encoding_data, encoding_type, face_angle, confidence_score, created_date, is_primary)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        encoding_values = (
            person_id,
            json.dumps(face_data['embedding']),
            'arcface',
            'front',
            face_data['confidence'],
            datetime.datetime.now(),
            True
        )
        
        cursor.execute(encoding_query, encoding_values)
        conn.commit()
        conn.close()
        
        return jsonify({
            'id': person_id,
            'name': data.get('name'),
            'status': 'success',
            'message': 'Person registered successfully',
            'face_quality': face_data['quality_score']
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/face-detection', methods=['POST'])
def detect_face():
    """Simple face detection endpoint"""
    try:
        data = request.json
        
        if not data.get('image'):
            return jsonify({'face_detected': False, 'error': 'No image provided'}), 400
        
        # Decode image
        cv_image = decode_base64_image(data['image'])
        if cv_image is None:
            return jsonify({'face_detected': False, 'error': 'Invalid image format'}), 400
        
        # Use ArcFace to detect faces
        faces = face_app.get(cv_image)
        
        face_detected = len(faces) > 0
        face_count = len(faces)
        
        response = {
            'face_detected': face_detected,
            'face_count': face_count
        }
        
        if face_detected:
            # Get face details for the first face
            face = faces[0]
            bbox = face.bbox
            
            response.update({
                'face_area': {
                    'x': int(bbox[0]),
                    'y': int(bbox[1]),
                    'width': int(bbox[2] - bbox[0]),
                    'height': int(bbox[3] - bbox[1])
                },
                'confidence': float(face.det_score)
            })
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in face detection: {e}")
        return jsonify({'face_detected': False, 'error': str(e)}), 500

@app.route('/api/face-recognition', methods=['POST'])
def recognize_face():
    """Recognize face and record attendance with proper validation"""
    try:
        data = request.json
        
        if not data.get('image'):
            return jsonify({'error': 'Image is required'}), 400
        
        # Get attendance mode (default to check_in)
        attendance_mode = data.get('mode', 'check_in')
        
        # Decode image
        cv_image = decode_base64_image(data['image'])
        if cv_image is None:
            return jsonify({'error': 'Invalid image format'}), 400
        
        # Extract face encoding
        face_data, error = extract_face_encoding(cv_image)
        if error:
            return jsonify({'error': error, 'recognized': False}), 400
        
        # Find matching person
        match_result, similarity = find_matching_person(face_data['embedding'])
        
        if match_result is None:
            # Log unrecognized face attempt
            log_recognition_attempt(None, similarity, 'unknown', face_data)
            return jsonify({
                'recognized': False,
                'message': 'Face not recognized. Please register first.',
                'similarity': float(similarity),
                'success': False
            })
        
        person_id, person_name = match_result
        
        # Record attendance with validation
        attendance_result = record_attendance(person_id, person_name, similarity, face_data, attendance_mode)
        
        # Log recognition attempt
        status = 'recognized' if attendance_result['success'] else 'validation_failed'
        log_recognition_attempt(person_id, similarity, status, face_data)
        
        if not attendance_result['success']:
            # Attendance validation failed
            return jsonify({
                'recognized': True,
                'person_id': person_id,
                'person_name': person_name,
                'similarity': float(similarity),
                'success': False,
                'error': attendance_result.get('error'),
                'message': attendance_result.get('message', 'Attendance validation failed'),
                'mode': attendance_mode,
                'timestamp': datetime.datetime.now().isoformat()
            })
        
        # Successful attendance recording
        return jsonify({
            'recognized': True,
            'person_id': person_id,
            'person_name': person_name,
            'similarity': float(similarity),
            'success': True,
            'attendance_id': attendance_result.get('attendance_id'),
            'mode': attendance_mode,
            'message': attendance_result['message'],
            'timestamp': attendance_result.get('timestamp', datetime.datetime.now().isoformat()),
            'total_hours': attendance_result.get('total_hours'),
            'status': attendance_result.get('status')
        })
        
    except Exception as e:
        print(f"Error in face recognition: {e}")
        return jsonify({'error': str(e), 'recognized': False, 'success': False}), 500

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    """Get attendance records"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Get query parameters
        date_filter = request.args.get('date')
        person_id = request.args.get('person_id')
        
        # Join with persons table to get employee details
        query = """
            SELECT 
                ar.*,
                p.name as person_name,
                p.department,
                p.position
            FROM attendance_records ar
            LEFT JOIN persons p ON ar.person_id = p.id
            WHERE 1=1
        """
        params = []
        
        if date_filter:
            query += " AND ar.date = %s"
            params.append(date_filter)
        
        if person_id:
            query += " AND ar.person_id = %s"
            params.append(person_id)
        
        query += " ORDER BY ar.check_in_time DESC"
        
        cursor.execute(query, params)
        attendance_records = cursor.fetchall()
        conn.close()
        
        # Convert datetime objects to strings
        for record in attendance_records:
            if record.get('check_in_time'):
                record['check_in_time'] = record['check_in_time'].isoformat()
            if record.get('check_out_time'):
                record['check_out_time'] = record['check_out_time'].isoformat()
            if record.get('date'):
                record['date'] = record['date'].isoformat()
            if record.get('created_at'):
                record['created_at'] = record['created_at'].isoformat()
            if record.get('updated_at'):
                record['updated_at'] = record['updated_at'].isoformat()
        
        return jsonify(attendance_records)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance/present-today', methods=['GET'])
def get_present_today():
    """Get list of employees present today"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Get today's date
        today = datetime.date.today()
        
        # Get employees who checked in today and haven't checked out yet
        query = """
            SELECT DISTINCT
                p.id,
                p.name,
                p.department,
                p.position,
                ar.check_in_time,
                ar.check_out_time,
                ar.total_hours
            FROM persons p
            INNER JOIN attendance_records ar ON p.id = ar.person_id
            WHERE ar.date = %s 
              AND ar.check_in_time IS NOT NULL
              AND p.status = 'active'
            ORDER BY ar.check_in_time ASC
        """
        
        cursor.execute(query, (today,))
        present_employees = cursor.fetchall()
        conn.close()
        
        # Convert datetime objects to strings and filter currently present
        currently_present = []
        for employee in present_employees:
            if employee.get('check_in_time'):
                employee['check_in_time'] = employee['check_in_time'].isoformat()
            if employee.get('check_out_time'):
                employee['check_out_time'] = employee['check_out_time'].isoformat()
            
            # Only include employees who haven't checked out yet (check_out_time is NULL)
            if not employee.get('check_out_time'):
                currently_present.append(employee)
        
        return jsonify({
            'date': today.isoformat(),
            'present_count': len(currently_present),
            'employees': currently_present
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recognition-logs', methods=['GET'])
def get_recognition_logs():
    """Get recent recognition attempts for monitoring"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT rl.*, p.name as person_name
            FROM recognition_logs rl
            LEFT JOIN persons p ON rl.person_id = p.id
            ORDER BY rl.recognition_time DESC
            LIMIT 100
        """)
        
        logs = cursor.fetchall()
        conn.close()
        
        # Convert datetime objects to strings
        for log in logs:
            if log.get('recognition_time'):
                log['recognition_time'] = log['recognition_time'].isoformat()
        
        return jsonify(logs)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance/export', methods=['GET'])
def export_attendance():
    """Export attendance records to CSV or Excel"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        format_type = request.args.get('format', 'csv').lower()
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Query attendance data with employee details
        query = """
            SELECT 
                p.employee_id,
                p.name as employee_name,
                p.department,
                p.position,
                ar.date,
                ar.check_in_time,
                ar.check_out_time,
                ar.total_hours,
                ar.overtime_hours,
                ar.status,
                ar.check_in_method,
                ar.check_out_method,
                ar.location,
                ar.notes
            FROM attendance_records ar
            JOIN persons p ON ar.person_id = p.id
            WHERE ar.date BETWEEN %s AND %s
            AND p.status = 'active'
            ORDER BY ar.date DESC, p.name ASC
        """
        
        # Execute query and get data
        df = pd.read_sql(query, conn, params=[start_date, end_date])
        conn.close()
        
        if df.empty:
            return jsonify({'error': 'No attendance records found for the specified date range'}), 404
        
        # Format datetime columns
        df['check_in_time'] = pd.to_datetime(df['check_in_time']).dt.strftime('%H:%M:%S')
        df['check_out_time'] = pd.to_datetime(df['check_out_time']).dt.strftime('%H:%M:%S')
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        # Replace NaN values
        df = df.fillna('')
        
        if format_type == 'excel':
            # Create Excel file
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Write main data
                df.to_excel(writer, sheet_name='Attendance Records', index=False)
                
                # Create summary sheet
                summary_data = []
                for employee in df['employee_name'].unique():
                    emp_data = df[df['employee_name'] == employee]
                    total_days = len(emp_data)
                    total_hours = emp_data['total_hours'].astype(float).sum()
                    avg_hours = total_hours / total_days if total_days > 0 else 0
                    late_days = len(emp_data[emp_data['status'] == 'late'])
                    
                    summary_data.append({
                        'Employee': employee,
                        'Department': emp_data['department'].iloc[0],
                        'Total Days': total_days,
                        'Total Hours': round(total_hours, 2),
                        'Average Hours': round(avg_hours, 2),
                        'Late Days': late_days,
                        'Attendance Rate': f"{((total_days - late_days) / total_days * 100):.1f}%" if total_days > 0 else "0%"
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Format the Excel file
                workbook = writer.book
                worksheet = writer.sheets['Attendance Records']
                
                # Add header formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Auto-adjust column widths
                for i, col in enumerate(df.columns):
                    max_length = max(df[col].astype(str).str.len().max(), len(col))
                    worksheet.set_column(i, i, min(max_length + 2, 50))
            
            output.seek(0)
            filename = f"attendance_{start_date}_to_{end_date}.xlsx"
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        
        else:  # CSV format
            output = BytesIO()
            df.to_csv(output, index=False, encoding='utf-8')
            output.seek(0)
            filename = f"attendance_{start_date}_to_{end_date}.csv"
            
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
            
    except Exception as e:
        print(f"Error exporting attendance: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance/summary', methods=['GET'])
def get_attendance_summary():
    """Get attendance summary statistics for a date range"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Get summary statistics
        summary_query = """
            SELECT 
                COUNT(DISTINCT ar.person_id) as total_employees,
                COUNT(ar.id) as total_attendance_records,
                AVG(ar.total_hours) as avg_daily_hours,
                SUM(ar.total_hours) as total_hours_worked,
                SUM(ar.overtime_hours) as total_overtime_hours,
                COUNT(CASE WHEN ar.status = 'late' THEN 1 END) as late_instances,
                COUNT(CASE WHEN ar.status = 'early_leave' THEN 1 END) as early_leave_instances
            FROM attendance_records ar
            JOIN persons p ON ar.person_id = p.id
            WHERE ar.date BETWEEN %s AND %s
            AND p.status = 'active'
        """
        
        cursor.execute(summary_query, [start_date, end_date])
        summary = cursor.fetchone()
        
        # Get employee-wise statistics
        employee_query = """
            SELECT 
                p.employee_id,
                p.name,
                p.department,
                COUNT(ar.id) as days_present,
                AVG(ar.total_hours) as avg_hours,
                SUM(ar.total_hours) as total_hours,
                SUM(ar.overtime_hours) as overtime_hours,
                COUNT(CASE WHEN ar.status = 'late' THEN 1 END) as late_days
            FROM persons p
            LEFT JOIN attendance_records ar ON p.id = ar.person_id 
                AND ar.date BETWEEN %s AND %s
            WHERE p.status = 'active'
            GROUP BY p.id, p.employee_id, p.name, p.department
            ORDER BY p.name
        """
        
        cursor.execute(employee_query, [start_date, end_date])
        employees = cursor.fetchall()
        conn.close()
        
        # Format the results
        for employee in employees:
            if employee['avg_hours']:
                employee['avg_hours'] = round(float(employee['avg_hours']), 2)
            if employee['total_hours']:
                employee['total_hours'] = round(float(employee['total_hours']), 2)
            if employee['overtime_hours']:
                employee['overtime_hours'] = round(float(employee['overtime_hours']), 2)
        
        return jsonify({
            'summary': {
                'total_employees': summary['total_employees'],
                'total_attendance_records': summary['total_attendance_records'],
                'avg_daily_hours': round(float(summary['avg_daily_hours']) if summary['avg_daily_hours'] else 0, 2),
                'total_hours_worked': round(float(summary['total_hours_worked']) if summary['total_hours_worked'] else 0, 2),
                'total_overtime_hours': round(float(summary['total_overtime_hours']) if summary['total_overtime_hours'] else 0, 2),
                'late_instances': summary['late_instances'],
                'early_leave_instances': summary['early_leave_instances']
            },
            'employees': employees,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        print(f"Error getting attendance summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'arcface_loaded': face_app is not None
    })

if __name__ == '__main__':
    print("Starting Face Recognition Attendance System...")
    print("ArcFace model loaded and ready!")
    app.run(debug=True, host='0.0.0.0', port=5000)
