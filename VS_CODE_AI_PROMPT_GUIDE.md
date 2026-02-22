# 🔥 VS CODE AI AGENT PROMPT GUIDE

## MASTER PROMPT FOR FUTURE DEVELOPMENT

Copy this prompt when working with VS Code AI Agent for Phase 2+ development:

---

## For Phase 2 Development (Teacher, Attendance, Classes)

```markdown
You are extending Phase 1 of School Management System (Multi-Tenant SaaS).

Existing Stack:
- Backend: Python Flask with SQLAlchemy
- Frontend: HTML, CSS, Vanilla JS
- Database: PostgreSQL (Multi-tenant with school_id)
- Auth: JWT + RBAC

Current Database:
- Schools, Users, Roles, Permissions
- Students (fully functional CRUD)

Task: Implement Phase 2 Features
- Teacher Management (CRUD)
- Class/Section System
- Attendance Tracking
- Subject Management

Requirements:
1. Follow existing architecture pattern: Routes → Services → Models
2. Multi-tenant isolation (always include school_id)
3. Use Blueprint pattern for routes (like student_routes.py)
4. Create corresponding service layer
5. Standard response format (from core/response.py)
6. JWT authentication required
7. RBAC: Teachers can only see/modify own data
8. Use existing database relationships
9. Soft deletes where applicable
10. Paginate list endpoints

Generate:
- Database models (Teacher, Class, Section, Subject, Attendance)
- SQLAlchemy relationships (proper foreign keys)
- Service layer logic
- Flask Blueprint routes with decorators
- Frontend pages with JavaScript
- API documentation (API_CONTRACT update)

Keep code clean, modular, and production-ready.
```

---

## For Backend Extensions

```markdown
You are a Backend Engineer extending the School Management System.

Tech Stack:
- Python 3.10+
- Flask (Application Factory Pattern)
- SQLAlchemy ORM
- Flask-JWT-Extended
- PostgreSQL

Architecture Pattern (DO NOT DEVIATE):
Routes (Flask Blueprint)
    ↓
Services (Business Logic)
    ↓
Models (Database)

Multi-Tenant Rule:
- EVERY table must have school_id (except Permission)
- EVERY query must filter by school_id
- EVERY model must have created_at, updated_at timestamps

Code Quality:
- Use BaseModel from models/base.py
- Use success_response() / error_response() from core/response.py
- Use @token_required decorator from core/auth.py
- Use @role_required('Role') for authorization
- Add docstrings to all functions
- PEP 8 compliance

Generate:
- Model with relationships
- Service with CRUD logic
- Flask Blueprint routes
- Proper error handling
- Input validation
- Response formatting

Example file structure when done:
- models/new_model.py (Model class)
- services/new_service.py (Business logic)
- routes/new_routes.py (Flask Blueprint)
```

---

## For Frontend Extensions

```markdown
You are a Frontend Developer extending School Management System UI.

Tech Stack:
- HTML5
- CSS3 (Responsive, using CSS Grid/Flexbox)
- Vanilla JavaScript (Fetch API)
- No frameworks or jQuery

Existing JavaScript Pattern:
1. api.js - Low-level API calls
   - apiRequest(endpoint, method, body)
   - localStorage for token
   
2. auth.js - Auth handlers
   - handleLogin()
   - logout()
   
3. Page-specific.js - Page logic
   - loadItems()
   - renderTable()
   - handleForm()

CSS Pattern:
- global.css - Global styles + variables
- dashboard.css - Layout, tables, modals
- forms.css - Form styling

Requirements:
1. Use modern CSS (Grid, Flexbox)
2. Responsive design (mobile-first)
3. Follow color scheme from CSS variables
4. All API calls through api.js
5. Store token in localStorage
6. Check authentication before loading page
7. Use modal for dialogs
8. Table with CRUD action buttons
9. Form validation before submit
10. Show success/error messages

Generate:
- HTML page with semantic structure
- CSS for styling and layout
- JavaScript for interactivity
- Form handling with validation
- API integration
- Error handling and messaging
```

---

## For Database Migrations

```markdown
You are extending the School Management System database.

Current Schema Pattern:
- All tables have: id (PK), created_at, updated_at
- Multi-tenant tables have: school_id (FK to schools)
- Relationships use proper foreign keys
- Unique constraints include school_id for multi-tenant keys

New Model Template:
class NewModel(BaseModel):
    __tablename__ = 'new_models'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    # ... other columns
    
    __table_args__ = (
        db.UniqueConstraint('school_id', 'field', name='uq_school_field'),
    )
    
    def to_dict(self):
        data = super().to_dict()
        data.update({ ... })
        return data

Requirements:
1. Inherit from BaseModel
2. Include school_id for multi-tenant tables
3. Add unique constraints per school
4. Define relationships properly
5. Write to_dict() method
6. Add proper docstrings
7. Test unique constraints
```

