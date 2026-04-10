# Orquestra

Orquestra is a web application for shift planning and fair workload distribution.

---

## 🚀 Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy
- Docker & Docker Compose

---

## 🐳 Run the project with Docker

### 1. Clone the repository

```bash
git clone <REPOSITORY_URL>  
cd orquestra-backend  
```

### 2. Start the application

```bash
docker compose up --build  
```

---

## 🌐 Access the application

- API: http://localhost:8000  
- Swagger documentation: http://localhost:8000/docs  

---

## 🗄️ Database

- PostgreSQL database running in Docker  
- Data is persisted using Docker volumes  
- Tables are created automatically on startup  

---

## 🌱 Database initialization

The database is automatically seeded when the application starts.

Initial data includes:

- Users  
- Employees  
- Schedules  
- Shifts  
- Assignments  

---

## ⚙️ Environment variables

Configured using a `.env` file:

DATABASE_URL=postgresql://postgres:postgres@db:5432/orquestra_db  
SECRET_KEY=your-secret-key  
ALGORITHM=HS256  
ACCESS_TOKEN_EXPIRE_MINUTES=30  

---

## 🔐 Authentication

- JWT-based authentication  
- Password hashing using bcrypt  
- Role-based access control:
  - Admin users  
  - Employee users  

### 🔹 First login flow

- Users created by an administrator are assigned a temporary password  
- These users are required to change their password on their first login  
- The system indicates whether a password change is required through a dedicated flag  
- Once the password is updated, the user can continue using the application normally  

Swagger supports authentication using the **Authorize** button.

---

## 🔐 Authorization & Data Access

The application enforces role-based access control and data filtering.

### Roles

- Admin
  - Full access to all resources
  - Can manage employees, schedules, shifts, and assignments
- Employee
  - Limited access to personal data
  - Can only access:
    - assigned shifts
    - schedules where they have assignments
    - their own workload metrics

### Access behavior

- Data returned by the API is filtered based on the authenticated user
- Unauthorized access attempts return a 403 Forbidden response
- This ensures that employees can only access their own planning context

---

## 👥 Employee onboarding

- Administrators can create an employee and its associated user account in a single operation  
- The process ensures consistency by creating and linking both entities together  
- Duplicate email addresses are not allowed  
- Newly created users are marked to require a password change on first login  

---

## 📅 Schedule management

The application supports full schedule management with role-based access.

### Features

- Create and manage schedules
- Associate shifts with schedules
- Generate planning automatically

### Schedule detail

- Each schedule provides a complete planning overview
- Includes:
  - shifts grouped by date
  - assignments per shift
  - employees assigned to each shift

### Access control

- Admin users can access all schedules
- Employees can only access schedules where they have assigned shifts

### Backend behavior

- Schedule data is returned in a structured format
- All required information (shifts and assignments) is included in a single response
- This reduces the need for multiple API calls and improves consistency

---

## 📊 Planning & Metrics

### 🔹 Planning

- Automatic shift assignment algorithm  
- Support for multiple employees per shift  
- Prevention of duplicate assignments  
- Avoidance of overlapping shifts for the same employee  

### 🔹 Metrics

#### Workload Metrics
- Calculate assigned working hours per employee  
- Filter by custom date ranges  
- Admins can view all employees or filter by employee  
- Employees can only view their own workload  

#### Fairness Metrics
- Evaluate workload distribution within a schedule  
- Metrics based on assigned hours:
  - Total assigned hours  
  - Maximum and minimum assigned hours  
  - Workload gap between employees  

---

## 🧪 Testing

The backend includes automated tests using **pytest**.

### 🔹 Test coverage

- Authentication (login)
- Authorization (role-based access control)
- Employee onboarding (user + employee creation in one step)
- First login password change flow
- Planning service and API
- Metrics endpoints (fairness and workload)

### 🔹 Running tests

Run tests locally:

```bash
pytest
```

### 🔹 Testing setup

- Isolated test database using SQLite
- Dependency overrides for FastAPI
- Reusable fixtures for users, authentication, planning, and metrics
- Tests are fully reproducible and independent from the seeded database

---

## 📌 Current features

- CRUD for all entities:
  - Users  
  - Employees  
  - Schedules  
  - Shifts  
  - Assignments  
- JWT authentication and role-based authorization
- Employee onboarding (user + employee creation in one step)
- First login password change flow
- Automatic shift planning
- Workload and fairness metrics
- Role-based data filtering in API responses
- Structured schedule detail with nested shifts and assignments
- Dockerized environment
- Automatic database setup and seeding