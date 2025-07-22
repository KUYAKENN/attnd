import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ExportService } from '../../services/export.service';

@Component({
  selector: 'app-export',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './export.component.html',
  styleUrl: './export.component.css'
})
export class ExportComponent {
  startDate: string = '';
  endDate: string = '';
  exportFormat: 'csv' | 'excel' = 'excel'; // Default to Excel
  selectedMonth: string = '';
  selectedYear: string = '';
  isExporting: boolean = false;
  message: string = '';
  messageType: 'success' | 'error' | 'info' = 'info';
  showSummary: boolean = false;
  summaryData: any = null;
  activeTab: 'monthly' | 'custom' = 'monthly';

  // Computed properties to prevent infinite change detection
  availableMonths = [
    { value: '01', label: 'January' },
    { value: '02', label: 'February' },
    { value: '03', label: 'March' },
    { value: '04', label: 'April' },
    { value: '05', label: 'May' },
    { value: '06', label: 'June' },
    { value: '07', label: 'July' },
    { value: '08', label: 'August' },
    { value: '09', label: 'September' },
    { value: '10', label: 'October' },
    { value: '11', label: 'November' },
    { value: '12', label: 'December' }
  ];

  availableYears: string[] = [];
  selectedMonthLabel: string = '';

  // Quick date range options
  quickRanges = [
    { label: 'Today', value: 'today' },
    { label: 'Yesterday', value: 'yesterday' },
    { label: 'This Week', value: 'thisWeek' },
    { label: 'Last Week', value: 'lastWeek' },
    { label: 'This Month', value: 'thisMonth' },
    { label: 'Last Month', value: 'lastMonth' },
    { label: 'Last 30 Days', value: 'last30Days' },
    { label: 'Last 90 Days', value: 'last90Days' }
  ];

  constructor(private exportService: ExportService) {
    // Set default to current month
    this.setQuickRange('thisMonth');
    
    // Initialize month/year selectors
    const now = new Date();
    this.selectedMonth = (now.getMonth() + 1).toString().padStart(2, '0');
    this.selectedYear = now.getFullYear().toString();
    
    // Initialize available years (current year ± 2 years)
    this.initializeAvailableYears();
    
    // Update selected month label
    this.updateSelectedMonthLabel();
  }

  /**
   * Initialize available years
   */
  private initializeAvailableYears(): void {
    const currentYear = new Date().getFullYear();
    this.availableYears = [];
    for (let year = currentYear - 2; year <= currentYear + 1; year++) {
      this.availableYears.push(year.toString());
    }
  }

  /**
   * Update selected month label when month changes
   */
  private updateSelectedMonthLabel(): void {
    const month = this.availableMonths.find(m => m.value === this.selectedMonth);
    this.selectedMonthLabel = month ? month.label : '';
  }

  /**
   * Set quick date range
   */
  setQuickRange(range: string): void {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    switch (range) {
      case 'today':
        this.startDate = this.formatDate(today);
        this.endDate = this.formatDate(today);
        break;
        
      case 'yesterday':
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        this.startDate = this.formatDate(yesterday);
        this.endDate = this.formatDate(yesterday);
        break;
        
      case 'thisWeek':
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - today.getDay());
        this.startDate = this.formatDate(startOfWeek);
        this.endDate = this.formatDate(today);
        break;
        
      case 'lastWeek':
        const lastWeekStart = new Date(today);
        lastWeekStart.setDate(today.getDate() - today.getDay() - 7);
        const lastWeekEnd = new Date(lastWeekStart);
        lastWeekEnd.setDate(lastWeekStart.getDate() + 6);
        this.startDate = this.formatDate(lastWeekStart);
        this.endDate = this.formatDate(lastWeekEnd);
        break;
        
      case 'thisMonth':
        const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
        this.startDate = this.formatDate(startOfMonth);
        this.endDate = this.formatDate(today);
        break;
        
      case 'lastMonth':
        const lastMonthStart = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0);
        this.startDate = this.formatDate(lastMonthStart);
        this.endDate = this.formatDate(lastMonthEnd);
        break;
        
      case 'last30Days':
        const last30 = new Date(today);
        last30.setDate(today.getDate() - 30);
        this.startDate = this.formatDate(last30);
        this.endDate = this.formatDate(today);
        break;
        
