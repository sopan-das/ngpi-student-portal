# Smart Student Management Portal

A secure, modern student portal for college students with admin approval system.

## Features
- Student registration with pending approval
- Admin approval/rejection of students
- Student dashboard with modules: Notice, Results, Class Routine, Exam Routine, Academic Calendar, Study Materials, Teachers, Gallery
- Admin dashboard with full CRUD for all modules
- File uploads (PDF/Images) with organized storage
- Secure authentication with password hashing
- Role-based access control

## Technology Stack
- Backend: Flask (Python)
- Frontend: Bootstrap 5, HTML, CSS, JavaScript
- Database: PostgreSQL
- ORM: SQLAlchemy
- Authentication: Flask-Login

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Set up PostgreSQL database and update `.env` with DATABASE_URL
6. Run: `python run.py`

## Default Admin
Create admin manually via shell or use Flask shell to add a user.

## Usage
- Visit `/` for landing page.
- Students register and wait for admin approval.
- Admin logs in (admin credentials must be created in database) and manages students and content.

## Folder Structure
See project documentation for full structure.