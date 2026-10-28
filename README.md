# Syllabus Feedback System

## Overview
A web-based system designed to collect, manage, and analyze feedback on course syllabi from multiple stakeholders (students, faculty, alumni, parents, and industry representatives) for SIES (Nerul) College of Arts, Science and Commerce (Autonomous).

> 📖 **Full Technical Documentation:** See [Documentation.MD](Documentation.MD) for comprehensive architectural details, entity-relationship diagrams, API references, and security specifications.

---

## Features
- Dynamic, stakeholder-specific feedback forms (Student, Internal Faculty, External Faculty, Alumni, Parent, Employer)
- 3 Question classifications: Demographics, Syllabus (1-5 Likert Scale), and Qualitative Suggestions
- Secure Administrator Dashboard with JWT authentication in HTTP-only cookies
- Real-time aggregate statistics and course/stream filtering
- Live response pivot table with in-line demographic editing
- Streaming CSV exports for individual stakeholders or all responses
- Admin killswitch to toggle feedback submissions open/closed
- **Supabase (PostgreSQL) Cloud Database** integration with connection pooling and MySQL backwards compatibility

---

## Prerequisites
- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) or standard `pip`
- Supabase account (or local PostgreSQL / MySQL)

---

## Installation & Quickstart with Supabase

### 1. Clone & Install Dependencies
```bash
git clone <repository-url>
cd Syllabus-Feedback-System

# Using pip:
pip install -r requirements.txt

# Or using uv:
uv sync
```

### 2. Configure Environment Variables
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Fill in your Supabase connection string and security keys:
```env
# Supabase Transaction Pooler (Port 6543)
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require

SECRET_KEY=generate_a_secure_random_key_here
```

### 3. Initialize & Seed Database
Choose **either**:
- **Option A (Supabase Web Console):** Open [setup_supabase.sql](setup_supabase.sql) and run it in the Supabase **SQL Editor**.
- **Option B (Python CLI):**
  ```bash
  python app/seed_supabase.py
  ```

### 4. Create Admin Account
```bash
python app/create_admin.py admin your_password
```

### 5. Launch the Application
```bash
# Using uvicorn:
uvicorn app.main:app --reload --port 8000

# Or using FastAPI CLI:
fastapi dev app/main.py
```

The application will start on `http://localhost:8000`  
Admin portal available at `http://localhost:8000/admin/login`

---

## Project Structure
```text
├── app/
│   ├── main.py                 # FastAPI application root & lifespan
│   ├── database.py             # Database engine (Supabase PostgreSQL / MySQL)
│   ├── models.py               # SQLAlchemy ORM models
│   ├── auth.py                 # Argon2 hashing & JWT cookie verification
│   ├── supabase_client.py      # Supabase Python SDK client wrapper
│   ├── create_admin.py         # Admin user creation & password reset CLI
│   ├── seed_supabase.py        # Automated Supabase database seeder
│   ├── routes/
│   │   ├── admin.py           # Admin dashboard, export & management routes
│   │   └── client.py          # Public feedback collection routes
│   ├── templates/             # Jinja2 HTML templates
│   │   └── feedbackForms/     # Stakeholder-specific survey forms
│   └── static/                # CSS, JS, images
├── pyproject.toml             # uv & project configuration
├── requirements.txt           # Python pip requirements
├── setup_supabase.sql         # Supabase PostgreSQL initialization script
├── setup_database.sql         # Legacy MySQL initialization script
├── Documentation.MD           # In-depth technical documentation
└── README.md                  # Project overview & quickstart
```

---

## Documentation
For complete technical documentation, database schemas, ER diagrams, and migration details, please refer to [Documentation.MD](Documentation.MD).

## License
MIT
