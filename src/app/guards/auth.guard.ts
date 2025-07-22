import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  async canActivate(): Promise<boolean> {
    const hasAccess = await this.authService.requestAccess();
    
    if (!hasAccess) {
      // Redirect to live attendance if access denied
      this.router.navigate(['/live-attendance']);
      return false;
    }
    
    return true;
  }
}
