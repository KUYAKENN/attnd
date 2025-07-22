import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';

export interface FaceRecognitionResult {
  recognized: boolean;
  person_id?: number;
  person_name?: string;
  similarity?: number;
  attendance_id?: number;
  mode?: string;
  message: string;
  timestamp?: string;
  error?: string;
  success?: boolean;
  total_hours?: number;
  status?: string;
}

@Injectable({
  providedIn: 'root'
})
export class CameraService {
  private apiUrl = 'http://localhost:5000/api';
  private videoElement: HTMLVideoElement | null = null;
  private stream: MediaStream | null = null;
  private isProcessing = false;
  
  // Observable for real-time recognition results
  private recognitionResultSubject = new BehaviorSubject<FaceRecognitionResult | null>(null);
  public recognitionResult$ = this.recognitionResultSubject.asObservable();
  
  // Observable for camera status
  private cameraStatusSubject = new BehaviorSubject<string>('stopped');
  public cameraStatus$ = this.cameraStatusSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Initialize camera and start video stream
   */
  async initializeCamera(videoElement: HTMLVideoElement): Promise<boolean> {
    try {
      this.videoElement = videoElement;
      
      // Request camera permissions
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: false
      });
      
      this.videoElement.srcObject = this.stream;
      this.cameraStatusSubject.next('active');
      
      return new Promise((resolve) => {
        this.videoElement!.onloadedmetadata = () => {
          this.videoElement!.play();
          resolve(true);
        };
      });
    } catch (error) {
      console.error('Error accessing camera:', error);
      this.cameraStatusSubject.next('error');
      return false;
    }
  }

  /**
   * Stop camera stream
   */
  stopCamera(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    
    if (this.videoElement) {
      this.videoElement.srcObject = null;
    }
    
    this.cameraStatusSubject.next('stopped');
    this.isProcessing = false;
  }

  /**
   * Capture image from video stream and convert to base64
   */
  captureImage(): string | null {
    if (!this.videoElement) {
      return null;
    }

    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    if (!context) {
      return null;
    }

    canvas.width = this.videoElement.videoWidth;
    canvas.height = this.videoElement.videoHeight;
    
    context.drawImage(this.videoElement, 0, 0);
    
    return canvas.toDataURL('image/jpeg', 0.8);
  }

  /**
   * Recognize face in captured image
   */
  recognizeFace(imageData: string, mode: 'check_in' | 'check_out' = 'check_in'): Observable<FaceRecognitionResult> {
    return this.http.post<FaceRecognitionResult>(`${this.apiUrl}/face-recognition`, {
      image: imageData,
      mode: mode
    });
  }

  /**
   * Start continuous face recognition scanning
   */
  startContinuousScanning(intervalMs: number = 2000, mode: 'check_in' | 'check_out' = 'check_in'): void {
    if (this.isProcessing) {
      return;
    }

    this.isProcessing = true;
    this.scanForFaces(intervalMs, mode);
  }

  /**
   * Stop continuous scanning
   */
  stopContinuousScanning(): void {
    this.isProcessing = false;
  }

  /**
   * Private method for continuous face scanning
   */
  private scanForFaces(intervalMs: number, mode: 'check_in' | 'check_out' = 'check_in'): void {
    if (!this.isProcessing || !this.videoElement) {
      return;
    }

    const imageData = this.captureImage();
    if (imageData) {
      this.recognizeFace(imageData, mode).subscribe({
        next: (result) => {
          this.recognitionResultSubject.next(result);
          
          // If face recognized, wait longer before next scan
          const nextScanDelay = result.recognized ? intervalMs * 3 : intervalMs;
          setTimeout(() => this.scanForFaces(intervalMs, mode), nextScanDelay);
        },
        error: (error) => {
          console.error('Face recognition error:', error);
          this.recognitionResultSubject.next({
            recognized: false,
            message: 'Recognition service error',
            error: error.message
          });
          
          // Continue scanning after error
          setTimeout(() => this.scanForFaces(intervalMs, mode), intervalMs);
        }
      });
    } else {
      // If couldn't capture image, try again shortly
      setTimeout(() => this.scanForFaces(intervalMs, mode), 500);
    }
  }

  /**
   * Register new person with face image
   */
  registerPerson(personData: any, faceImage: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/persons`, {
      ...personData,
      face_image: faceImage
    });
  }

  /**
   * Check backend health
   */
  checkBackendHealth(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }

  /**
   * Get recognition logs for monitoring
   */
  getRecognitionLogs(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/recognition-logs`);
  }

  /**
   * Get today's attendance records
   */
  getTodayAttendance(): Observable<any[]> {
    const today = new Date().toISOString().split('T')[0];
    return this.http.get<any[]>(`${this.apiUrl}/attendance?date=${today}`);
  }

  /**
   * Get employees present today
   */
  getPresentToday(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/attendance/present-today`);
  }
}
