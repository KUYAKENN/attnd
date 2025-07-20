import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { Person, FaceEncoding, Attendance } from '../models/person.model';

@Injectable({
  providedIn: 'root'
})
export class PersonService {
  private apiUrl = 'http://localhost:5000/api'; // Flask backend URL
  private personsSubject = new BehaviorSubject<Person[]>([]);
  public persons$ = this.personsSubject.asObservable();

  constructor(private http: HttpClient) {
    this.loadPersons();
  }

  // Person CRUD operations
  getPersons(): Observable<Person[]> {
    return this.http.get<Person[]>(`${this.apiUrl}/persons`);
  }

  getPerson(id: number): Observable<Person> {
    return this.http.get<Person>(`${this.apiUrl}/persons/${id}`);
  }

  createPerson(person: Person): Observable<Person> {
    return this.http.post<Person>(`${this.apiUrl}/persons`, person);
  }

  updatePerson(id: number, person: Person): Observable<Person> {
    return this.http.put<Person>(`${this.apiUrl}/persons/${id}`, person);
  }

  deletePerson(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/persons/${id}`);
  }

  // Face encoding operations
  uploadFaceImage(personId: number, imageFile: File): Observable<FaceEncoding> {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('person_id', personId.toString());
    
    return this.http.post<FaceEncoding>(`${this.apiUrl}/face-encodings`, formData);
  }

  getFaceEncodings(personId: number): Observable<FaceEncoding[]> {
    return this.http.get<FaceEncoding[]>(`${this.apiUrl}/persons/${personId}/face-encodings`);
  }

  // Load persons into subject
  private loadPersons(): void {
    this.getPersons().subscribe(persons => {
      this.personsSubject.next(persons);
    });
  }

  // Refresh persons list
  refreshPersons(): void {
    this.loadPersons();
  }
}
