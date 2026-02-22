# School Management System - Phase 1

**Multi-Tenant SaaS Platform for Educational Institutions**

A professional, production-ready foundation for a school management system with multi-tenant support, JWT authentication, dynamic RBAC, and student management.

---

## 🚀 Features (Phase 1)

- ✅ **Multi-Tenant Architecture** - Complete data isolation per school
- ✅ **JWT Authentication** - Secure login system
- ✅ **Dynamic RBAC** - Role-based access control with permissions
- ✅ **Student CRUD** - Complete student management
- ✅ **Admin Dashboard** - Overview and quick access
- ✅ **Clean Architecture** - Layered separation of concerns

---

## 🏗 Tech Stack

### Backend
- **Python 3.10+** with Flask
- **SQLAlchemy** ORM
- **Flask-JWT-Extended** for authentication
- **PostgreSQL** database
- **python-dotenv** for configuration

### Frontend
- **HTML5** markup
- **CSS3** styling
- **Vanilla JavaScript** (Fetch API)
- **Responsive Design**

---

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 12+
- pip (Python package manager)

---

## 🔧 Installation & Setup

### 1. Clone and Navigate

```bash
cd backend
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database

Update `.env` with your PostgreSQL credentials:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/schoolms
JWT_SECRET_KEY=your-secret-key-change-in-production
```

### 5. Create Database

```bash
psql -U postgres -c "CREATE DATABASE schoolms;"
```

### 6. Run the Application

```bash
python run.py
```

API will be available at: `http://localhost:5000/api`

---

## 📂 Project Structure

```
schoolms/
├── backend/
│   ├── app/
│   │   ├── core/          # Auth, RBAC, Response handlers
│   │   ├── models/        # Database models
│   │   ├── routes/        # API endpoints
│   │   ├── services/      # Business logic
│   │   ├── utils/         # Helpers
│   │   ├── __init__.py    # Application factory
│   │   ├── config.py      # Configuration
│   │   ├── extensions.py  # Flask extensions
│   │
│   ├── run.py             # Entry point
│   ├── requirements.txt   # Dependencies
│   ├── .env               # Environment config
│
├── frontend/
│   ├── assets/
│   │   ├── css/           # Stylesheets
│   │   ├── js/            # JavaScript
│   ├── auth/              # Login/Register pages
│   ├── admin/             # Dashboard pages
│   ├── index.html         # Home page
│
├── docs/                  # Documentation
├── README.md
├── .gitignore
```

---

## 🔌 API Endpoints

### Authentication

```
POST /api/register     - Register new school
POST /api/login        - User login
```

### Students

```
GET    /api/students           - Get all students
GET    /api/students/<id>      - Get specific student
POST   /api/students           - Create student (Admin only)
PUT    /api/students/<id>      - Update student (Admin only)
DELETE /api/students/<id>      - Delete student (Admin only)
```

All endpoints require JWT token (except `/register` and `/login`).

---

## 🔐 Authentication Flow

1. **Register School**: Create school and admin account
2. **Login**: Send email, password, school_id
3. **Receive JWT Token**: Store in localStorage
4. **API Calls**: Include token in Authorization header
5. **Logout**: Clear localStorage

---

## 👤 User Roles

- **Admin** - Full system access
- **Teacher** - Can view students (future use)
- **Student** - Limited permissions (future use)

---

## 📝 Standard Response Format

### Success
```json
{
  "status": true,
  "message": "Operation successful",
  "data": { ... }
}
```

### Error
```json
{
  "status": false,
  "message": "Error description",
  "data": {}
}
```

---

## 🧪 Testing the System

### 1. Register a School

```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "school_name": "St. Johns Academy",
    "school_email": "admin@stjohns.com",
    "admin_name": "John Doe",
    "admin_email": "john@stjohns.com",
    "admin_password": "password123"
  }'
```

### 2. Login

Get the `school_id` from registration response, then:

```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@stjohns.com",
    "password": "password123",
    "school_id": 1
  }'
```

### 3. Use JWT Token

Add to all subsequent requests:

```
Authorization: Bearer <token>
```

---

## 🌐 Frontend Usage

1. **Home**: `http://localhost:8000/frontend/index.html`
2. **Register**: `http://localhost:8000/frontend/auth/register.html`
3. **Login**: `http://localhost:8000/frontend/auth/login.html`
4. **Dashboard**: `http://localhost:8000/frontend/admin/dashboard.html`
5. **Students**: `http://localhost:8000/frontend/admin/students.html`

**Note**: Run a simple HTTP server in frontend folder:

```bash
cd frontend
python -m http.server 8000
```

---

## 🔒 Security Considerations

- Passwords are hashed using `werkzeug.security`
- JWT tokens expire after 24 hours
- All endpoints validate school_id for multi-tenancy
- Sensitive data is not exposed in responses
- CORS should be configured for production

---

## 📚 Documentation

See docs/ folder for:
- `FEATURES.md` - Detailed feature list
- `ARCHITECTURE.md` - System architecture
- `API_CONTRACT.md` - API specifications
- `FUTURE_UPGRADE_PLAN.md` - Roadmap

---

## 🚀 Next Steps (Phase 2+)

- Teacher Management
- Class System
- Attendance Tracking
- Fees Management
- Exam System
- Docker support
- Production deployment

---

## 📝 License

This project is confidential and proprietary.

---

## 👥 Support

For issues or questions, contact the development team.

**Version**: 1.0.0 Phase 1  
**Created**: February 22, 2026  
**Status**: Active Development
