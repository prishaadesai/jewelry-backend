# Jewelry Production Management System - Backend API

A comprehensive FastAPI backend for managing jewelry production workflows, tracking jobs, workers, and material loss across production stages.

## Features

- **Role-Based Access Control**: Owner and worker roles with specific permissions
- **Job Management**: Create, track, and manage jewelry production jobs
- **Worker Task Assignment**: Assign jobs to workers with stage-specific tracking
- **Real-Time Loss Tracking**: Automatic calculation of material loss at each stage
- **Performance Reports**: Worker performance and material consumption analytics
- **Secure Authentication**: JWT-based authentication with password hashing

## Tech Stack

- **FastAPI**: High-performance Python web framework
- **Supabase**: PostgreSQL database with real-time capabilities
- **Pydantic**: Data validation and serialization
- **JWT**: Secure token-based authentication
- **Render**: Cloud deployment platform

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in the root directory:
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SECRET_KEY=your_secret_key_for_jwt_tokens
```

### 2. Supabase Database Setup

1. Create a Supabase project at https://supabase.com
2. Run the SQL schema from `schema.sql` in the Supabase SQL editor
3. Copy your project URL and anon key to `.env`

### 3. Local Development

Install dependencies
```
pip install -r requirements.txt
```
Run the server
```
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```


API will be available at http://localhost:8000

API Documentation: http://localhost:8000/docs

### 4. Deploy to Render

1. Push code to GitHub repository
2. Connect repository to Render
3. Render will auto-detect `render.yaml` configuration
4. Add environment variables in Render dashboard:
   - SUPABASE_URL
   - SUPABASE_KEY
   - SECRET_KEY

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user (owner only)
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user profile

### User Management (Owner Only)
- `GET /api/users` - List all users
- `GET /api/users/{user_id}` - Get user details
- `PUT /api/users/{user_id}` - Update user
- `DELETE /api/users/{user_id}` - Delete user

### Job Management
- `POST /api/jobs` - Create new job (owner only)
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{job_id}` - Get job details with history
- `PUT /api/jobs/{job_id}` - Update job (owner only)
- `POST /api/jobs/{job_id}/assign` - Assign job to worker (owner only)

### Worker Operations
- `GET /api/worker/tasks` - Get assigned tasks
- `POST /api/worker/complete-task` - Complete assigned task

### Reports & Analytics
- `GET /api/reports/worker-performance` - Worker performance report
- `GET /api/reports/job-summary` - Overall job statistics
- `GET /api/reports/material-consumption` - Material consumption by category

## Workflow Example

1. **Owner creates job**: POST `/api/jobs` with design_no, item_category, initial_weight
2. **Owner assigns to caster**: POST `/api/jobs/{job_id}/assign` with worker_id and stage
3. **Caster views task**: GET `/api/worker/tasks`
4. **Caster completes**: POST `/api/worker/complete-task` with returned_weight
5. **System calculates loss** and updates job automatically
6. **Owner assigns next stage**: Repeat assignment for filer, setter, polisher
7. **Owner views reports**: GET `/api/reports/worker-performance`

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- Role-based authorization
- Input validation with Pydantic
- SQL injection prevention via Supabase client

## Database Schema

- **users**: User accounts with roles
- **jobs**: Jewelry production jobs
- **transactions**: Stage-specific weight transactions

All tables include proper foreign keys, indexes, and constraints for data integrity.