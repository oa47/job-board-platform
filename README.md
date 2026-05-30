# Job Board Platform - README

## Project Structure
- **jobs/**: Main job listings app with Job model
- **users/**: User authentication and profile management
- **applications/**: Job application tracking
- **jobboard/**: Main project configuration

## Setup Instructions

### 1. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser
```bash
python manage.py createsuperuser
```

### 5. Run Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000/` to see the application.
Visit `http://localhost:8000/admin/` to manage jobs and applications.

## Features
- Browse job listings
- View detailed job information
- Apply to jobs (admin panel)
- User profiles with resume upload
- Job applications tracking
- Admin interface for managing jobs and applications

## Models
- **User**: Custom user model with role (employer/candidate)
- **Profile**: User profile with bio, resume, and profile picture
- **Job**: Job listings with salary range, job type, and employer
- **Application**: Job applications with status tracking
