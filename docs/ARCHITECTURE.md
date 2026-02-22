# System Architecture

## 🏗 Overview

School Management System is built using a **three-tier layered architecture** pattern:

```
┌─────────────────────────────────────━─┐
│        Frontend (Presentation)        │
│  HTML, CSS, JavaScript (Vanilla)      │
└──────────────────┬────────────────────┘
                   │ (HTTP/REST)
┌──────────────────┼────────────────────┐
│    API Layer     │ (Flask)            │
│  Routes → Services → Models           │
└──────────────────┼────────────────────┘
                   │ (SQL)
┌──────────────────┼────────────────────┐
│  Database Layer  │ (PostgreSQL)       │
│  ORM (SQLAlchemy)                    │
└────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### 1. Request Flow (Incoming)
```
Client Request
    ↓
Routes (HTTP endpoint handler)
    ↓
Authentication Middleware
    ↓
Service Layer (business logic)
    ↓
Model Layer (database operations)
    ↓
PostgreSQL Database
```

### 2. Response Flow (Outgoing)
```
Database Record
    ↓
Model to Dictionary (to_dict())
    ↓
Service returns result
    ↓
Route formats response
    ↓
Success/Error Response
```

---

## 📦 Component Architecture

### Backend Structure

```
backend/
├── app/
│   ├── __init__.py              # Application Factory
│   │                             # - Creates Flask app
│   │                             # - Initializes extensions
│   │                             # - Registers blueprints
│   │
│   ├── config.py                # Configuration management
│   │                             # - Database settings
│   │                             # - JWT settings
│   │                             # - Environment variables
│   │
│   ├── extensions.py            # Flask extensions
│   │                             # - SQLAlchemy
│   │                             # - JWT Manager
│   │
│   ├── core/
│   │   ├── auth.py              # Authentication decorators
│   │   ├── rbac.py              # Role-based access control
│   │   └── response.py          # Standard response format
│   │
│   ├── models/
│   │   ├── base.py              # Base model with common fields
│   │   ├── school.py            # School (Tenant)
│   │   ├── user.py              # User with password
│   │   ├── role.py              # Role with permissions
│   │   ├── permission.py        # Permission
│   │   └── student.py           # Student
│   │
│   ├── routes/
│   │   ├── auth_routes.py       # /login, /register
│   │   └── student_routes.py    # /students CRUD
│   │
│   ├── services/
│   │   ├── auth_service.py      # Authentication logic
│   │   └── student_service.py   # Student CRUD logic
│   │
│   └── utils/
│       └── helpers.py           # Utility functions
│
├── run.py                       # Application entry point
├── requirements.txt             # Dependencies
└── .env                         # Environment config
```

---

## 📊 Database Schema

### Multi-Tenant Design

```sql
Schools (Tenant)
├── id (PK)
├── name
├── email
└── created_at

Users (Multi-tenant)
├── id (PK)
├── school_id (FK) ← Multi-tenant key
├── name
├── email
├── password_hash
└── role_id (FK)

Roles (Multi-tenant)
├── id (PK)
├── school_id (FK) ← Multi-tenant key
├── name
└── permissions (many-to-many)

Permissions (Global)
├── id (PK)
├── name
└── description

RolePermissions (Junction)
├── role_id (FK, PK)
└── permission_id (FK, PK)

Students (Multi-tenant)
├── id (PK)
├── school_id (FK) ← Multi-tenant key
├── name
├── admission_no
├── class_name
└── is_active
```

### Key Design Decisions

**Multi-Tenant Isolation**:
- Every table (except Permission) includes `school_id`
- Queries always filter by `school_id`
- Unique constraints include `school_id`
- Physical data separation at application level

```python
# Example: Getting students for a specific school
students = Student.query.filter_by(
    school_id=current_user.school_id,
    is_active=True
).all()
```

---

## 🔐 Authentication & Authorization

### Authentication Flow

```
1. User submits email + password + school_id
                ↓
2. AuthService.login() validates credentials
                ↓
3. JWT token generated with user_id
                ↓
4. Token stored in localStorage (frontend)
                ↓
5. Token sent in Authorization header (frontend)
                ↓
6. @token_required decorator validates token
                ↓
7. user_id decoded from token
                ↓
8. User object loaded from database
```

### Authorization (RBAC)

```
Request reaches endpoint
        ↓
@token_required (validates JWT)
        ↓
@role_required('Admin') (checks user role)
        ↓
