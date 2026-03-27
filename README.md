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

git clone <REPOSITORY_URL>  
cd orquestra-backend  

### 2. Start the application

docker compose up --build  

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

Swagger supports authentication using the **Authorize** button.

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

## 📌 Current features

- CRUD for all entities:
  - Users  
  - Employees  
  - Schedules  
  - Shifts  
  - Assignments  
- JWT authentication and authorization  
- Automatic shift planning  
- Workload and fairness metrics  
- Dockerized environment  
- Automatic database setup and seeding  