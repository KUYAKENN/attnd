import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ExportService {
  private apiUrl = 'http://localhost:5000/api';

  constructor(private http: HttpClient) {}

  /**
   * Export attendance records for a date range
   */
  exportAttendance(startDate: string, endDate: string, format: 'csv' | 'excel' = 'csv'): Observable<Blob> {
    const params = {
      start_date: startDate,
      end_date: endDate,
      format: format
    };

    return this.http.get(`${this.apiUrl}/attendance/export`, {
      params: params,
      responseType: 'blob'
    });
  }

  /**
   * Get attendance summary for date range
   */
  getAttendanceSummary(startDate: string, endDate: string): Observable<any> {
    const params = {
      start_date: startDate,
      end_date: endDate
    };

    return this.http.get(`${this.apiUrl}/attendance/summary`, { params });
  }

  /**
   * Download blob as file
   */
  downloadFile(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }

  /**
   * Generate filename based on date range and format
   */
  generateFilename(startDate: string, endDate: string, format: 'csv' | 'excel'): string {
    const start = new Date(startDate).toISOString().split('T')[0];
    const end = new Date(endDate).toISOString().split('T')[0];
    const extension = format === 'csv' ? 'csv' : 'xlsx';
    
    if (start === end) {
      return `attendance_${start}.${extension}`;
    } else {
      return `attendance_${start}_to_${end}.${extension}`;
    }
  }
}
