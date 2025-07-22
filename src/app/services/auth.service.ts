import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly ADMIN_PASSWORD = 'qunabydevs7719';
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(false);
  private sessionTimeout: any;

  constructor() {
    // Check if user is already authenticated (with session timeout)
    const lastAuth = localStorage.getItem('lastAuthTime');
    if (lastAuth) {
      const timeDiff = Date.now() - parseInt(lastAuth);
      // Session valid for 30 minutes
      if (timeDiff < 30 * 60 * 1000) {
        this.isAuthenticatedSubject.next(true);
        this.setSessionTimeout();
      } else {
        this.logout();
      }
    }
  }

  get isAuthenticated$(): Observable<boolean> {
    return this.isAuthenticatedSubject.asObservable();
  }

  get isAuthenticated(): boolean {
    return this.isAuthenticatedSubject.value;
  }

  authenticate(password: string): boolean {
    if (password === this.ADMIN_PASSWORD) {
      this.isAuthenticatedSubject.next(true);
      localStorage.setItem('lastAuthTime', Date.now().toString());
      this.setSessionTimeout();
      return true;
    }
    return false;
  }

  logout(): void {
    this.isAuthenticatedSubject.next(false);
    localStorage.removeItem('lastAuthTime');
    if (this.sessionTimeout) {
      clearTimeout(this.sessionTimeout);
    }
  }

  private setSessionTimeout(): void {
    if (this.sessionTimeout) {
      clearTimeout(this.sessionTimeout);
    }
    // Auto logout after 30 minutes
    this.sessionTimeout = setTimeout(() => {
      this.logout();
    }, 30 * 60 * 1000);
  }

  requestAccess(): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.isAuthenticated) {
        resolve(true);
        return;
      }

      const password = prompt('Enter admin password to access this section:');
      if (password && this.authenticate(password)) {
        resolve(true);
      } else {
        alert('Incorrect password!');
        resolve(false);
      }
    });
  }
}
