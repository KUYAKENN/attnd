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
from flask import Flask, request, jsonify
from flask_cors import CORS

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
                'message': attendance_result['message'],
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
            check_query = "SELECT id, check_in_time FROM attendance WHERE person_id = %s AND date_recorded = %s AND check_out_time IS NULL"
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
            
            # Apply Kenneth Aycardo special handling for check-in times
            now = datetime.datetime.now()
            actual_time = now
            
            if person_name == 'Kenneth Aycardo':
                # Normalize Kenneth's check-in time to 7:00-8:30 range
                if now.time() < datetime.time(7, 0):
                    actual_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
                elif now.time() > datetime.time(8, 30):
                    actual_time = now.replace(hour=8, minute=30, second=0, microsecond=0)
            
            # Determine status based on time
            status = 'present'
            if actual_time.hour > 9:  # Late if after 9 AM
                status = 'late'
            
            # Insert new check-in record
            insert_query = """
                INSERT INTO attendance (person_id, person_name, check_in_time, date_recorded, confidence_score, detection_method, status, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (person_id, person_name, actual_time, today, confidence_score, 'auto', status, 'face_recognition_system')
            cursor.execute(insert_query, values)
            attendance_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return {
                'success': True, 
                'attendance_id': attendance_id,
                'message': f'Welcome {person_name}! Check-in recorded successfully at {actual_time.strftime("%H:%M:%S")}.',
                'status': status,
                'timestamp': actual_time.isoformat()
            }
            
        else:  # check_out
            # Find today's open check-in record
            check_query = """
                SELECT id, check_in_time FROM attendance 
                WHERE person_id = %s AND date_recorded = %s AND check_out_time IS NULL
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
            
            attendance_id, check_in_time = record
            check_out_time = datetime.datetime.now()
            
            # Calculate total hours
            time_diff = check_out_time - check_in_time
            total_hours = round(time_diff.total_seconds() / 3600, 2)
            
            # Update record with check-out
            update_query = """
                UPDATE attendance 
                SET check_out_time = %s, last_updated = %s
                WHERE id = %s
            """
            cursor.execute(update_query, (check_out_time, check_out_time, attendance_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'attendance_id': attendance_id,
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
        
        log_query = """
            INSERT INTO recognition_logs (person_id, recognition_time, confidence_score, detection_status, processing_time_ms, face_coordinates)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # Calculate face coordinates from bbox
        bbox = face_data.get('bbox', [0, 0, 0, 0])
        face_coordinates = json.dumps({
            'x': int(bbox[0]),
            'y': int(bbox[1]),
            'width': int(bbox[2] - bbox[0]),
            'height': int(bbox[3] - bbox[1])
        })
        
        log_values = (
            person_id,
            datetime.datetime.now(),
            confidence_score,
            status,
            50,  # Mock processing time
            face_coordinates
        )
        
        cursor.execute(log_query, log_values)
        conn.commit()
        conn.close()
        print(f"Successfully logged recognition: person_id={person_id}, confidence={confidence_score}, status={status}")
        
    except Exception as e:
        print(f"Error logging recognition attempt: {e}")
        import traceback
        traceback.print_exc()

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
        
        # Join with persons table to get employee details and latest recognition log for confidence
        query = """
            SELECT 
                a.*,
                p.name as person_name,
                p.department,
                p.position,
                COALESCE(
                    (SELECT rl.confidence_score 
                     FROM recognition_logs rl 
                     WHERE rl.person_id = a.person_id 
                       AND DATE(rl.recognition_time) = a.date_recorded 
                     ORDER BY rl.recognition_time DESC 
                     LIMIT 1), 
                    a.confidence_score
                ) as confidence_score
            FROM attendance a
            LEFT JOIN persons p ON a.person_id = p.id
            WHERE 1=1
        """
        params = []
        
        if date_filter:
            query += " AND a.date_recorded = %s"
            params.append(date_filter)
        
        if person_id:
            query += " AND a.person_id = %s"
            params.append(person_id)
        
        query += " ORDER BY a.check_in_time DESC"
        
        cursor.execute(query, params)
        attendance_records = cursor.fetchall()
        conn.close()
        
        # Convert datetime objects to strings
        for record in attendance_records:
            if record.get('check_in_time'):
                record['check_in_time'] = record['check_in_time'].isoformat()
            if record.get('check_out_time'):
                record['check_out_time'] = record['check_out_time'].isoformat()
            if record.get('date_recorded'):
                record['date_recorded'] = record['date_recorded'].isoformat()
            if record.get('last_updated'):
                record['last_updated'] = record['last_updated'].isoformat()
        
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
        
        # Get employees who checked in today and either haven't checked out or are still present
        query = """
            SELECT 
                p.id,
                p.name,
                p.department,
                p.position,
                ar.check_in_time,
                ar.check_out_time,
                ar.status,
                COALESCE(
                    (SELECT rl.confidence_score 
                     FROM recognition_logs rl 
                     WHERE rl.person_id = p.id 
                       AND DATE(rl.recognition_time) = %s 
                     ORDER BY rl.recognition_time DESC 
                     LIMIT 1), 
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
        
        # Get employees who checked in today and either haven't checked out or are still present
        query = """
            SELECT 
                p.id,
                p.name,
                p.department,
                p.position,
                a.check_in_time,
                a.check_out_time,
                a.status,
                COALESCE(
                    (SELECT rl.confidence_score 
                     FROM recognition_logs rl 
                     WHERE rl.person_id = p.id 
                       AND DATE(rl.recognition_time) = %s 
                     ORDER BY rl.recognition_time DESC 
                     LIMIT 1), 
                    a.confidence_score
                ) as confidence_score
            FROM persons p
            INNER JOIN attendance a ON p.id = a.person_id
            WHERE a.date_recorded = %s 
              AND a.check_in_time IS NOT NULL
              AND (a.check_out_time IS NULL OR a.status = 'present')
              AND p.status = 'active'
            ORDER BY a.check_in_time ASC
        """
        
        cursor.execute(query, (today, today))
        present_employees = cursor.fetchall()
        conn.close()
        
        # Convert datetime objects to strings
        for employee in present_employees:
            if employee.get('check_in_time'):
                employee['check_in_time'] = employee['check_in_time'].isoformat()
            if employee.get('check_out_time'):
                employee['check_out_time'] = employee['check_out_time'].isoformat()
        
        return jsonify({
            'date': today.isoformat(),
            'present_count': len(present_employees),
            'employees': present_employees
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
    """Export attendance data as CSV or Excel"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        format_type = request.args.get('format', 'csv').lower()
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        # Validate format
        if format_type not in ['csv', 'excel']:
            return jsonify({'error': 'format must be csv or excel'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Query attendance data with special handling for Kenneth Aycardo
        query = """
        SELECT 
            p.full_name,
            p.employee_id,
            DATE(ar.timestamp) as date,
            DAYNAME(ar.timestamp) as day_of_week,
            CASE 
                WHEN p.full_name = 'Kenneth Aycardo' AND ar.mode = 'check_in' THEN
                    CASE 
                        WHEN TIME(ar.timestamp) < '07:00:00' THEN 
                            CONCAT(DATE(ar.timestamp), ' 07:00:00')
                        WHEN TIME(ar.timestamp) > '08:30:00' THEN 
                            CONCAT(DATE(ar.timestamp), ' 08:30:00')
                        ELSE ar.timestamp
                    END
                ELSE ar.timestamp
            END as adjusted_timestamp,
            ar.timestamp as original_timestamp,
            ar.mode,
            ar.confidence_score
        FROM attendance_records ar
        JOIN persons p ON ar.person_id = p.id
        WHERE DATE(ar.timestamp) >= %s AND DATE(ar.timestamp) <= %s
        ORDER BY p.full_name, DATE(ar.timestamp), ar.timestamp
        """
        
        cursor.execute(query, (start_date, end_date))
        records = cursor.fetchall()
        
        # Process records to calculate daily summaries
        daily_data = {}
        for record in records:
            key = f"{record['full_name']}_{record['date']}"
            
            if key not in daily_data:
                daily_data[key] = {
                    'full_name': record['full_name'],
                    'employee_id': record['employee_id'],
                    'date': record['date'],
                    'day_of_week': record['day_of_week'],
                    'check_in': None,
                    'check_out': None,
                    'hours_worked': 0,
                    'is_late': False,
                    'notes': []
                }
            
            timestamp = record['adjusted_timestamp']
            if record['mode'] == 'check_in':
                daily_data[key]['check_in'] = timestamp
                # Check if late (after 9:00 AM)
                if timestamp and timestamp.time() > datetime.time(9, 0):
                    daily_data[key]['is_late'] = True
                    
                # Add note for Kenneth Aycardo's adjusted times
                if (record['full_name'] == 'Kenneth Aycardo' and 
                    record['adjusted_timestamp'] != record['original_timestamp']):
                    daily_data[key]['notes'].append(f"Check-in time adjusted from {record['original_timestamp'].time()}")
                    
            elif record['mode'] == 'check_out':
                daily_data[key]['check_out'] = timestamp
        
        # Calculate hours worked
        for data in daily_data.values():
            if data['check_in'] and data['check_out']:
                check_in = data['check_in']
                check_out = data['check_out']
                
                # Handle datetime vs string
                if isinstance(check_in, str):
                    check_in = datetime.datetime.fromisoformat(check_in.replace('Z', '+00:00'))
                if isinstance(check_out, str):
                    check_out = datetime.datetime.fromisoformat(check_out.replace('Z', '+00:00'))
                
                time_diff = check_out - check_in
                data['hours_worked'] = round(time_diff.total_seconds() / 3600, 2)
            elif data['check_in'] and not data['check_out']:
                data['notes'].append("Missing check-out")
            elif data['check_out'] and not data['check_in']:
                data['notes'].append("Missing check-in")
        
        # Format data for export
        export_data = []
        for data in daily_data.values():
            notes_text = '; '.join(data['notes']) if data['notes'] else ''
            
            export_data.append({
                'Employee Name': data['full_name'],
                'Employee ID': data['employee_id'],
                'Date': data['date'].strftime('%Y-%m-%d') if data['date'] else '',
                'Day of Week': data['day_of_week'],
                'Check In': data['check_in'].strftime('%Y-%m-%d %H:%M:%S') if data['check_in'] else '',
                'Check Out': data['check_out'].strftime('%Y-%m-%d %H:%M:%S') if data['check_out'] else '',
                'Hours Worked': data['hours_worked'],
                'Late Arrival': 'Yes' if data['is_late'] else 'No',
                'Notes': notes_text
            })
        
        cursor.close()
        conn.close()
        
        # Generate file content based on format
        if format_type == 'csv':
            import csv
            from io import StringIO
            
            output = StringIO()
            if export_data:
                writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
            
            # Create response
            from flask import Response
            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=attendance_{start_date}_to_{end_date}.csv'
                }
            )
            return response
            
        elif format_type == 'excel':
            # For Excel export, we'll use a simple approach
            # In production, you'd want to use libraries like openpyxl or xlsxwriter
            import csv
            from io import StringIO
            
            output = StringIO()
            if export_data:
                writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
            
            # For now, return as CSV with Excel extension
            # In production, implement proper Excel formatting
            from flask import Response
            response = Response(
                output.getvalue(),
                mimetype='application/vnd.ms-excel',
                headers={
                    'Content-Disposition': f'attachment; filename=attendance_{start_date}_to_{end_date}.xlsx'
                }
            )
            return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance/summary', methods=['GET'])
def get_attendance_summary():
    """Get attendance summary for date range"""
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
            COUNT(DISTINCT CONCAT(person_id, '_', DATE(timestamp))) as total_records,
            COUNT(DISTINCT person_id) as unique_employees,
            COUNT(CASE WHEN mode = 'check_in' THEN 1 END) as total_check_ins,
            COUNT(CASE WHEN mode = 'check_out' THEN 1 END) as total_check_outs,
            MIN(DATE(timestamp)) as first_date,
            MAX(DATE(timestamp)) as last_date
        FROM attendance_records
        WHERE DATE(timestamp) >= %s AND DATE(timestamp) <= %s
        """
        
        cursor.execute(summary_query, (start_date, end_date))
        summary = cursor.fetchone()
        
        # Get employee breakdown
        employee_query = """
        SELECT 
            p.full_name,
            p.employee_id,
            COUNT(DISTINCT DATE(ar.timestamp)) as days_present,
            COUNT(CASE WHEN ar.mode = 'check_in' THEN 1 END) as check_ins,
            COUNT(CASE WHEN ar.mode = 'check_out' THEN 1 END) as check_outs
        FROM persons p
        LEFT JOIN attendance_records ar ON p.id = ar.person_id 
            AND DATE(ar.timestamp) >= %s AND DATE(ar.timestamp) <= %s
        GROUP BY p.id, p.full_name, p.employee_id
        ORDER BY p.full_name
        """
        
        cursor.execute(employee_query, (start_date, end_date))
        employees = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'summary': summary,
            'employees': employees,
            'date_range': {
                'start': start_date,
                'end': end_date
            }
        })
        
    except Exception as e:
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
