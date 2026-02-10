# Caribou Coffee Backend API

## Overview
This is a professional backend API built with **FastAPI**, **PostgreSQL**, and **Docker**.
It features Role-Based Access Control (RBAC), JWT Authentication, and automated weekly KPI reports.

## Tech Stack
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy (Async) + Alembic for migrations
- **Authentication**: JWT (JSON Web Tokens)
- **Containerization**: Docker & Docker Compose

## Features
- **User Management**: Admin, Auditor, Viewer roles.
- **Audit System**: Create, View, and Delete Audits linked to specific Coffees.
- **KPI Dashboard**: Aggregated metrics for performance analysis.
- **Role-Based Access**:
  - **Admin**: Full access to all audits.
  - **Auditor**: Can create and view their own audits.
  - **Viewer**: View-only access restricted to their assigned Coffee location.
- **Weekly Reporting**: Automated email reports sent via background scheduler.

## Setup & specific Steps

### 1. Prerequisites
- Docker and Docker Compose installed.

### 2. Run with Docker
### 2. Run with Docker
```bash
docker-compose up --build
```
The API will be available at `http://localhost:8008`.

### 3. API Documentation
After running the container, access the interactive API docs at:
- **Swagger UI**: `http://localhost:8008/docs`
- **ReDoc**: `http://localhost:8008/redoc`

### 4. Database Migrations (Manual)
To apply schema changes:
1. Enter the container: `docker-compose exec web bash`
2. Initialize Alembic (first time): `alembic init alembic`
3. Configure `alembic.ini` to use `sqlalchemy.url = postgresql+asyncpg://postgres:postgres@db/caribou`
4. Create migration: `alembic revision --autogenerate -m "Initial migration"`
5. Apply migration: `alembic upgrade head`

## Project Structure
```
app/
├── api/             # API Endpoints (v1)
├── core/            # Config & Security
├── db/              # Database session & Base classes
├── models/          # SQLAlchemy Models
├── schemas/         # Pydantic Schemas
├── services/        # Business Logic (Email, Scheduler)
└── main.py          # Application Entry Point
```
