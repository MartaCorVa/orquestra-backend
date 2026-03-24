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

## 📌 Current features

- CRUD for all entities:
  - Users  
  - Employees  
  - Schedules  
  - Shifts  
  - Assignments  
- Dockerized environment  
- Automatic database setup and seeding  