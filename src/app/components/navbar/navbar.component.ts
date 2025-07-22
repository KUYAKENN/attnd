import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css'
})
export class NavbarComponent implements OnInit {
  isMenuOpen = false;
  currentRoute = '';
  private readonly ADMIN_PASSWORD = 'qunabydevs7719';

  constructor(private router: Router) {}

  ngOnInit(): void {
    // Track route changes to update active state
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: NavigationEnd) => {
        this.currentRoute = event.urlAfterRedirects;
      });
    
    // Set initial route
    this.currentRoute = this.router.url;
  }

  /**
   * Check if a route is currently active
   */
  isRouteActive(route: string): boolean {
    if (route === '/live-attendance') {
      return this.currentRoute === '/' || this.currentRoute === '/live-attendance';
    }
    return this.currentRoute === route;
  }

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
