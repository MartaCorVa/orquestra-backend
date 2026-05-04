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
- Contracts  
- Schedules  
- Shifts  
- Assignments  

---

## ⚙️ Environment variables

Configuration is managed using a `.env` file.

You can use `.env.example` as a template.

### Required variables

```env
DATABASE_URL=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
SECRET_KEY=
SONAR_TOKEN=
```

### Notes
- `.env` file is not included in the repository for security reasons
- `.env.example` provides the required structure
- `SONAR_TOKEN` is optional and only required for SonarQube analysis

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

## 📄 Contract management

Employee contracts are managed as a separate resource.

### Features

- Each employee can have multiple contracts  
- Only one contract can be active at a time  
- Contracts define:
  - weekly working hours  
  - daily working hours  
  - minimum days off per week  
  - working days (Monday to Sunday)  
  - optional fixed schedule (start and end time)  

### Behavior

- Contracts are created and managed independently from employees  
- When a contract is activated:
  - any previously active contract for that employee is automatically deactivated  
- Contracts can be updated, activated, or deleted without affecting employee data  

This separation improves flexibility and allows tracking contract changes over time.

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

## ⏱️ Shift management

Shifts are defined using precise datetime intervals, allowing support for overnight and cross-day shifts.

### Features

- Shifts use:
  - `start_datetime`
  - `end_datetime`
- Support for shifts crossing midnight (e.g., 22:00 → 04:00)
- Optional employee assignment at creation time
- Ability to assign, reassign, or remove employees from shifts

### Recurrent shift creation

The system supports creating shifts in bulk using a date range and selected weekdays.

#### Features

- Create multiple shifts across a date range
- Select specific weekdays (e.g., Monday to Friday)
- Define a common time range for all generated shifts
- Optionally assign an employee to all generated shifts

#### Behavior

- For each matching day in the selected range:
  - If no shift exists → a new shift is created
  - If a shift already exists:
    - no duplicate shift is created
    - the employee is assigned to the existing shift (if provided)

- Duplicate assignments are prevented:
  - the same employee will not be assigned twice to the same shift

#### Validation

- Start date must be before end date
- End time must be later than start time
- At least one weekday must be selected
- If an employee is provided:
  - the employee must exist
  - the employee must be active
  - the employee must have an active contract
  - assignment must respect all contract constraints:
    - allowed working days  
    - maximum daily working hours  
    - maximum weekly working hours  
    - minimum rest period (12 hours)  
    - minimum days off per week  
    - optional fixed schedule constraints  

If any validation fails, the operation is rejected with detailed error messages.

#### Example use cases

- Create shifts Monday–Friday for a full month
- Create shifts only on specific days (e.g., Tue–Thu)
- Assign a single employee to a recurring pattern of shifts

### Validation rules

All shift operations (manual creation, update, and automatic planning) share the same validation logic:

- End datetime must be later than start datetime  
- Shift must belong to the selected schedule range  
- No overlapping shifts for the same employee  
- Minimum rest period of 12 hours between shifts  
- Respect of maximum weekly working hours defined in the employee's active contract  
- Respect of maximum daily working hours defined in the employee's active contract  
- Respect of allowed working days defined in the employee's active contract  
- Recurrent shift creation also validates contract working days before creating or assigning shifts
- Respect of minimum days off per week  
- Optional fixed schedule constraints (start and end time windows)  

Validation errors are aggregated and returned together to provide clear feedback.

---

## 📊 Planning & Metrics

### 🔹 Planning

- Automatic shift assignment algorithm  
- Minimum coverage per shift (at least one employee per shift)  
- Prevention of duplicate assignments  

- Contract-driven assignment:
  - Only employees with an active contract are considered  
  - Assignments must respect:
    - allowed working days  
    - maximum daily working hours  
    - maximum weekly working hours  
    - minimum rest period (12 hours)  
    - minimum days off per week  
    - optional fixed schedule constraints  

- Priority-based assignment:
  - Employees are prioritized based on:
    - remaining weekly hours to fulfill  
    - contract workload (full-time vs part-time)  
    - number of already assigned working days  

- Planning results include detailed feedback:
  - Successfully created assignments  
  - Shifts that could not be assigned (minimum coverage not met)  
  - Employees below their contract target hours  
  - Total missing contract hours required to fulfill all contracts  
  - Per-employee validation errors explaining why assignment was not possible

This ensures that planning is automatic, explainable, and aligned with real-world contract constraints.

Additionally, the planning system does not rely on a fixed number of employees per shift.

- Each shift is covered by at least one employee when possible  
- Additional assignments are created only if they help fulfill weekly contract hours  
- If available shifts are insufficient, the system reports the missing hours required  

This approach makes planning contract-hour driven rather than fixed-staffing driven.

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

## 📊 Code Quality (SonarQube)

The project includes static code analysis using **SonarQube**.

### 🔹 Requirements

- SonarQube running locally (default: http://localhost:9000)
- A valid `SONAR_TOKEN`

### 🔹 Generate coverage report

```bash
pytest --cov=app --cov=main --cov-report=xml --cov-report=term-missing --cov-config=.coveragerc
```

This generates the `coverage.xml` file required by SonarQube.

### 🔹 Run analysis

```bash
sonar-scanner
```

### 🔹 Notes

- The `coverage.xml` file is ignored in `.gitignore`
- The analysis uses the configuration defined in `sonar-project.properties`

---

## 📌 Current features

- CRUD for all entities:
  - Users  
  - Employees  
  - Contracts  
  - Schedules  
  - Shifts  
  - Assignments  
- JWT authentication and role-based authorization
- Employee onboarding (user + employee creation in one step)
- First login password change flow
- Automatic shift planning with contract-hour-driven allocation:
  - Minimum one employee per shift  
  - Additional assignments based on remaining contract hours  
  - No overlapping shifts  
  - Minimum rest period enforcement  
  - Daily and weekly hour limits per employee  
- Explainable planning results (assignment success and failure reasons)  
- Workload and fairness metrics
- Role-based data filtering in API responses
- Structured schedule detail with nested shifts and assignments
- Dockerized environment
- Automatic database setup and seeding
- Contract-based workforce management:
  - Multiple contracts per employee  
  - Active contract selection  
  - Planning driven by contract constraints  
- Contract-aware planning with advanced constraints:
  - Working day validation  
  - Daily and weekly hour limits  
  - Minimum rest enforcement  
  - Minimum days off enforcement  
  - Optional fixed schedule validation  
- Priority-based assignment to maximize contract hour fulfillment
- Planning feedback with contract fulfillment insights:
  - Employees below target hours  
  - Total missing contract hours  
  - Guidance for creating additional shifts
- Recurrent shift creation:
  - Bulk creation of shifts across date ranges  
  - Weekday-based generation  
  - Automatic reuse of existing shifts  
  - Contract-aware validation for employee assignments  

--- 

## 🧠 Design considerations

The system centralizes shift validation logic in a dedicated service layer.

- The same validation rules are reused across:
  - Manual shift creation  
  - Shift updates  
  - Automatic planning  

This ensures consistency, reduces duplication, and improves maintainability.

The planning system also provides explainable results, allowing users to understand why certain assignments could not be performed.

Contract management is decoupled from employee management:

- Contracts are handled as independent resources  
- This allows tracking contract history and changes over time  
- Planning logic relies on the active contract, improving flexibility and scalability  

The planning algorithm prioritizes fulfilling contract hours while respecting all scheduling constraints, providing a balance between fairness and feasibility.

## 🔐 Security notes

- Never commit `.env` files
- Always use `.env.example` for sharing configuration
- Keep secrets such as `SONAR_TOKEN` private