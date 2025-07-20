import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AttendanceService } from '../../services/attendance.service';
import { PersonService } from '../../services/person.service';
import { Person, Attendance } from '../../models/person.model';
import { Subscription, interval } from 'rxjs';

@Component({
  selector: 'app-attendance',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './attendance.component.html',
  styleUrl: './attendance.component.css'
})
export class AttendanceComponent implements OnInit, OnDestroy {
  isRecognitionActive = false;
  persons: Person[] = [];
  todayAttendance: Attendance[] = [];
  selectedDate = new Date().toISOString().split('T')[0];
  
  // Manual attendance
  selectedPersonId: number | null = null;
  isProcessing = false;
  message = '';
  messageType: 'success' | 'error' | 'info' | '' = '';
  
  // Real-time updates
  private refreshSubscription?: Subscription;
  
  // Statistics
  stats = {
    totalEmployees: 0,
    presentToday: 0,
    lateArrivals: 0,
    earlyDepartures: 0
  };

  constructor(
    private attendanceService: AttendanceService,
    private personService: PersonService
  ) {}

  ngOnInit(): void {
    this.loadPersons();
    this.loadTodayAttendance();
    this.checkRecognitionStatus();
    this.startAutoRefresh();
  }

  ngOnDestroy(): void {
    this.refreshSubscription?.unsubscribe();
  }

  private loadPersons(): void {
    this.personService.getPersons().subscribe({
      next: (persons) => {
        this.persons = persons.filter(p => p.status === 'active');
        this.stats.totalEmployees = this.persons.length;
      },
      error: (error) => {
        console.error('Error loading persons:', error);
        this.showMessage('Failed to load employees', 'error');
      }
    });
  }

  private loadTodayAttendance(): void {
    this.attendanceService.getAttendance(this.selectedDate).subscribe({
      next: (attendance) => {
        this.todayAttendance = attendance;
        this.calculateStats();
      },
      error: (error) => {
        console.error('Error loading attendance:', error);
        this.showMessage('Failed to load attendance data', 'error');
      }
    });
  }

  private calculateStats(): void {
    this.stats.presentToday = this.todayAttendance.length;
    this.stats.lateArrivals = this.todayAttendance.filter(a => a.status === 'late').length;
    this.stats.earlyDepartures = this.todayAttendance.filter(a => a.status === 'early_leave').length;
  }

  onDateChange(): void {
    this.loadAttendanceForDate();
  }

  private loadAttendanceForDate(): void {
    this.attendanceService.getAttendance(this.selectedDate).subscribe({
      next: (attendance) => {
        this.todayAttendance = attendance;
        if (this.selectedDate === new Date().toISOString().split('T')[0]) {
          this.calculateStats();
        }
      },
      error: (error) => {
        console.error('Error loading attendance for date:', error);
        this.showMessage('Failed to load attendance data', 'error');
      }
    });
  }

  toggleFaceRecognition(): void {
    this.isProcessing = true;
    
    if (this.isRecognitionActive) {
      this.attendanceService.stopFaceRecognition().subscribe({
        next: () => {
          this.isRecognitionActive = false;
          this.showMessage('Face recognition stopped', 'info');
        },
        error: (error) => {
          console.error('Error stopping recognition:', error);
          this.showMessage('Failed to stop face recognition', 'error');
        },
        complete: () => {
          this.isProcessing = false;
        }
      });
    } else {
      this.attendanceService.startFaceRecognition().subscribe({
        next: () => {
          this.isRecognitionActive = true;
          this.showMessage('Face recognition started', 'success');
        },
        error: (error) => {
          console.error('Error starting recognition:', error);
          this.showMessage('Failed to start face recognition', 'error');
        },
        complete: () => {
          this.isProcessing = false;
        }
      });
    }
  }

  manualCheckIn(): void {
    if (!this.selectedPersonId) {
      this.showMessage('Please select an employee', 'error');
      return;
    }

    this.isProcessing = true;
    this.attendanceService.checkIn(this.selectedPersonId).subscribe({
      next: (attendance) => {
        this.showMessage(`Check-in successful for ${attendance.person_name}`, 'success');
        this.loadTodayAttendance();
        this.selectedPersonId = null;
      },
      error: (error) => {
        console.error('Error during check-in:', error);
        this.showMessage('Failed to check in employee', 'error');
      },
      complete: () => {
        this.isProcessing = false;
      }
    });
  }

  manualCheckOut(): void {
    if (!this.selectedPersonId) {
      this.showMessage('Please select an employee', 'error');
      return;
    }

    this.isProcessing = true;
    this.attendanceService.checkOut(this.selectedPersonId).subscribe({
      next: (attendance) => {
        this.showMessage(`Check-out successful for ${attendance.person_name}`, 'success');
        this.loadTodayAttendance();
        this.selectedPersonId = null;
      },
      error: (error) => {
        console.error('Error during check-out:', error);
        this.showMessage('Failed to check out employee', 'error');
      },
      complete: () => {
        this.isProcessing = false;
      }
    });
  }

  private checkRecognitionStatus(): void {
    this.attendanceService.getRecognitionStatus().subscribe({
      next: (status) => {
        this.isRecognitionActive = status.active || false;
      },
      error: (error) => {
        console.error('Error checking recognition status:', error);
      }
    });
  }

  private startAutoRefresh(): void {
    // Refresh every 30 seconds
    this.refreshSubscription = interval(30000).subscribe(() => {
      if (this.selectedDate === new Date().toISOString().split('T')[0]) {
        this.loadTodayAttendance();
      }
    });
  }

  getPersonName(personId: number): string {
    const person = this.persons.find(p => p.id === personId);
    return person ? person.name : 'Unknown';
  }

  formatTime(timeString: string): string {
    return new Date(timeString).toLocaleTimeString();
  }

  getAttendanceStatusClass(status: string): string {
    switch (status) {
      case 'present': return 'status-present';
      case 'late': return 'status-late';
      case 'early_leave': return 'status-early';
      case 'absent': return 'status-absent';
      default: return '';
    }
  }

  private showMessage(text: string, type: 'success' | 'error' | 'info'): void {
    this.message = text;
    this.messageType = type;
    
    // Clear message after 5 seconds
    setTimeout(() => {
      this.message = '';
      this.messageType = '';
    }, 5000);
  }
}