---

## For Documentation Updates

```markdown
You are updating documentation for School Management System.

When updating API_CONTRACT.md:
1. Add new endpoints with full examples
2. Include Request and Response JSON
3. List HTTP status codes
4. Document required headers
5. Show error responses
6. Update authentication table

When updating ARCHITECTURE.md:
1. Add new models to schema diagram
2. Explain new relationships
3. Update data flow if changed
4. Document new service layer
5. Add new design patterns if any

When updating FEATURES.md:
1. Add new feature to implemented list
2. Move Phase 2 feature to complete
3. Update feature matrix
4. Note any dependencies
```

---

## For Code Reviews

Use this checklist when reviewing Phase 2+ code:

### Backend Review
- [ ] Multi-tenant isolation (school_id in queries)
- [ ] Follows Routes → Services → Models pattern
- [ ] Uses decorators (@token_required, @role_required)
- [ ] Standard response format
- [ ] Error handling present
- [ ] Input validation done
- [ ] Docstrings written
- [ ] No hardcoded values
- [ ] No sensitive data in logs
- [ ] Relationships properly defined

### Frontend Review
- [ ] No inline JavaScript
- [ ] All API calls through api.js
- [ ] Token check before rendering protected content
- [ ] Responsive design tested
- [ ] Form validation implemented
- [ ] Error messages shown to user
- [ ] Loading states handled
- [ ] No console errors
- [ ] Pagination implemented for lists
- [ ] Accessibility considerations made

### Database Review
- [ ] All tables have school_id (except Permission)
- [ ] Proper foreign key relationships
- [ ] Unique constraints include school_id
- [ ] Indexes on frequently queried columns
- [ ] No SELECT N+1 problems
- [ ] Proper data types used
- [ ] Timestamps included

---

## For Performance Optimization (Phase 4+)

```markdown
You are optimizing School Management System for production.

Use This Prompt When Need Performance Work:

Current Issues:
- No caching
- N+1 query problems
- No pagination
- No indexing
- No query optimization

Optimization Tasks:
1. Add Redis for caching
2. Optimize SQLAlchemy queries (eager loading)
3. Add database indexes
4. Implement query batching
5. Add response compression
6. Optimize database connection pooling
7. Frontend: Lazy load images
8. Frontend: Minimize bundle size
9. Add monitoring/logging
10. Performance profiling

Generate production-ready optimizations.
```

---

## For Security Hardening (Phase 4+)

```markdown
You are hardening School Management System security.

Focus Areas:
1. CORS configuration
2. Rate limiting
3. SQL injection prevention
4. XSS prevention
5. CSRF tokens
6. Password policies
7. API key management
8. Audit logging
9. Encryption at rest/transit
10. Secrets management

Generate security hardening code.
```

---

## Quick Reference: Key Files

### When updating Models:
```
backend/app/models/base.py         - Modify for new base fields
backend/app/models/[model].py      - Your model file
```

### When updating Services:
```
backend/app/services/[service].py  - Your service file
```

### When updating Routes:
```
backend/app/routes/[routes].py     - Your routes file
```

### When updating Frontend:
```
frontend/assets/js/api.js           - Add API function
frontend/assets/js/[module].js     - Add page logic
frontend/assets/css/[style].css    - Add CSS
frontend/[page]/[page].html        - Add HTML
```

### When updating Docs:
```
docs/API_CONTRACT.md               - Add API endpoints
docs/ARCHITECTURE.md               - Update diagrams
docs/FEATURES.md                   - Update feature list
```

---

## Example: Phase 2 Teacher Implementation

### Use this as template:

1. **Create Teacher Model**
   - File: `backend/app/models/teacher.py`
   - Include: name, email, subject, school_id

2. **Create Teacher Service**
   - File: `backend/app/services/teacher_service.py`
   - Methods: create, read, update, delete, get_all

3. **Create Teacher Routes**
   - File: `backend/app/routes/teacher_routes.py`
   - Endpoints: /teachers (CRUD)
   - Register in app/__init__.py

4. **Frontend Teacher Page**
   - Files: frontend/admin/teachers.html
   - JS: frontend/assets/js/teacher.js
   - CSS: Update dashboard.css

5. **Update Documentation**
   - API_CONTRACT.md: Add teacher endpoints
   - FEATURES.md: Mark teacher complete
   - ARCHITECTURE.md: Add teacher to schema

---

## How to Use These Prompts

1. **Copy relevant section** based on task
2. **Paste into VS Code AI Chat**
3. **Add specific details**: "Implement Teacher model with fields: name, email, subject_taught"
4. **Ask for specific file**: "Generate backend/app/models/teacher.py"
5. **Review generated code** against standards
6. **Save to appropriate location**

---

**Last Updated**: February 22, 2026  
**Version**: 1.0.0  
**Status**: Ready for Phase 2 Development
