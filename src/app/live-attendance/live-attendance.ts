import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule, TitleCasePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CameraService, FaceRecognitionResult } from '../services/camera.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-live-attendance',
  imports: [CommonModule, TitleCasePipe, FormsModule],
  templateUrl: './live-attendance.html',
  styleUrl: './live-attendance.css'
})
export class LiveAttendanceComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement', { static: true }) videoElement!: ElementRef<HTMLVideoElement>;
  
  // Camera and recognition state
  cameraStatus: string = 'stopped';
  isScanning: boolean = false;
  currentResult: FaceRecognitionResult | null = null;
  
  // Attendance mode
  attendanceMode: 'check_in' | 'check_out' = 'check_in';
  showPasswordModal: boolean = false;
  passwordInput: string = '';
  
  // Recent attendance records
  recentAttendance: any[] = [];
  presentEmployees: any[] = [];
  presentCount: number = 0;
  recognitionLogs: any[] = [];
  
  // UI state
  showLogs: boolean = false;
  lastRecognitionTime: Date | null = null;
  
  private subscriptions: Subscription[] = [];
  private readonly ADMIN_PASSWORD = 'qunabydevs7719';

  constructor(private cameraService: CameraService) {}

  async ngOnInit() {
    // Subscribe to camera status
    this.subscriptions.push(
      this.cameraService.cameraStatus$.subscribe(status => {
        this.cameraStatus = status;
      })
    );

    // Subscribe to recognition results
    this.subscriptions.push(
      this.cameraService.recognitionResult$.subscribe(result => {
        if (result) {
          this.currentResult = result;
          this.lastRecognitionTime = new Date();
          
          // If person recognized, refresh attendance list
          if (result.recognized) {
            this.loadTodayAttendance();
            this.loadPresentEmployees();
          }
        }
      })
    );

    // Load initial data
    this.loadTodayAttendance();
    this.loadPresentEmployees();
    this.checkBackendHealth();
  }

  ngOnDestroy() {
    this.stopCamera();
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  /**
   * Start camera and face recognition
   */
  async startCamera() {
    try {
      const success = await this.cameraService.initializeCamera(this.videoElement.nativeElement);
      if (success) {
        this.startScanning();
      }
    } catch (error) {
      console.error('Failed to start camera:', error);
    }
  }

  /**
   * Stop camera and scanning
   */
  stopCamera() {
    this.cameraService.stopCamera();
    this.cameraService.stopContinuousScanning();
    this.isScanning = false;
  }

  /**
   * Start face recognition scanning
   */
  startScanning() {
    if (this.cameraStatus === 'active') {
      this.isScanning = true;
      this.cameraService.startContinuousScanning(2000, this.attendanceMode); // Scan every 2 seconds with current mode
    }
  }

  /**
   * Stop face recognition scanning
   */
  stopScanning() {
    this.isScanning = false;
    this.cameraService.stopContinuousScanning();
  }

  /**
   * Manual capture for testing
   */
  manualCapture() {
    const imageData = this.cameraService.captureImage();
    if (imageData) {
      this.cameraService.recognizeFace(imageData, this.attendanceMode).subscribe({
        next: (result) => {
          this.currentResult = result;
          this.lastRecognitionTime = new Date();
          if (result.recognized) {
            this.loadTodayAttendance();
          }
        },
        error: (error) => {
          console.error('Manual recognition error:', error);
        }
      });
    }
  }

  /**
   * Load today's attendance records
   */
  loadTodayAttendance() {
    this.cameraService.getTodayAttendance().subscribe({
      next: (records) => {
        this.recentAttendance = records.slice(0, 10); // Show last 10 records
      },
      error: (error) => {
        console.error('Error loading attendance:', error);
      }
    });
  }

  /**
   * Load employees present today
   */
  loadPresentEmployees() {
    this.cameraService.getPresentToday().subscribe({
      next: (data) => {
        this.presentEmployees = data.employees || [];
        this.presentCount = data.present_count || 0;
      },
      error: (error) => {
        console.error('Error loading present employees:', error);
        this.presentEmployees = [];
        this.presentCount = 0;
      }
    });
  }

  /**
   * Load recognition logs
   */
  loadRecognitionLogs() {
    this.cameraService.getRecognitionLogs().subscribe({
      next: (logs) => {
        this.recognitionLogs = logs.slice(0, 20); // Show last 20 logs
      },
      error: (error) => {
        console.error('Error loading logs:', error);
      }
    });
  }

  /**
   * Check backend health
   */
  checkBackendHealth() {
    this.cameraService.checkBackendHealth().subscribe({
      next: (health) => {
        console.log('Backend health:', health);
      },
      error: (error) => {
        console.error('Backend health check failed:', error);
      }
    });
  }

  /**
   * Toggle logs display
   */
  toggleLogs() {
    this.showLogs = !this.showLogs;
    if (this.showLogs) {
      this.loadRecognitionLogs();
    }
  }

  /**
   * Get status color class
   */
  getStatusClass(): string {
    switch (this.cameraStatus) {
      case 'active': return 'status-active';
      case 'error': return 'status-error';
      default: return 'status-stopped';
    }
  }

  /**
   * Get result status class
   */
  getResultClass(): string {
    if (!this.currentResult) return '';
    return this.currentResult.recognized ? 'result-success' : 'result-warning';
  }

  /**
   * Format time for display
   */
  formatTime(timeString: string): string {
    return new Date(timeString).toLocaleTimeString();
  }

  /**
   * Calculate duration since check-in
   */
  calculateDuration(checkInTime: string): string {
    if (!checkInTime) return '';
    
    const checkIn = new Date(checkInTime);
    const now = new Date();
    const diff = now.getTime() - checkIn.getTime();
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  }

  /**
   * Get time since last recognition
   */
  getTimeSinceLastRecognition(): string {
    if (!this.lastRecognitionTime) return '';
    
    const diff = Date.now() - this.lastRecognitionTime.getTime();
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    return `${minutes}m ago`;
  }

  /**
   * Request mode change (shows password modal)
   */
  requestModeChange(): void {
    this.showPasswordModal = true;
    this.passwordInput = '';
  }

  /**
   * Verify password and change mode
   */
  verifyPasswordAndChangeMode(): void {
    if (this.passwordInput === this.ADMIN_PASSWORD) {
      this.attendanceMode = this.attendanceMode === 'check_in' ? 'check_out' : 'check_in';
      this.showPasswordModal = false;
      this.passwordInput = '';
    } else {
      alert('Incorrect password!');
      this.passwordInput = '';
    }
  }

  /**
   * Cancel password modal
   */
  cancelPasswordModal(): void {
    this.showPasswordModal = false;
    this.passwordInput = '';
  }

  /**
   * Get mode display text
   */
  getModeDisplayText(): string {
    return this.attendanceMode === 'check_in' ? 'Check In' : 'Check Out';
  }

  /**
   * Get mode color class
   */
  getModeColorClass(): string {
    return this.attendanceMode === 'check_in' ? 'mode-checkin' : 'mode-checkout';
  }
}
