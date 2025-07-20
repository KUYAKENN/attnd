# Simplified Flask Backend for Face Recognition Attendance System
# This version uses basic face detection without ArcFace to avoid compatibility issues

import os
import cv2
import numpy as np
import json
import base64
import datetime
from io import BytesIO
from PIL import Image
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',  # Change this to your MySQL password
    'database': 'attendance_system'
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

def extract_face_features(image):
    """Extract basic face features using OpenCV for demo purposes"""
    try:
        # Load OpenCV face cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return None, "No face detected"
        
        if len(faces) > 1:
            return None, "Multiple faces detected. Please ensure only one face is visible."
        
        # Get the largest face
        x, y, w, h = faces[0]
        
        # Extract face region
        face_roi = gray[y:y+h, x:x+w]
        
        # Resize to standard size
        face_roi = cv2.resize(face_roi, (128, 128))
        
        # Create a simple feature vector (histogram)
        features = cv2.calcHist([face_roi], [0], None, [256], [0, 256])
        features = features.flatten()
        
        # Normalize features
        features = features / np.linalg.norm(features)
        
        return {
            'features': features.tolist(),
            'bbox': [int(x), int(y), int(w), int(h)],
            'confidence': 0.8,  # Mock confidence
            'face_area': w * h,
            'quality_score': min(1.0, (w * h) / (image.shape[0] * image.shape[1]) * 10)
        }, None
        
    except Exception as e:
        print(f"Error extracting face features: {e}")
        return None, f"Error processing face: {str(e)}"

def find_matching_person(target_features, threshold=0.8):
    """Find matching person using simple correlation"""
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
        
        target_features = np.array(target_features)
        
        for person_id, encoding_data, person_name, status in encodings:
            try:
                stored_features = np.array(json.loads(encoding_data))
                
                # Calculate correlation coefficient
                correlation = np.corrcoef(target_features, stored_features)[0, 1]
                
                # Handle NaN values
                if np.isnan(correlation):
                    correlation = 0.0
                
                # Convert to positive similarity score
                similarity = (correlation + 1) / 2  # Convert from [-1,1] to [0,1]
                
                if similarity > best_similarity and similarity >= threshold:
                    best_similarity = similarity
                    best_match_id = person_id
                    best_person_name = person_name
                    
            except Exception as e:
                print(f"Error comparing features for person {person_id}: {e}")
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
        
        # Extract face features
        face_data, error = extract_face_features(cv_image)
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
            json.dumps(face_data['features']),
            'opencv_histogram',
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

@app.route('/api/face-recognition', methods=['POST'])
def recognize_face():
    """Recognize face and record attendance automatically"""
    try:
        data = request.json
        
        if not data.get('image'):
            return jsonify({'error': 'Image is required'}), 400
        
        # Decode image
        cv_image = decode_base64_image(data['image'])
        if cv_image is None:
            return jsonify({'error': 'Invalid image format'}), 400
        
        # Extract face features
        face_data, error = extract_face_features(cv_image)
        if error:
            return jsonify({'error': error, 'recognized': False}), 400
        
        # Find matching person
        match_result, similarity = find_matching_person(face_data['features'])
        
        if match_result is None:
            # Log unrecognized face attempt
            log_recognition_attempt(None, similarity, 'unknown', face_data)
            return jsonify({
                'recognized': False,
                'message': 'Face not recognized. Please register first.',
                'similarity': float(similarity)
            })
        
        person_id, person_name = match_result
        
        # Record attendance
        attendance_id = record_attendance(person_id, person_name, similarity, face_data)
        
        # Log successful recognition
        log_recognition_attempt(person_id, similarity, 'recognized', face_data)
        
        return jsonify({
            'recognized': True,
            'person_id': person_id,
            'person_name': person_name,
            'similarity': float(similarity),
            'attendance_id': attendance_id,
            'message': f'Welcome {person_name}! Attendance recorded successfully.',
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in face recognition: {e}")
        return jsonify({'error': str(e), 'recognized': False}), 500

def record_attendance(person_id, person_name, confidence_score, face_data):
    """Record attendance in database"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        # Check if already checked in today
        today = datetime.date.today()
        cursor.execute("""
            SELECT id, check_in_time, check_out_time 
            FROM attendance 
            WHERE person_id = %s AND date_recorded = %s
            ORDER BY check_in_time DESC 
            LIMIT 1
        """, (person_id, today))
        
        existing_record = cursor.fetchone()
        
        if existing_record:
            # If already checked in today, this is check-out
            if existing_record[2] is None:  # No check-out time yet
                cursor.execute("""
                    UPDATE attendance 
                    SET check_out_time = %s, last_updated = %s
                    WHERE id = %s
                """, (datetime.datetime.now(), datetime.datetime.now(), existing_record[0]))
                conn.commit()
                conn.close()
                return existing_record[0]
        
        # New check-in
        attendance_query = """
            INSERT INTO attendance (person_id, person_name, check_in_time, date_recorded, confidence_score, detection_method, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Determine status based on time
        now = datetime.datetime.now()
        status = 'present'
        if now.hour > 9:  # Late if after 9 AM
            status = 'late'
        
        attendance_values = (
            person_id,
            person_name,
            now,
            today,
            confidence_score,
            'auto',
            status,
            'face_recognition_system'
        )
        
        cursor.execute(attendance_query, attendance_values)
        attendance_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return attendance_id
        
    except Exception as e:
        print(f"Error recording attendance: {e}")
        return None

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
            'width': int(bbox[2]),
            'height': int(bbox[3])
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
        
    except Exception as e:
        print(f"Error logging recognition attempt: {e}")

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
        
        query = "SELECT * FROM attendance WHERE 1=1"
        params = []
        
        if date_filter:
            query += " AND date_recorded = %s"
            params.append(date_filter)
        
        if person_id:
            query += " AND person_id = %s"
            params.append(person_id)
        
        query += " ORDER BY check_in_time DESC"
        
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
        
        return jsonify(attendance_records)
        
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'face_detection': 'opencv',
        'message': 'Face Recognition Attendance System - Demo Version'
    })

if __name__ == '__main__':
    print("Starting Face Recognition Attendance System (Demo Version)...")
    print("Using OpenCV for basic face detection")
    print("Note: This is a simplified version for demonstration")
    app.run(debug=True, host='0.0.0.0', port=5000)
