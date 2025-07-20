import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Person } from '../../models/person.model';
import { PersonService } from '../../services/person.service';
import { AttendanceService } from '../../services/attendance.service';

@Component({
  selector: 'app-employee-table',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './employee-table.component.html',
  styleUrls: ['./employee-table.component.css']
})
export class EmployeeTableComponent implements OnInit {
  persons: Person[] = [];
  filteredPersons: Person[] = [];
  paginatedPersons: Person[] = [];
  attendanceData: { [key: number]: any[] } = {};
  
  // Filters
  searchTerm: string = '';
  selectedDepartment: string = '';
  selectedStatus: string = '';
  sortBy: string = 'name';
  sortDirection: 'asc' | 'desc' = 'asc';
  
  // Pagination
  currentPage: number = 1;
  itemsPerPage: number = 10;
  totalPages: number = 0;
  
  // Data for filters
  departments: string[] = [];
  
  // Date range for attendance data
  startDate: string = new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0];
  endDate: string = new Date().toISOString().split('T')[0];
  
  // Loading state
  isLoading: boolean = false;
  
  // Message display
  message: string = '';
  messageType: 'success' | 'error' | 'info' = 'info';

  constructor(
    private personService: PersonService,
    private attendanceService: AttendanceService
  ) {}

  ngOnInit() {
    this.loadPersons();
  }

  async loadPersons() {
    try {
      this.isLoading = true;
      
      // Subscribe to the observable to get persons
      this.personService.getPersons().subscribe({
        next: (persons) => {
          this.persons = persons;
          this.updateDepartments();
          this.loadAttendanceData();
          this.applyFilters();
        },
        error: (error) => {
          console.error('Error loading persons:', error);
          this.showMessage('Error loading employees', 'error');
        }
      });
    } catch (error) {
      console.error('Error loading persons:', error);
      this.showMessage('Error loading employees', 'error');
    } finally {
      this.isLoading = false;
    }
  }

  updateDepartments() {
    const deptSet = new Set(this.persons.map(p => p.department).filter(d => d !== undefined && d !== null));
    this.departments = Array.from(deptSet) as string[];
  }

  async loadAttendanceData() {
    for (const person of this.persons) {
      if (person.id) {
        try {
          // For now, use mock data until we implement the actual service method
          this.attendanceData[person.id] = [];
        } catch (error) {
          console.error(`Error loading attendance for ${person.name}:`, error);
          this.attendanceData[person.id] = [];
        }
      }
    }
  }

  applyFilters() {
    this.filteredPersons = this.persons.filter(person => {
      const matchesSearch = !this.searchTerm || 
        person.name.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        person.email?.toLowerCase().includes(this.searchTerm.toLowerCase());
      
      const matchesDepartment = !this.selectedDepartment || person.department === this.selectedDepartment;
      const matchesStatus = !this.selectedStatus || 
        (person.status === (this.selectedStatus === 'active' ? 'active' : 'inactive'));
      
      return matchesSearch && matchesDepartment && matchesStatus;
    });

    this.applySorting();
    this.updatePagination();
  }

  applySorting() {
    this.filteredPersons.sort((a, b) => {
      let valueA: any, valueB: any;
      
      switch (this.sortBy) {
        case 'name':
          valueA = a.name;
          valueB = b.name;
          break;
        case 'email':
          valueA = a.email || '';
          valueB = b.email || '';
          break;
        case 'department':
          valueA = a.department || '';
          valueB = b.department || '';
          break;
        case 'status':
          valueA = a.status;
          valueB = b.status;
          break;
        case 'attendance':
          valueA = this.getAttendanceRate(a.id!);
          valueB = this.getAttendanceRate(b.id!);
          break;
        case 'registration_date':
          valueA = new Date(a.registration_date || 0);
          valueB = new Date(b.registration_date || 0);
          break;
        default:
          valueA = a.name;
          valueB = b.name;
      }

      if (valueA < valueB) return this.sortDirection === 'asc' ? -1 : 1;
      if (valueA > valueB) return this.sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }

  updatePagination() {
    this.totalPages = Math.ceil(this.filteredPersons.length / this.itemsPerPage);
    this.currentPage = Math.min(this.currentPage, this.totalPages || 1);
    
    const startIndex = (this.currentPage - 1) * this.itemsPerPage;
    const endIndex = startIndex + this.itemsPerPage;
    this.paginatedPersons = this.filteredPersons.slice(startIndex, endIndex);
  }

  getAttendanceCount(personId: number): number {
    const attendance = this.attendanceData[personId] || [];
    return new Set(attendance.map(a => new Date(a.check_in_time!).toDateString())).size;
  }

  getAttendanceRate(personId: number): number {
    const totalDays = Math.ceil((new Date(this.endDate).getTime() - new Date(this.startDate).getTime()) / (1000 * 60 * 60 * 24));
    const attendedDays = this.getAttendanceCount(personId);
    return totalDays > 0 ? (attendedDays / totalDays) * 100 : 0;
  }

  getTotalHours(personId: number): number {
    const attendance = this.attendanceData[personId] || [];
    return attendance.reduce((total, record) => {
      if (record.check_in_time && record.check_out_time) {
        const checkIn = new Date(record.check_in_time);
        const checkOut = new Date(record.check_out_time);
        const hours = (checkOut.getTime() - checkIn.getTime()) / (1000 * 60 * 60);
        return total + hours;
      }
      return total;
    }, 0);
  }

  getStatusClass(status: string): string {
    return status === 'active' ? 'status-active' : 'status-inactive';
  }

  formatDateTime(dateString?: string): string {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  }

  async deletePerson(person: Person) {
    if (confirm(`Are you sure you want to delete ${person.name}?`)) {
      try {
        await this.personService.deletePerson(person.id!);
        await this.loadPersons();
        this.showMessage('Employee deleted successfully', 'success');
      } catch (error) {
        console.error('Error deleting person:', error);
        this.showMessage('Error deleting employee', 'error');
      }
    }
  }

  async togglePersonStatus(person: Person) {
    try {
      const newStatus = person.status === 'active' ? 'inactive' as const : 'active' as const;
      const updatedPerson: Person = { ...person, status: newStatus };
      await this.personService.updatePerson(person.id!, updatedPerson);
      person.status = newStatus;
      this.showMessage(`Employee ${newStatus === 'active' ? 'activated' : 'deactivated'} successfully`, 'success');
    } catch (error) {
      console.error('Error updating person status:', error);
      this.showMessage('Error updating employee status', 'error');
    }
  }

  editPerson(person: Person) {
    // TODO: Implement edit functionality - could open a modal or navigate to edit page
    console.log('Edit person:', person);
    this.showMessage('Edit functionality coming soon', 'info');
  }

  exportToCSV() {
    const headers = [
      'ID',
      'Name', 
      'Email',
      'Employee ID',
      'Department',
      'Status',
      'Attendance Rate (%)',
      'Days Attended',
      'Total Hours'
    ];

    const data = this.filteredPersons.map(person => [
      person.id || '',
      person.name,
      person.email || '',
      '', // Employee ID not in current model
      person.department || '',
      person.status === 'active' ? 'Active' : 'Inactive',
      this.getAttendanceRate(person.id!).toFixed(1),
      this.getAttendanceCount(person.id!).toString(),
      this.getTotalHours(person.id!).toFixed(1)
    ]);

    const csvContent = [headers, ...data]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `employees_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  sort(column: string) {
    if (this.sortBy === column) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortBy = column;
      this.sortDirection = 'asc';
    }
    this.applyFilters();
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.updatePagination();
    }
  }

  onFiltersChange() {
    this.currentPage = 1;
    this.applyFilters();
  }

  onDateRangeChange() {
    this.loadAttendanceData();
  }

  showMessage(text: string, type: 'success' | 'error' | 'info' = 'info') {
    this.message = text;
    this.messageType = type;
    setTimeout(() => {
      this.message = '';
    }, 5000);
  }
}
