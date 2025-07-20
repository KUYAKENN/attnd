import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

interface Person {
  id?: number;
  name: string;
  email: string;
  phone: string;
  department: string;
  position: string;
  status: string;
  notes: string;
}

interface RegistrationResponse {
  id: number;
  name: string;
  status: string;
  message: string;
  face_quality: number;
}

@Component({
  selector: 'app-registration',
  imports: [CommonModule, FormsModule],
  templateUrl: './registration.html',
  styleUrl: './registration.css'
})
export class Registration implements OnInit {
  @ViewChild('videoElement', { static: false }) videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement', { static: false }) canvasElement!: ElementRef<HTMLCanvasElement>;
  @ViewChild('fileInput', { static: false }) fileInput!: ElementRef<HTMLInputElement>;

  // Form data
  person: Person = {
    name: '',
    email: '',
    phone: '',
    department: '',
    position: '',
    status: 'active',
    notes: ''
  };

  // Camera and image state
  cameraActive: boolean = false;
  capturedImage: string | null = null;
  faceImageBase64: string | null = null;
  
  // Auto-capture state
  isDetectingFace: boolean = false;
  faceDetected: boolean = false;
  captureCountdown: number = 0;
  autoCapturing: boolean = false;
  
  // UI state
  isSubmitting: boolean = false;
  message: string = '';
  messageType: 'success' | 'error' | '' = '';
  
  // Options
  departments = ['Engineering', 'Human Resources', 'Marketing', 'Sales', 'Finance', 'Operations', 'Other'];
  positions = ['Manager', 'Developer', 'Analyst', 'Specialist', 'Coordinator', 'Assistant', 'Other'];

