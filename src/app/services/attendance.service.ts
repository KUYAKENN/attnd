import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { Attendance } from '../models/person.model';

@Injectable({
  providedIn: 'root'
})
export class AttendanceService {
  private apiUrl = 'http://localhost:5000/api';
  private attendanceSubject = new BehaviorSubject<Attendance[]>([]);
  public attendance$ = this.attendanceSubject.asObservable();

  constructor(private http: HttpClient) {}

  // Get attendance records
  getAttendance(date?: string, personId?: number): Observable<Attendance[]> {
    let params = '';
    if (date || personId) {
      const searchParams = new URLSearchParams();
      if (date) searchParams.append('date', date);
      if (personId) searchParams.append('person_id', personId.toString());
      params = '?' + searchParams.toString();
    }
    return this.http.get<Attendance[]>(`${this.apiUrl}/attendance${params}`);
  }

  // Manual check-in
  checkIn(personId: number, locationId?: number): Observable<Attendance> {
    return this.http.post<Attendance>(`${this.apiUrl}/attendance/check-in`, {
      person_id: personId,
      location_id: locationId,
      detection_method: 'manual'
    });
  }

  // Manual check-out
  checkOut(personId: number): Observable<Attendance> {
    return this.http.put<Attendance>(`${this.apiUrl}/attendance/check-out`, {
      person_id: personId,
      detection_method: 'manual'
    });
  }

  // Export attendance to CSV
  exportAttendance(startDate: string, endDate: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/attendance/export`, {
      params: { start_date: startDate, end_date: endDate },
      responseType: 'blob'
    });
  }

  // Get attendance summary
  getAttendanceSummary(startDate: string, endDate: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/attendance/summary`, {
      params: { start_date: startDate, end_date: endDate }
    });
  }

  // Start face recognition
  startFaceRecognition(): Observable<any> {
    return this.http.post(`${this.apiUrl}/recognition/start`, {});
  }

  // Stop face recognition
  stopFaceRecognition(): Observable<any> {
    return this.http.post(`${this.apiUrl}/recognition/stop`, {});
  }

  // Get recognition status
  getRecognitionStatus(): Observable<any> {
    return this.http.get(`${this.apiUrl}/recognition/status`);
  }
}