Service logic executes
        ↓
Multi-tenant filter (school_id check)
```

---

## 🎯 Design Patterns Used

### 1. Application Factory Pattern
```python
def create_app(config_class=Config):
    app = Flask(__name__)
    db.init_app(app)
    jwt.init_app(app)
    # ... register blueprints
    return app
```

### 2. Blueprint Pattern (Modular Routes)
```python
auth_bp = Blueprint('auth', __name__)
@auth_bp.route('/login', methods=['POST'])
def login():
    pass
```

### 3. Service Layer Pattern
```
Routes → Services → Models
```
- Routes handle HTTP
- Services contain business logic
- Models handle database

### 4. Decorator Pattern (Middleware)
```python
@token_required
@role_required('Admin')
def create_student(current_user):
    pass
```

### 5. Repository Pattern
```python
class StudentService:
    @staticmethod
    def create_student(...):
        # Encapsulates database operations
```

---

## 🔄 Request Lifecycle Example

### Creating a Student

```
1. POST /api/students
   ↓ Headers: Authorization: Bearer <token>
   ↓ Body: { name, admission_no, class_name, ... }

2. student_routes.create_student() called
   ↓ @token_required validates JWT

3. Current user loaded from token
   ↓ Verify user belongs to school

4. @role_required('Admin') checks role
   ↓ Ensure user is admin

5. StudentService.create_student() called
   ↓ Validate input
   ↓ Check if admission_no already exists in school

6. Student model created
   ↓ school_id set to current_user.school_id
   ↓ Database INSERT

7. student.to_dict() converts to JSON
   ↓ Standard response format

8. 201 Created response sent
   ↓ Frontend receives and updates UI
```

---

## 🎨 Frontend Architecture

### Template Structure

```html
<!-- Page Structure -->
<header>Navigation</header>
<div class="container">
    <aside>Sidebar</aside>
    <main>Content</main>
</div>
<footer>Footer</footer>

<!-- Scripts loaded in order -->
<script src="api.js">         // API utilities
<script src="auth.js">        // Auth logic
<script src="student.js">     // Student logic
```

### JavaScript Layers

1. **api.js** - Low-level HTTP
   - `apiRequest()` - Generic fetch wrapper
   - JWT token management

2. **auth.js** - Authentication flows
   - Login handler
   - Registration handler
   - Logout

3. **student.js** - Business logic
   - `loadStudents()` - Fetch list
   - `createStudent()` - POST request
   - `updateStudent()` - PUT request
   - `deleteStudent()` - DELETE request
   - Modal management

---

## 📝 Naming Conventions

### Database
- Tables: singular, lowercase `users`, `students`
- Columns: snake_case `created_at`, `school_id`
- Foreign keys: `{table}_id` format

### Backend
- Functions: snake_case `create_student()`
- Classes: PascalCase `StudentService`
- Modules: snake_case `student_routes.py`
- Constants: UPPER_CASE `API_BASE`

### Frontend
- Classes: PascalCase (for CSS): `.btn-primary`
- IDs: camelCase: `studentForm`, `studentTableBody`
- Functions: camelCase `handleLogin()`, `openStudentModal()`

---

## 🚀 Deployment Architecture (Future)

```
┌─────────────────────────────────────────┐
│    CDN (Static files)                   │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│    Nginx (Reverse Proxy)                │
│    - Load balancing                     │
│    - SSL termination                    │
│    - Static file serving                │
└──────────────────┬──────────────────────┘
                   ↓
┌──────────────────┴──────────────────────┐
│    Flask App (Multiple instances)       │
│    - Docker containers                  │
│    - Kubernetes orchestration (optional)│
└──────────────────┬──────────────────────┘
                   ↓
┌──────────────────┴──────────────────────┐
│    PostgreSQL (Primary + Replica)       │
│    - Automated backups                  │
│    - Replication                        │
│    - High availability                  │
└─────────────────────────────────────────┘
```

---

## ✅ Architecture Benefits

- **Scalability**: Separate concerns, easy to add features
- **Maintainability**: Clear module organization
- **Testability**: Service layer can be unit tested
- **Multi-tenancy**: Proper data isolation
- **Security**: Authentication and authorization at every layer
- **Performance**: Efficient database queries with foreign keys
- **Extensibility**: Easy to add new features in Phase 2+

---

**Version**: 1.0.0  
**Last Updated**: February 22, 2026
