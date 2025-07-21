import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css'
})
export class NavbarComponent {
  isMenuOpen = false;
  private readonly ADMIN_PASSWORD = 'qunabydevs7719';

  constructor(private router: Router) {}

  toggleMenu(): void {
    this.isMenuOpen = !this.isMenuOpen;
  }

  closeMenu(): void {
    this.isMenuOpen = false;
  }

  navigateToProtectedRoute(route: string): void {
    const password = prompt('Enter admin password to access this section:');
    
    if (password === this.ADMIN_PASSWORD) {
      this.router.navigate([route]);
      this.closeMenu();
    } else if (password !== null) { // null means user cancelled
      alert('Incorrect password!');
    }
  }

  navigateToLive(): void {
    this.router.navigate(['/live-attendance']);
    this.closeMenu();
  }
}
