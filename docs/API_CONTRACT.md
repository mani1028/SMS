# API Contract (Phase 1)

## 📋 Standard Response Format

All API responses follow this structure:

### Success Response (2xx)
```json
{
  "status": true,
  "message": "Operation description",
  "data": {
    // Response payload
  }
}
```

### Error Response (4xx, 5xx)
```json
{
  "status": false,
  "message": "Error description",
  "data": {}
}
```

---

## 🔐 Authentication

### Required Headers
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### Token Format
- JWT token issued on successful login
- Placed in `Authorization` header with `Bearer` prefix
- Expires after 24 hours

---

## 📡 Endpoints

### 1. AUTHENTICATION

#### Register School
```
POST /api/register
```

**Request:**
```json
{
  "school_name": "St. Johns Academy",
  "school_email": "admin@stjohns.com",
  "admin_name": "John Doe",
  "admin_email": "john@stjohns.com",
  "admin_password": "password123"
}
```

**Response (201):**
```json
{
  "status": true,
  "message": "School registered successfully",
  "data": {
    "school_id": 1,
    "message": "School registered successfully",
    "success": true
  }
}
```

**Errors:**
- `400` - Missing required fields
- `400` - School already registered
- `500` - Server error

---

#### Login
```
POST /api/login
```

**Request:**
```json
{
  "email": "john@stjohns.com",
  "password": "password123",
  "school_id": 1
}
```

**Response (200):**
```json
{
  "status": true,
  "message": "Login successful",
  "data": {
    "id": 1,
    "school_id": 1,
    "name": "John Doe",
    "email": "john@stjohns.com",
    "is_active": true,
    "role": {
      "id": 1,
      "school_id": 1,
      "name": "Admin",
      "description": null,
      "permissions": [...]
    },
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "created_at": "2026-02-22T10:30:00",
    "updated_at": "2026-02-22T10:30:00"
  }
}
```

**Errors:**
- `400` - Missing email, password, or school_id
- `401` - Invalid credentials

---

### 2. STUDENT MANAGEMENT

#### Get All Students
```
GET /api/students?page=1&limit=50
```

**Headers:**
```
Authorization: Bearer <TOKEN>
```

**Query Parameters:**
- `page` (optional, default: 1)
- `limit` (optional, default: 50)

**Response (200):**
```json
{
  "status": true,
  "message": "Students retrieved successfully",
  "data": {
    "students": [
      {
        "id": 1,
        "school_id": 1,
        "name": "Alice Johnson",
        "admission_no": "ADM001",
        "class_name": "10-A",
        "email": "alice@example.com",
        "phone": "9876543210",
        "is_active": true,
        "created_at": "2026-02-22T10:30:00",
        "updated_at": "2026-02-22T10:30:00"
      },
      ...
    ],
    "total": 150,
    "pages": 3,
    "current_page": 1
  }
}
```

**Errors:**
- `401` - Unauthorized
- `500` - Server error

---

#### Get Specific Student
```
GET /api/students/{id}
```

**Headers:**
```
Authorization: Bearer <TOKEN>
```

**Response (200):**
```json
{
  "status": true,
  "message": "Student retrieved successfully",
  "data": {
    "id": 1,
    "school_id": 1,
    "name": "Alice Johnson",
    "admission_no": "ADM001",
    "class_name": "10-A",
    "email": "alice@example.com",
    "phone": "9876543210",
    "is_active": true,
    "created_at": "2026-02-22T10:30:00",
    "updated_at": "2026-02-22T10:30:00"
  }
}
```

**Errors:**
- `401` - Unauthorized
- `404` - Student not found
- `500` - Server error

---

#### Create Student (*Admin Only)
```
POST /api/students
```

