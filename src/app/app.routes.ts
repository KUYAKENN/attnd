import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { Registration } from './components/registration/registration';
import { AttendanceComponent } from './components/attendance/attendance.component';
import { EmployeeTable } from './components/employee-table/employee-table';
import { LiveAttendanceComponent } from './live-attendance/live-attendance';
import { ExportComponent } from './components/export/export.component';

export const routes: Routes = [
  { path: '', component: LiveAttendanceComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'registration', component: Registration },
  { path: 'attendance', component: AttendanceComponent },
  { path: 'employees', component: EmployeeTable },
  { path: 'live-attendance', component: LiveAttendanceComponent },
  { path: 'export', component: ExportComponent },
  { path: '**', redirectTo: '/live-attendance' }
];
