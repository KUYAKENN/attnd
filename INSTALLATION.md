# Face Recognition Attendance System - Installation Guide

## System Requirements

### Hardware Requirements
- **CPU**: Intel Core i5 or AMD Ryzen 5 (minimum), Intel Core i7 or AMD Ryzen 7 (recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space minimum
- **Camera**: USB webcam or IP camera with minimum 720p resolution
- **GPU**: Optional NVIDIA GPU with CUDA support for better performance

### Software Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux Ubuntu 18.04+
- **Python**: 3.8 to 3.11 (3.10 recommended)
- **MySQL**: 8.0 or later
- **Node.js**: 18.x or later (for frontend)
- **npm**: 9.x or later

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/KUYAKENN/attnd.git
cd attnd
```

### 2. Backend Setup

#### 2.1 Create Python Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 2.2 Install Python Dependencies
```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

#### 2.3 Database Setup
1. Install MySQL Server 8.0+
2. Create database and user:
```sql
-- Run in MySQL Workbench or command line
SOURCE setup_database.sql;
```

#### 2.4 Environment Configuration
Create `.env` file in backend folder:
```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=attendance_system

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Face Recognition
ARCFACE_MODEL_PATH=models/buffalo_l
CONFIDENCE_THRESHOLD=0.7

# Camera Settings
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
DETECTION_SIZE=640

# API Configuration
API_PORT=5000
DEBUG_MODE=True
```

### 3. Frontend Setup

#### 3.1 Install Node.js Dependencies
```bash
npm install
```

#### 3.2 Angular Configuration
Update `src/environments/environment.ts`:
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000/api'
};
```

### 4. Start the Application

#### 4.1 Start Backend Server
```bash
cd backend
python app.py
```
Backend will run on: http://localhost:5000

#### 4.2 Start Frontend Development Server
```bash
npm start
```
Frontend will run on: http://localhost:4200

## Troubleshooting

### Common Issues

#### 1. InsightFace Installation Issues
```bash
# If you encounter ONNX runtime issues
pip uninstall onnxruntime
pip install onnxruntime-gpu  # For GPU support
# OR
pip install onnxruntime      # For CPU only
```

#### 2. MySQL Connection Issues
- Ensure MySQL service is running
- Check database credentials in `.env` file
- Verify MySQL port (default: 3306)

#### 3. Camera Access Issues
- Check camera permissions
- Ensure no other applications are using the camera
- Try different camera indices (0, 1, 2, etc.)

#### 4. CORS Issues
- Ensure Flask-CORS is properly configured
- Check frontend API URL configuration

### Performance Optimization

#### For Better Face Recognition Performance:
1. **GPU Acceleration**: Install CUDA and use `onnxruntime-gpu`
2. **Model Optimization**: Use quantized models for faster inference
3. **Camera Resolution**: Use 640x480 for balance between speed and accuracy
4. **Memory Management**: Increase Python memory limits if needed

### Security Considerations

1. **Change Default Passwords**: Update all default credentials
2. **HTTPS Configuration**: Enable SSL/TLS in production
3. **Database Security**: Use strong passwords and restrict access
4. **Firewall Rules**: Configure appropriate network security

## Production Deployment

### Using Gunicorn (Linux/macOS)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Waitress (Windows)
```bash
pip install waitress
waitress-serve --port=5000 app:app
```

### Frontend Production Build
```bash
ng build --prod
```

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │   Database      │
│   Angular 20    │───▶│   Flask + ArcFace│───▶│   MySQL 8.0     │
│   Port: 4200    │    │   Port: 5000     │    │   Port: 3306    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐               │
         └─────────────▶│   Camera System │               │
                        │   USB/IP Camera │               │
                        └─────────────────┘               │
                                 │                        │
                        ┌─────────────────┐               │
                        │   File Storage  │◀──────────────┘
                        │   Face Models   │
                        └─────────────────┘
```

## Support and Documentation

- **GitHub Issues**: Report bugs and feature requests
- **Wiki**: Detailed API documentation
- **Security**: See SECURITY_MEASURES.md for security guidelines
- **Contributing**: See CONTRIBUTING.md for development guidelines

---

**Last Updated**: July 21, 2025
**Version**: 2.1.0
**Minimum Python Version**: 3.8
**Recommended Python Version**: 3.10