**Headers:**
```
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

**Request:**
```json
{
  "name": "Bob Wilson",
  "admission_no": "ADM002",
  "class_name": "10-A",
  "email": "bob@example.com",
  "phone": "9876543211"
}
```

**Required Fields:**
- `name` - String
- `admission_no` - String (unique per school)
- `class_name` - String

**Optional Fields:**
- `email` - String
- `phone` - String

**Response (201):**
```json
{
  "status": true,
  "message": "Student created successfully",
  "data": {
    "id": 2,
    "school_id": 1,
    "name": "Bob Wilson",
    "admission_no": "ADM002",
    "class_name": "10-A",
    "email": "bob@example.com",
    "phone": "9876543211",
    "is_active": true,
    "created_at": "2026-02-22T11:00:00",
    "updated_at": "2026-02-22T11:00:00"
  }
}
```

**Errors:**
- `400` - Missing required fields
- `400` - Admission number already exists
- `401` - Unauthorized
- `403` - Admin role required
- `500` - Server error

---

#### Update Student (*Admin Only)
```
PUT /api/students/{id}
```

**Headers:**
```
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json
```

**Request:**
```json
{
  "name": "Bob Wilson Updated",
  "class_name": "10-B",
  "email": "bob.new@example.com"
}
```

**Updateable Fields:**
- `name`
- `class_name`
- `email`
- `phone`
- `is_active` (boolean)

**Response (200):**
```json
{
  "status": true,
  "message": "Student updated successfully",
  "data": {
    "id": 2,
    "school_id": 1,
    "name": "Bob Wilson Updated",
    "admission_no": "ADM002",
    "class_name": "10-B",
    "email": "bob.new@example.com",
    "phone": "9876543211",
    "is_active": true,
    "created_at": "2026-02-22T11:00:00",
    "updated_at": "2026-02-22T11:30:00"
  }
}
```

**Errors:**
- `401` - Unauthorized
- `403` - Admin role required
- `404` - Student not found
- `500` - Server error

---

#### Delete Student (*Admin Only)
```
DELETE /api/students/{id}
```

**Headers:**
```
Authorization: Bearer <ADMIN_TOKEN>
```

**Response (200):**
```json
{
  "status": true,
  "message": "Student deleted successfully",
  "data": {}
}
```

**Errors:**
- `401` - Unauthorized
- `403` - Admin role required
- `404` - Student not found
- `500` - Server error

---

## 🔒 Authentication Requirements

| Endpoint | Public | Auth Required | Role | Notes |
|----------|--------|---------------|------|-------|
| POST /api/register | ✅ | ❌ | - | Anyone can register |
| POST /api/login | ✅ | ❌ | - | Anyone can login |
| GET /api/students | ❌ | ✅ | Any | JWT token required |
| GET /api/students/{id} | ❌ | ✅ | Any | JWT token required |
| POST /api/students | ❌ | ✅ | Admin | Admin only |
| PUT /api/students/{id} | ❌ | ✅ | Admin | Admin only |
| DELETE /api/students/{id} | ❌ | ✅ | Admin | Admin only |

---

## 📊 HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST (resource created) |
| 400 | Bad Request | Invalid input, missing fields |
| 401 | Unauthorized | Invalid/missing JWT token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Database error, unhandled exception |

---

## 🔑 JWT Token Structure

```
Header: {"typ": "JWT", "alg": "HS256"}
Payload: {"sub": "user_id", "iat": ..., "exp": ...}
Signature: HMACSHA256(...)
```

**Token Payload Includes:**
- `sub` (subject): User ID
- `iat` (issued at): Timestamp
- `exp` (expiration): Timestamp (24 hours)

---

## 🔄 Multi-Tenant Isolation

All write/read operations automatically include school isolation:

```
User makes request
    ↓
JWT decoded → user_id extracted
    ↓
User loaded from database
    ↓
User's school_id determined
    ↓
All queries filtered by school_id
    ↓
Only that school's data accessible
```

---

## ⚠️ Error Handling

### Common Error Responses

**Authentication Failed:**
```json
{
  "status": false,
  "message": "Invalid credentials",
  "data": {}
}
```

**Authorization Failed:**
```json
{
  "status": false,
  "message": "Insufficient permissions",
  "data": {}
}
```

**Validation Error:**
```json
{
  "status": false,
  "message": "Missing required fields",
  "data": {}
}
```

**Not Found:**
```json
{
  "status": false,
  "message": "Student not found",
  "data": {}
}
```

---

## 🧪 Example API Workflow

### 1. Register
```bash
POST /api/register
→ 201 Created (school_id: 1)
```

### 2. Login
```bash
POST /api/login
→ 200 OK (token: jwt_token_here)
```

### 3. Create Student
```bash
POST /api/students
Header: Authorization: Bearer jwt_token_here
→ 201 Created (student_id: 1)
```

### 4. Get All Students
```bash
GET /api/students?page=1&limit=10
Header: Authorization: Bearer jwt_token_here
→ 200 OK (list of students)
```

### 5. Update Student
```bash
PUT /api/students/1
Header: Authorization: Bearer jwt_token_here
→ 200 OK (updated student)
```

### 6. Delete Student
```bash
DELETE /api/students/1
Header: Authorization: Bearer jwt_token_here
→ 200 OK (success message)
```

---

**API Version**: 1.0.0  
**Status**: Active  
**Last Updated**: February 22, 2026
