# SETUP_INSTRUCTIONS.md

# 🚀 Quick Start Guide - School Management System

## ⚡ 5-Minute Setup

### Prerequisites Check
```bash
python --version          # Should be 3.10+
psql --version           # Should be 12+
```

---

## Step 1: Backend Setup (3 minutes)

### 1.1 Navigate to backend
```bash
cd backend
```

### 1.2 Create virtual environment
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

### 1.3 Install dependencies
```bash
pip install -r requirements.txt
```

### 1.4 Configure database
Update `.env` file:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/schoolms
JWT_SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=development
DEBUG=True
```

### 1.5 Create database
```bash
psql -U postgres
CREATE DATABASE schoolms;
\q
```

### 1.6 Run backend
```bash
python run.py
```

✅ Backend running at: `http://localhost:5000`

---

## Step 2: Frontend Setup (1 minute)

### 2.1 Start HTTP server
In a new terminal, navigate to root folder:

```bash
cd frontend
python -m http.server 8000
```

✅ Frontend running at: `http://localhost:8000`

---

## Step 3: First Test (1 minute)

### 3.1 Register a school
Open browser: `http://localhost:8000/auth/register.html`

Fill form:
- School Name: `St. Johns Academy`
- School Email: `admin@stjohns.com`
- Admin Name: `John Doe`
- Admin Email: `john@stjohns.com`
- Admin Password: `password123`

Click Register ✅

### 3.2 Login
Navigate to: `http://localhost:8000/auth/login.html`

Enter:
- School ID: `1` (from registration)
- Email: `john@stjohns.com`
- Password: `password123`

Click Login ✅

### 3.3 Dashboard
You're now at the Admin Dashboard!

---

## 🧪 Test API with Curl

### Register School
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "school_name": "Test School",
    "school_email": "test@school.com",
    "admin_name": "Admin",
    "admin_email": "admin@test.com",
    "admin_password": "test123"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "test123",
    "school_id": 1
  }'
```

Save the token from response, then:

### Create Student
```bash
curl -X POST http://localhost:5000/api/students \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN_HERE>" \
  -d '{
    "name": "Alice Johnson",
    "admission_no": "ADM001",
    "class_name": "10-A",
    "email": "alice@example.com",
    "phone": "9876543210"
  }'
```

### Get Students
```bash
curl -X GET "http://localhost:5000/api/students?page=1&limit=10" \
  -H "Authorization: Bearer <YOUR_TOKEN_HERE>"
```

---

## 📂 Project Structure After Setup

```
schoolms/
├── backend/
│   ├── venv/                    # Virtual environment
│   ├── app/                     # Application code
│   ├── run.py                   # Start here
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── assets/
│   ├── auth/
│   ├── admin/
│   └── index.html
│
└── docs/                        # Documentation
```

---

## 🛠 Troubleshooting

### Issue: "psycopg2 installation failed"
```bash
# Windows - install with binary
pip install psycopg2-binary

# Mac - install PostgreSQL first
brew install postgresql

# Linux
sudo apt-get install postgresql postgresql-contrib
```

### Issue: "Database connection refused"
- Check PostgreSQL is running
- Verify DATABASE_URL in .env
- Ensure database exists: `psql -l`

### Issue: "Port 5000 already in use"
```bash
# Use different port
python run.py --port 5001

# Or kill existing process
lsof -i :5000
kill -9 <PID>
```

### Issue: "Port 8000 already in use"
```bash
# Use different port
python -m http.server 8001
```

### Issue: "JWT token invalid"
- Ensure JWT_SECRET_KEY in .env is set
- Token expires after 24 hours
- Re-login to get new token

---

## 📝 Development Workflow

### Daily Startup
```bash
# Terminal 1: Backend
cd backend
venv\Scripts\activate  # or source venv/bin/activate
python run.py

# Terminal 2: Frontend
cd frontend
python -m http.server 8000
```

### Making Changes
- Backend changes auto-reload (debug mode)
- Frontend changes require browser refresh
- Database changes may need manual migration

### Testing
- Use browser DevTools (F12)
- Check Network tab for API calls
- Check Console for JavaScript errors
- Backend logs in terminal

---

## 🔐 Security Notes for Development

⚠️ **NOT for Production**:
- Debug mode is ON
- JWT_SECRET_KEY is default
- CORS not restricted
- No rate limiting

### Before Production
- [ ] Change JWT_SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure CORS properly
- [ ] Use environment-specific configs
- [ ] Enable HTTPS
- [ ] Add rate limiting
- [ ] Set up monitoring

---

## 📚 Next Steps

1. **Explore API**: Check `docs/API_CONTRACT.md`
2. **Understand Architecture**: Read `docs/ARCHITECTURE.md`
3. **Learn Features**: Review `docs/FEATURES.md`
4. **Plan Future**: See `docs/FUTURE_UPGRADE_PLAN.md`

---

## ✅ Verification Checklist

- [ ] Backend running at http://localhost:5000
- [ ] Frontend running at http://localhost:8000
- [ ] Database created and accessible
- [ ] Can register a school
- [ ] Can login successfully
- [ ] Can see admin dashboard
- [ ] Can add a student
- [ ] Can view students list

---

## 🆘 Need Help?

1. Check all prerequisites are installed
2. Review error messages carefully
3. Check logs in terminal
4. Verify .env configuration
5. Try killing and restarting servers

---

**Version**: 1.0.0  
**Last Updated**: February 22, 2026  
**Status**: Ready to Deploy
