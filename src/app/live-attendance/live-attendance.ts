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
   * Get result status class with time-based styling
   */
  getResultClass(): string {
    if (!this.currentResult) return '';
    
    if (this.currentResult.recognized) {
      // Check if the result includes status information
      if (this.currentResult.status === 'late') {
        return 'result-late';
      } else if (this.currentResult.status === 'overtime') {
        return 'result-overtime';
      } else if (this.currentResult.status === 'present') {
        return 'result-success';
      } else {
        return 'result-success'; // Default for recognized faces
      }
    } else {
      return 'result-warning';
    }
  }

  /**
   * Get status badge for attendance records
   */
  getStatusBadgeClass(status: string): string {
    switch (status) {
      case 'present': return 'badge-success';
      case 'late': return 'badge-warning';
      case 'overtime': return 'badge-info';
      case 'absent': return 'badge-danger';
      case 'early_leave': return 'badge-info';
      default: return 'badge-secondary';
    }
  }

  /**
   * Get status display text
   */
  getStatusDisplayText(status: string): string {
    switch (status) {
      case 'present': return 'On Time';
      case 'late': return 'Late';
      case 'overtime': return 'Overtime';
      case 'absent': return 'Absent';
      case 'early_leave': return 'Early Leave';
      case 'partial': return 'Partial Day';
      default: return status;
    }
  }

  /**
   * Check if current time is within on-time check-in window
   */
  isOnTimeWindow(): boolean {
    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes(); // Convert to minutes
    const onTimeStart = 8 * 60; // 8:00 AM in minutes (480)
    const onTimeEnd = 9 * 60 + 30; // 9:30 AM in minutes (570)
    
    return currentTime >= onTimeStart && currentTime <= onTimeEnd;
  }

  /**
   * Get time window status message
   */
  getTimeWindowMessage(): string {
    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();
    const onTimeStart = 8 * 60; // 8:00 AM
    const onTimeEnd = 9 * 60 + 30; // 9:30 AM
    
    if (currentTime < onTimeStart) {
      const minutesUntilStart = onTimeStart - currentTime;
      const hours = Math.floor(minutesUntilStart / 60);
      const minutes = minutesUntilStart % 60;
      
      if (hours > 0) {
        return `Check-in starts in ${hours}h ${minutes}m (8:00 AM)`;
      } else {
        return `Check-in starts in ${minutes}m (8:00 AM)`;
      }
    } else if (currentTime >= onTimeStart && currentTime <= onTimeEnd) {
      const minutesRemaining = onTimeEnd - currentTime;
      return `On-time check-in window: ${minutesRemaining} minutes remaining`;
    } else {
      return 'Late check-in period (after 9:30 AM)';
    }
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
      
      // Resume scanning with the new mode if camera is active
      if (this.cameraStatus === 'active') {
        this.cameraService.stopContinuousScanning();
        setTimeout(() => {
          this.cameraService.resumeScanning(2000, this.attendanceMode);
        }, 500); // Brief pause before resuming with new mode
      }
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

  /**
   * Get confidence display with proper formatting
   */
  getConfidenceDisplay(similarity?: number): string {
    if (similarity === undefined || similarity === null || isNaN(similarity)) {
      return 'N/A';
    }
    return `${(similarity * 100).toFixed(1)}%`;
  }

  /**
   * Get time-based attendance message
   */
  getAttendanceStatusMessage(status: string, timestamp?: string): string {
    if (!timestamp) return '';
    
    const checkInTime = new Date(timestamp);
    const timeStr = checkInTime.toLocaleTimeString();
    
    switch (status) {
      case 'present':
        return `✅ On-time check-in at ${timeStr}`;
      case 'late':
        return `⚠️ Late check-in at ${timeStr} (after 9:30 AM)`;
      default:
        return `Check-in recorded at ${timeStr}`;
    }
  }
}
