export interface Person {
  id?: number;
  name: string;
  email?: string;
  phone?: string;
  department?: string;
  position?: string;
  status: 'active' | 'inactive';
  registration_date?: string;
  last_updated?: string;
  notes?: string;
}

export interface FaceEncoding {
  id?: number;
  person_id: number;
  encoding_data: string;
  encoding_type: 'standard' | 'enhanced' | 'multi_angle';
  face_angle: 'front' | 'left' | 'right' | 'up' | 'down';
  confidence_score: number;
  image_path?: string;
  created_date?: string;
  is_primary: boolean;
}

export interface Attendance {
  id?: number;
  person_id: number;
  person_name: string;
  check_in_time?: string;
  check_out_time?: string;
  date_recorded: string;
  confidence_score: number;
  detection_method: 'auto' | 'manual' | 'override';
  image_path?: string;
  location_id?: number;
  status: 'present' | 'late' | 'early_leave' | 'absent' | 'overtime';
  notes?: string;
  created_by?: string;
}

export interface Location {
  id?: number;
  name: string;
  description?: string;
  camera_id?: string;
  coordinates?: string;
  status: 'active' | 'inactive' | 'maintenance';
  created_date?: string;
}

export interface RecognitionLog {
  id?: number;
  person_id?: number;
  person_name?: string;
  recognition_time?: string;
  confidence_score: number;
  detection_status: 'recognized' | 'unknown' | 'low_confidence' | 'failed';
  image_path?: string;
  location_id?: number;
  processing_time_ms?: number;
  face_coordinates?: string;
  notes?: string;
}
