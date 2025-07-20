import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Person } from '../../models/person.model';
import { PersonService } from '../../services/person.service';
import { AttendanceService } from '../../services/attendance.service';

@Component({
  selector: 'app-employee-table',
  imports: [CommonModule, FormsModule],
  templateUrl: './employee-table.html',
  styleUrl: './employee-table.css'
})
export class EmployeeTable implements OnInit {
  persons: Person[] = [];
  filteredPersons: Person[] = [];
  paginatedPersons: Person[] = [];
  
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

  loadPersons() {
    this.isLoading = true;
    this.personService.getPersons().subscribe({
      next: (persons) => {
        this.persons = persons;
        this.updateDepartments();
        this.applyFilters();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading persons:', error);
        this.showMessage('Error loading employees', 'error');
        this.isLoading = false;
      }
    });
  }

  updateDepartments() {
    const deptSet = new Set(this.persons.map(p => p.department).filter(d => d));
    this.departments = Array.from(deptSet) as string[];
  }

  applyFilters() {
    this.filteredPersons = this.persons.filter(person => {
      const matchesSearch = !this.searchTerm || 
        person.name.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        (person.email && person.email.toLowerCase().includes(this.searchTerm.toLowerCase()));
      
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
        this.loadPersons();
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
    console.log('Edit person:', person);
    this.showMessage('Edit functionality coming soon', 'info');
  }

  exportToCSV() {
    const headers = ['ID', 'Name', 'Email', 'Department', 'Status', 'Registered'];
    const data = this.filteredPersons.map(person => [
      person.id || '',
      person.name,
      person.email || '',
      person.department || '',
      person.status === 'active' ? 'Active' : 'Inactive',
      this.formatDateTime(person.registration_date)
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

  showMessage(text: string, type: 'success' | 'error' | 'info' = 'info') {
    this.message = text;
    this.messageType = type;
    setTimeout(() => {
      this.message = '';
    }, 5000);
  }
}