  private apiUrl = 'http://localhost:5000/api';
  private stream: MediaStream | null = null;
  private detectionInterval: any = null;
  private countdownInterval: any = null;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.checkBackendConnection();
    this.checkCameraSupport();
  }

  /**
   * Check if camera is supported
   */
  async checkCameraSupport() {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        this.showMessage('Camera not supported on this device/browser.', 'error');
        return;
      }

      // Check available devices
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(device => device.kind === 'videoinput');
      
      if (videoDevices.length === 0) {
        this.showMessage('No camera found on this device.', 'error');
        return;
      }

      console.log('Camera support detected:', videoDevices.length, 'camera(s) available');
      
      // Check permissions
      try {
        const permissionStatus = await navigator.permissions.query({ name: 'camera' as PermissionName });
        console.log('Camera permission status:', permissionStatus.state);
        
        if (permissionStatus.state === 'denied') {
          this.showMessage('Camera permission denied. Please enable camera access in browser settings.', 'error');
        }
      } catch (error) {
        console.log('Permission query not supported, will request on camera start');
      }
      
    } catch (error) {
      console.error('Error checking camera support:', error);
    }
  }

  /**
   * Check if backend is running
   */
  checkBackendConnection() {
    this.http.get(`${this.apiUrl}/health`).subscribe({
      next: (response: any) => {
        console.log('Backend connected:', response);
      },
      error: (error) => {
        console.error('Backend connection failed:', error);
        this.showMessage('Backend server not available. Please start the Python server.', 'error');
      }
    });
  }

  /**
   * Start camera for face capture
   */
  async startCamera() {
    try {
      console.log('Starting camera...');
      
      // Clear any existing message
      this.clearMessage();
      
      // Request camera with specific constraints for better face capture
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user' // Front-facing camera preferred
        }
      });
      
      console.log('Camera stream obtained successfully');
      
      // First set cameraActive to true to render the video element
      this.cameraActive = true;
      
      // Wait for Angular to render the video element
      setTimeout(() => {
        this.initializeVideoElement();
      }, 100);
      
    } catch (error) {
      console.error('Camera access error:', error);
      let errorMessage = 'Camera access failed: ';
      
      if (error instanceof Error) {
        if (error.name === 'NotAllowedError') {
          errorMessage += 'Please allow camera permissions and try again.';
        } else if (error.name === 'NotFoundError') {
          errorMessage += 'No camera found on this device.';
        } else if (error.name === 'NotReadableError') {
          errorMessage += 'Camera is already in use by another application.';
        } else {
          errorMessage += error.message;
        }
      }
      
      this.showMessage(errorMessage, 'error');
    }
  }

  /**
   * Initialize video element after it's rendered
   */
  private initializeVideoElement() {
    if (this.videoElement && this.stream) {
      const video = this.videoElement.nativeElement;
      video.srcObject = this.stream;
      
      console.log('Video element found, setting srcObject');
      
      // Wait for video to be ready
      video.onloadedmetadata = () => {
        console.log('Video metadata loaded, dimensions:', video.videoWidth, 'x', video.videoHeight);
        
        video.play().then(() => {
          console.log('Video playing successfully');
          
          // Force video visibility with inline styles
          video.style.display = 'block';
          video.style.visibility = 'visible';
          video.style.opacity = '1';
          video.style.width = '640px';
          video.style.height = '480px';
          
          console.log('Video element styles applied, should be visible now');
          
          this.showMessage('Camera started! You can see your live face - auto-capture will begin when face is detected.', 'success');
          
          // Start auto face detection after a short delay to ensure video is stable
          setTimeout(() => {
            this.startFaceDetection();
          }, 1000);
        }).catch((error) => {
          console.error('Error playing video:', error);
          this.showMessage('Error starting video playback: ' + error.message, 'error');
        });
      };
      
      video.onerror = (error) => {
        console.error('Video error:', error);
        this.showMessage('Video playback error.', 'error');
      };
      
    } else {
      console.error('Video element not found! Retrying...');
      // Retry after another short delay
      setTimeout(() => {
        this.initializeVideoElement();
      }, 200);
    }
  }

  /**
   * Stop camera
   */
  stopCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    this.cameraActive = false;
    this.stopFaceDetection();
  }

  /**
   * Start automatic face detection
   */
  startFaceDetection() {
    if (this.detectionInterval) {
      clearInterval(this.detectionInterval);
    }

    this.isDetectingFace = true;
    console.log('Starting face detection...');

    // Debug: Check video status
    this.debugVideoStatus();

    // Check for face every 500ms
    this.detectionInterval = setInterval(() => {
      this.detectFaceInVideo();
    }, 500);
  }

  /**
   * Debug video status
   */
  debugVideoStatus() {
    if (this.videoElement) {
      const video = this.videoElement.nativeElement;
      console.log('Video debug info:', {
        videoWidth: video.videoWidth,
        videoHeight: video.videoHeight,
        readyState: video.readyState,
        paused: video.paused,
        ended: video.ended,
        srcObject: !!video.srcObject,
        style: {
          display: video.style.display,
          visibility: video.style.visibility,
          opacity: video.style.opacity
        }
      });
    }
  }

  /**
   * Stop face detection
   */
  stopFaceDetection() {
    if (this.detectionInterval) {
      clearInterval(this.detectionInterval);
      this.detectionInterval = null;
    }
    
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
    }

    this.isDetectingFace = false;
    this.faceDetected = false;
    this.captureCountdown = 0;
    this.autoCapturing = false;
  }

  /**
   * Detect face in video stream
   */
  async detectFaceInVideo() {
    if (!this.videoElement || !this.canvasElement || this.autoCapturing) {
      return;
    }

    const video = this.videoElement.nativeElement;
    const canvas = this.canvasElement.nativeElement;
    const context = canvas.getContext('2d');

    if (!context || video.videoWidth === 0 || video.videoHeight === 0) {
      return;
    }

    try {
      // Set canvas size
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Draw current frame
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert to base64 for face detection
      const imageData = canvas.toDataURL('image/jpeg', 0.7);

      // Send to backend for face detection
      const response = await this.http.post(`${this.apiUrl}/face-detection`, {
        image: imageData
      }).toPromise() as any;

      if (response && response.face_detected) {
        if (!this.faceDetected) {
          console.log('Face detected! Starting countdown...');
          this.faceDetected = true;
          this.startCaptureCountdown();
        }
      } else {
        if (this.faceDetected) {
          console.log('Face lost, stopping countdown');
          this.faceDetected = false;
          this.stopCaptureCountdown();
        }
      }
    } catch (error) {
      // Fallback: use simple timeout-based capture
      if (!this.faceDetected && !this.autoCapturing) {
        console.log('Face detection service unavailable, using timer-based capture');
        this.faceDetected = true;
        this.startCaptureCountdown();
      }
    }
  }

  /**
   * Start countdown for automatic capture
   */
  startCaptureCountdown() {
    if (this.countdownInterval || this.autoCapturing) {
      return;
    }

    this.captureCountdown = 3;
    this.autoCapturing = true;

    this.countdownInterval = setInterval(() => {
      this.captureCountdown--;
      
      if (this.captureCountdown <= 0) {
        this.executeAutoCapture();
      }
    }, 1000);
  }

  /**
   * Stop capture countdown
   */
  stopCaptureCountdown() {
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
    }
    this.captureCountdown = 0;
    this.autoCapturing = false;
  }

  /**
   * Execute automatic capture
   */
  executeAutoCapture() {
    console.log('Auto-capturing face image...');
    this.stopCaptureCountdown();
    this.captureImage();
  }

  /**
   * Capture image from camera
   */
  captureImage() {
    if (!this.videoElement || !this.canvasElement) {
      this.showMessage('Camera not ready. Please try again.', 'error');
      return;
    }

    const video = this.videoElement.nativeElement;
    const canvas = this.canvasElement.nativeElement;
    const context = canvas.getContext('2d');

    if (!context) {
      this.showMessage('Canvas not supported.', 'error');
      return;
    }

    // Check if video is playing
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      this.showMessage('Video not ready. Please wait for camera to load.', 'error');
      return;
    }

    console.log('Capturing image from video:', video.videoWidth, 'x', video.videoHeight);

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Save the current context state
    context.save();
    
    // Flip the canvas horizontally to un-mirror the image for capture
    context.scale(-1, 1);
    context.translate(-canvas.width, 0);

    // Draw video frame to canvas (this will be un-mirrored)
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Restore the context state
    context.restore();

    // Convert to base64 with high quality for face recognition
    this.faceImageBase64 = canvas.toDataURL('image/jpeg', 0.9);
    this.capturedImage = this.faceImageBase64;
    
    console.log('Image captured, size:', this.faceImageBase64.length, 'characters');
    
    // Stop camera after capture
    this.stopCamera();
    
    this.showMessage('Face image captured successfully! You can now register the employee.', 'success');
  }

  /**
   * Handle file upload
   */
  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      this.showMessage('Please select a valid image file.', 'error');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      this.showMessage('Image file too large. Please select an image under 5MB.', 'error');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      this.faceImageBase64 = e.target?.result as string;
      this.capturedImage = this.faceImageBase64;
      this.showMessage('Image uploaded successfully!', 'success');
    };
    reader.readAsDataURL(file);
  }

  /**
   * Remove captured/uploaded image
   */
  removeImage() {
    this.capturedImage = null;
    this.faceImageBase64 = null;
    if (this.fileInput) {
      this.fileInput.nativeElement.value = '';
    }
  }

  /**
   * Validate form data
   */
  validateForm(): boolean {
    if (!this.person.name.trim()) {
      this.showMessage('Name is required.', 'error');
      return false;
    }

    if (!this.person.email.trim()) {
      this.showMessage('Email is required.', 'error');
      return false;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(this.person.email)) {
      this.showMessage('Please enter a valid email address.', 'error');
      return false;
    }

    if (!this.faceImageBase64) {
      this.showMessage('Face image is required. Please capture or upload an image.', 'error');
      return false;
    }

    return true;
  }

  /**
   * Submit registration form
   */
  async submitRegistration() {
    if (!this.validateForm()) {
      return;
    }

    this.isSubmitting = true;
    this.message = '';

    const registrationData = {
      name: this.person.name.trim(),
      email: this.person.email.trim(),
      phone: this.person.phone.trim(),
      department: this.person.department,
      position: this.person.position,
      status: this.person.status,
      notes: this.person.notes.trim(),
      face_image: this.faceImageBase64
    };

    try {
      const response = await this.http.post<RegistrationResponse>(
        `${this.apiUrl}/persons`,
        registrationData
      ).toPromise();

      if (response) {
        this.showMessage(
          `Registration successful! ${response.name} has been registered with ID: ${response.id}`,
          'success'
        );
        
        // Reset form
        this.resetForm();
      }
    } catch (error: any) {
      console.error('Registration error:', error);
      
      let errorMessage = 'Registration failed. Please try again.';
      if (error.error?.error) {
        errorMessage = error.error.error;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      this.showMessage(errorMessage, 'error');
    } finally {
      this.isSubmitting = false;
    }
  }

  /**
   * Reset form to initial state
   */
  resetForm() {
    this.person = {
      name: '',
      email: '',
      phone: '',
      department: '',
      position: '',
      status: 'active',
      notes: ''
    };
    this.removeImage();
    this.stopCamera();
  }

  /**
   * Show message to user
   */
  showMessage(message: string, type: 'success' | 'error') {
    this.message = message;
    this.messageType = type;
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
      setTimeout(() => {
        this.message = '';
        this.messageType = '';
      }, 5000);
    }
  }

  /**
   * Test camera access for debugging
   */
  async testCameraAccess() {
    try {
      console.log('Testing camera access...');
      
      // Request basic camera access
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      
      console.log('Camera test successful, stream:', stream);
      this.showMessage('Camera access test successful! Camera is available.', 'success');
      
      // Stop test stream
      stream.getTracks().forEach(track => track.stop());
      
    } catch (error) {
      console.error('Camera test failed:', error);
      this.showMessage('Camera test failed: ' + (error as Error).message, 'error');
    }
  }

  /**
   * Clear message
   */
  clearMessage() {
    this.message = '';
    this.messageType = '';
  }
}