      case 'last90Days':
        const last90 = new Date(today);
        last90.setDate(today.getDate() - 90);
        this.startDate = this.formatDate(last90);
        this.endDate = this.formatDate(today);
        break;
    }
  }

  /**
   * Format date for input field
   */
  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  /**
   * Validate date range
   */
  isValidDateRange(): boolean {
    if (!this.startDate || !this.endDate) {
      return false;
    }
    
    const start = new Date(this.startDate);
    const end = new Date(this.endDate);
    
    return start <= end;
  }

  /**
   * Export attendance data
   */
  exportAttendance(): void {
    if (!this.isValidDateRange()) {
      this.showMessage('Please select a valid date range', 'error');
      return;
    }

    this.isExporting = true;
    this.showMessage('Exporting attendance data...', 'info');

    this.exportService.exportAttendance(this.startDate, this.endDate, this.exportFormat)
      .subscribe({
        next: (blob) => {
          const filename = this.exportService.generateFilename(
            this.startDate, 
            this.endDate, 
            this.exportFormat
          );
          
          this.exportService.downloadFile(blob, filename);
          this.showMessage(`Successfully exported ${filename}`, 'success');
        },
        error: (error) => {
          console.error('Export error:', error);
          this.showMessage('Failed to export attendance data', 'error');
        },
        complete: () => {
          this.isExporting = false;
        }
      });
  }

  /**
   * Export monthly attendance - convenience method
   */
  exportMonthlyAttendance(): void {
    if (!this.selectedMonth || !this.selectedYear) {
      this.showMessage('Please select month and year', 'error');
      return;
    }

    const year = parseInt(this.selectedYear);
    const month = parseInt(this.selectedMonth);
    
    // Calculate first and last day of selected month
    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0);
    
    this.startDate = this.formatDate(firstDay);
    this.endDate = this.formatDate(lastDay);
    
    // Force Excel format for monthly export
    this.exportFormat = 'excel';
    
    this.exportAttendance();
  }

  /**
   * Get attendance summary
   */
  getSummary(): void {
    if (!this.isValidDateRange()) {
      this.showMessage('Please select a valid date range', 'error');
      return;
    }

    this.exportService.getAttendanceSummary(this.startDate, this.endDate)
      .subscribe({
        next: (summary) => {
          console.log('Attendance Summary:', summary);
          this.summaryData = summary;
          this.showSummary = true;
          this.showMessage(`Summary loaded: ${summary.summary.total_attendance_records} records found`, 'info');
        },
        error: (error) => {
          console.error('Summary error:', error);
          this.showMessage('Failed to get attendance summary', 'error');
        }
      });
  }

  /**
   * Show message to user
   */
  private showMessage(text: string, type: 'success' | 'error' | 'info'): void {
    this.message = text;
    this.messageType = type;
    
    // Clear message after 5 seconds
    setTimeout(() => {
      this.message = '';
    }, 5000);
  }

  /**
   * Get date range description
   */
  getDateRangeDescription(): string {
    if (!this.startDate || !this.endDate) {
      return 'No date range selected';
    }
    
    const start = new Date(this.startDate);
    const end = new Date(this.endDate);
    
    if (this.startDate === this.endDate) {
      return start.toLocaleDateString();
    } else {
      return `${start.toLocaleDateString()} - ${end.toLocaleDateString()}`;
    }
  }

  /**
   * Set month/year from quick range selection
   */
  setMonthFromQuickRange(range: string): void {
    const now = new Date();
    
    if (range === 'thisMonth') {
      this.selectedMonth = (now.getMonth() + 1).toString().padStart(2, '0');
      this.selectedYear = now.getFullYear().toString();
    } else if (range === 'lastMonth') {
      const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
      this.selectedMonth = (lastMonth.getMonth() + 1).toString().padStart(2, '0');
      this.selectedYear = lastMonth.getFullYear().toString();
    }
    
    // Update the label when month changes
    this.updateSelectedMonthLabel();
  }

  /**
   * Toggle summary display
   */
  toggleSummary(): void {
    this.showSummary = !this.showSummary;
    if (this.showSummary && !this.summaryData) {
      this.getSummary();
    }
  }

  /**
   * Get message icon class
   */
  getMessageIcon(): string {
    switch (this.messageType) {
      case 'success': return 'icon-success';
      case 'error': return 'icon-error';
      case 'info': return 'icon-info';
      default: return 'icon-info';
    }
  }

  /**
   * Handle month selection change
   */
  onMonthChange(): void {
    this.updateSelectedMonthLabel();
  }

  /**
   * Handle year selection change
   */
  onYearChange(): void {
    this.updateSelectedMonthLabel();
  }
}
