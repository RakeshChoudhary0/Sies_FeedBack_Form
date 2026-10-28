# Syllabus Feedback System - Technical Documentation

> **Institution:** SIES (Nerul) College of Arts, Science and Commerce (Autonomous)  
> **Application:** Multi-Stakeholder Syllabus Feedback & Analytics Platform  
> **Backend Framework:** FastAPI (Python 3.11+)  
> **ORM & Database:** SQLAlchemy 2.0 with PostgreSQL (Supabase) / MySQL fallback  
> **Frontend:** Jinja2 Templates with Tailwind CSS  
> **Security:** Argon2 password hashing + JWT in HTTP-Only Cookies

---

## 1. System Overview & Architecture

The **Syllabus Feedback System** is a full-stack web application developed to collect, manage, and analyze structured curriculum feedback across six åçdistinct stakeholder groups for academic quality assurance and National Education Policy (NEP) compliance.

The system replaces manual survey workflows with dynamic, database-driven forms, automated aggregation, and an interactive admin analytics dashboard featuring live data pivoting, filtering, inline updates, and streaming CSV exports.

### High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientLayer["Client Layer (Browser)"]
        UserBrowser["Stakeholder (Student, Faculty, Alumni, Parent, Employer)"]
        AdminBrowser["College Administrator"]
    end

    subgraph FastAPILayer["FastAPI Application Layer"]
        RouterClient["Client Router (/feedback, /submit-feedback)"]
        RouterAdmin["Admin Router (/admin/dashboard, /admin/export)"]
        AuthMiddleware["Security / JWT Cookie Verification (Argon2 + Jose)"]
        TemplateEngine["Jinja2 Template Engine + TailwindCSS"]
    end

    subgraph DataAccessLayer["Data Access & ORM Layer"]
        SQLAlchemyORM["SQLAlchemy ORM (Models & Sessions)"]
        SupabaseClientWrapper["Supabase Python SDK Wrapper (Optional)"]
    end

    subgraph DatabaseLayer["Supabase PostgreSQL Cloud Infrastructure"]
        Supavisor["Supavisor Connection Pooler (Port 6543 / 5432)"]
        PostgresDB[("PostgreSQL Database (Tables & Indexes)")]
        RLS["Row Level Security Policies"]
    end

    UserBrowser -->|HTTP GET / POST| RouterClient
    AdminBrowser -->|HTTP GET / POST with JWT Cookie| RouterAdmin

    RouterAdmin --> AuthMiddleware
    RouterClient --> TemplateEngine
    RouterAdmin --> TemplateEngine

    RouterClient --> SQLAlchemyORM
    RouterAdmin --> SQLAlchemyORM
    RouterClient -.-> SupabaseClientWrapper

    SQLAlchemyORM -->|Encrypted SSL Connection| Supavisor
    Supavisor --> PostgresDB
    SupabaseClientWrapper -.->|PostgREST API| RLS
    RLS -.-> PostgresDB
```

---

## 2. Key Features & Stakeholder Workflow

### 2.1 Supported Stakeholder Categories

The platform caters to six specific stakeholder categories, each with tailored demographic questions and syllabus assessment criteria:

| Stakeholder Category     | Code Identifier   | Target Audience                        | Key Focus Areas                                                        |
| :----------------------- | :---------------- | :------------------------------------- | :--------------------------------------------------------------------- |
| **Internal Faculty**     | `TEACHER`         | College professors & lecturers         | Syllabus depth, pedagogical effectiveness, learning outcomes alignment |
| **External Faculty**     | `OUTSIDE_TEACHER` | Visiting faculty & peer professors     | Skill relevance, comparative syllabus standards, employability         |
| **Students**             | `STUDENT`         | Current enrolled students              | Comprehension, delivery pacing, NEP alignment, career readiness        |
| **Alumni**               | `ALUMNI`          | Graduated alumni in industry/higher ed | Practical relevance, real-world utility, career preparation            |
| **Parents**              | `PARENT`          | Parents & guardians of students        | Holistic growth, discipline, overall institutional satisfaction        |
| **Industry / Employers** | `EMPLOYER`        | Recruiters & industry leaders          | Skill gap analysis, modern tools/trends, recruitment readiness         |

### 2.2 Question Categorization Framework

Every question in the system is classified under one of three categories:

1. **`DEMOGRAPHIC`**: Captures respondent context (Name, Email, Course/Stream, Class, Organization, PRN).
2. **`SYLLABUS`**: Quantitative evaluation statements answered via a **1 to 5 Likert rating scale** (1 = Poor, 5 = Excellent).
3. **`SUGGESTION`**: Qualitative open-ended text fields for actionable curriculum improvements.

### 2.3 Form Availability Control (Admin Killswitch)

Administrators can toggle form submissions on or off with a single click in the dashboard. When disabled:

- Client route requests to `/feedback/{form_name}` immediately return a styled `403 Forbidden` notice ("Feedback Forms Closed").
- Direct POST submissions to `/submit-feedback` are blocked before database writes occur.

### 2.4 Administrative Analytics & Reporting

- **Cumulative Cross-Stakeholder Overview:** Aggregates average scores across all stakeholder groups for high-level institutional reporting.
- **Stakeholder Deep-Dive:** Displays per-question response counts and average ratings.
- **Stream/Course Filtering:** Filters responses by specific academic streams (e.g., `BSc IT`, `BSc CS`, `B.Com (Accounting & Finance)`).
- **Live Pivot Matrix:** Converts normalized vertical answers into a horizontal spreadsheet-like row for each respondent.
- **Inline Demographic Updates:** Allows administrators to correct typographical errors in demographic data directly from the dashboard table.
- **Streaming CSV Export:** Generates downloadable CSV reports on-the-fly using memory buffers (`StreamingResponse`) to avoid disk bloat and memory spikes.

---

## 3. Database Architecture & Schema

The system uses a normalized relational schema that decouples questions and answers from hardcoded form layouts, allowing forms and questions to change without schema migrations.

### 3.1 Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    STAKEHOLDERS ||--o{ STAKEHOLDER_PERSONAL_INFO : "submits"
    FEEDBACK_SESSION ||--o{ STAKEHOLDER_PERSONAL_INFO : "groups"
    STAKEHOLDER_PERSONAL_INFO ||--o{ FEEDBACK_ANSWERS : "provides"
    SYLLABUS_QUESTION ||--o{ FEEDBACK_ANSWERS : "answers"

    STAKEHOLDERS {
        int stakeholder_id PK
        varchar stakeholder_type UK
    }

    FEEDBACK_SESSION {
        int session_id PK
        varchar session_name
        timestamptz created_at
    }

    STAKEHOLDER_PERSONAL_INFO {
        int person_id PK
        int session_id FK
        int stakeholder_id FK
        varchar name
        varchar association_name
    }

    SYLLABUS_QUESTION {
        int id PK
        text text
        varchar stakeholder_type
        enum category
    }

    FEEDBACK_ANSWERS {
        int answer_id PK
        int person_id FK
        int question_id FK
        text answer_text
    }

    ADMIN_USER {
        int admin_id PK
        varchar username UK
        varchar password
    }

    SYSTEM_SETTINGS {
        int id PK
        boolean is_active
    }
```

### 3.2 Detailed Data Dictionary

#### 1. `stakeholders`

Stores the recognized stakeholder roles within the college.

- `stakeholder_id` (`SERIAL PRIMARY KEY`): Unique stakeholder ID.
- `stakeholder_type` (`VARCHAR(50) UNIQUE NOT NULL`): Role identifier (`TEACHER`, `STUDENT`, `ALUMNI`, `EMPLOYER`, `OUTSIDE_TEACHER`, `PARENT`).

#### 2. `feedback_session`

Organizes feedback collection batches (e.g., "Academic Year 2024-25 Term 1").

- `session_id` (`SERIAL PRIMARY KEY`): Unique session ID.
- `session_name` (`VARCHAR(100) NOT NULL`): Descriptive session name.
- `created_at` (`TIMESTAMPTZ DEFAULT NOW()`): Creation timestamp.

#### 3. `stakeholder_personal_info`

Represents an individual submission attempt.

- `person_id` (`SERIAL PRIMARY KEY`): Unique respondent submission ID.
- `session_id` (`INT NOT NULL`): Foreign key referencing `feedback_session.session_id`.
- `stakeholder_id` (`INT NOT NULL`): Foreign key referencing `stakeholders.stakeholder_id`.
- `name` (`VARCHAR(100) NOT NULL`): Respondent name or placeholder (`N/A`).
- `association_name` (`VARCHAR(100)`): Department, college, or company name.

#### 4. `syllabus_question`

Defines survey questions dynamically.

- `id` (`SERIAL PRIMARY KEY`): Question ID.
- `text` (`TEXT NOT NULL`): Full question prompt.
- `stakeholder_type` (`VARCHAR(50) NOT NULL`): Target stakeholder code.
- `category` (`question_category ENUM`): One of `'DEMOGRAPHIC'`, `'SYLLABUS'`, or `'SUGGESTION'`.

#### 5. `feedback_answers`

Stores every answer to every question normalized on separate rows.

- `answer_id` (`SERIAL PRIMARY KEY`): Unique answer ID.
- `person_id` (`INT NOT NULL`): Foreign key referencing `stakeholder_personal_info.person_id` (`ON DELETE CASCADE`).
- `question_id` (`INT NOT NULL`): Foreign key referencing `syllabus_question.id` (`ON DELETE CASCADE`).
- `answer_text` (`TEXT NOT NULL`): Submitted response (numeric string `'1'`-`'5'` for ratings, string for demographics, long text for suggestions).

#### 6. `admin_user`

Stores administrator credentials.

- `admin_id` (`SERIAL PRIMARY KEY`): Unique admin ID.
- `username` (`VARCHAR(50) UNIQUE NOT NULL`): Login username.
- `password` (`VARCHAR(255) NOT NULL`): Argon2 password hash.

#### 7. `system_settings`

Global configuration flags.

- `id` (`INT PRIMARY KEY`): Setting record ID (typically `1`).
- `is_active` (`BOOLEAN DEFAULT TRUE`): Form submission switch (`true` = open, `false` = closed).

---

## 4. Converting to Supabase

Supabase is a hosted backend platform built on PostgreSQL. Moving from local MySQL to Supabase provides automated backups, connection pooling, high availability, an intuitive SQL/table editor, and SSL encryption.

### 4.1 Connection Modes in Supabase

Supabase provides two distinct connection URIs for PostgreSQL:

| Mode                               | Port   | Recommended Use               | URI Structure                                                                                        |
| :--------------------------------- | :----- | :---------------------------- | :--------------------------------------------------------------------------------------------------- |
| **Transaction Pooler (Supavisor)** | `6543` | **FastAPI & Web Apps (Best)** | `postgresql://postgres.[REF]:[PWD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require` |
| **Session Pooler**                 | `5432` | Long-lived migrations/DDL     | `postgresql://postgres.[REF]:[PWD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require` |
| **Direct Connection**              | `5432` | Standard direct client        | `postgresql://postgres:[PWD]@db.[REF].supabase.co:5432/postgres?sslmode=require`                     |

> [!TIP]
> Always use **Transaction Mode (Port 6543)** with Supavisor for web backends like FastAPI. It reuses PostgreSQL processes efficiently and prevents connection exhaustion.

### 4.2 Codebase Enhancements for Supabase

The codebase has been refactored to support Supabase out of the box:

1. **Adaptive Driver Detection in [`app/database.py`](file:///Users/rakesh/Documents/WORKING_DIR/Syllabus-Feedback-System/app/database.py):**
   - Automatically detects `DATABASE_URL` or `SUPABASE_DB_URL`.
   - Normalizes legacy `postgres://` prefixes to SQLAlchemy-compliant `postgresql+psycopg2://`.
   - Enforces `sslmode=require` for secure Supabase cloud connections.
   - Tunes pool recycling (`pool_recycle=300`) to match Supavisor's idle timeout.
   - Maintains fallback compatibility with MySQL and SQLite.

2. **Schema Data Types in [`app/models.py`](file:///Users/rakesh/Documents/WORKING_DIR/Syllabus-Feedback-System/app/models.py):**
   - Expanded `feedback_answers.answer_text` to `Text` (prevents truncation on long suggestion submissions).
   - Expanded `admin_user.password` to `String(255)` for Argon2 hash length safety.
   - Enforced cascading foreign key constraints (`ondelete="CASCADE"`).

3. **Supabase DDL Script ([`setup_supabase.sql`](file:///Users/rakesh/Documents/WORKING_DIR/Syllabus-Feedback-System/setup_supabase.sql)):**
   - Pure PostgreSQL DDL with `SERIAL PRIMARY KEY`, PostgreSQL `ENUM`, performance indexes, seed data, and Row Level Security (RLS) policies.

4. **Automated Seeding Script ([`app/seed_supabase.py`](file:///Users/rakesh/Documents/WORKING_DIR/Syllabus-Feedback-System/app/seed_supabase.py)):**
   - Seeds the entire questionnaire and stakeholder matrix directly using SQLAlchemy ORM.

5. **Supabase SDK Client ([`app/supabase_client.py`](file:///Users/rakesh/Documents/WORKING_DIR/Syllabus-Feedback-System/app/supabase_client.py)):**
   - Initializes the official `supabase-py` client for features like file storage (e.g. syllabus PDFs) or Supabase Auth.

---

## 5. Step-by-Step Supabase Migration Guide

### Step 1: Create a Supabase Project

1. Go to [https://database.new](https://database.new) and sign in to Supabase.
2. Click **New project**, choose an organization, set a project name (e.g., `syllabus-feedback-system`), and select a region close to your users (e.g., `Mumbai (ap-south-1)`).
3. Set a strong database password and keep it handy.

### Step 2: Retrieve Your Connection String

1. In the Supabase Dashboard, navigate to **Project Settings** (gear icon) -> **Database**.
2. Scroll down to the **Connection string** section.
3. Select the **URI** tab.
4. Select **Mode: Transaction** (port 6543).
5. Copy the connection string. It will look like:
   ```text
   postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```

### Step 3: Configure Environment Variables

Create or update your `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and set your credentials:

```env
# Supabase PostgreSQL Connection String (Transaction Pooler)
DATABASE_URL=postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require

# Supabase API Credentials (from Project Settings -> API)
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
SUPABASE_KEY=[YOUR-SUPABASE-ANON-KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SUPABASE-SERVICE-ROLE-KEY]

# Security
SECRET_KEY=9a2b8e34c567812f890123456789abcdef0123456789abcdef0123456789abcd
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Admin User Defaults
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
```

### Step 4: Install Dependencies

Install Python dependencies including PostgreSQL drivers:

```bash
# Using pip
pip install -r requirements.txt

# Or using uv (recommended)
uv add psycopg2-binary supabase
uv sync
```

### Step 5: Initialize and Seed Database Tables

You can initialize the database using **either** of the following methods:

#### Method A: Using Supabase Web SQL Editor (Recommended)

1. In the Supabase Dashboard, open the **SQL Editor** tab from the left sidebar.
2. Open [`setup_supabase.sql`](file:///Users/rakesh/Documents/WORKING_DIR/Syllabus-Feedback-System/setup_supabase.sql) from this repository.
3. Paste the contents into the SQL Editor and click **Run**.
4. All tables, indexes, RLS policies, and questions are created instantly.

#### Method B: Using the Python CLI Seeder

Alternatively, run the automated Python migration:

```bash
python app/seed_supabase.py
```

### Step 6: Create the Admin Account

Create or update your initial administrator credentials:

```bash
python app/create_admin.py admin your_secure_password
```

### Step 7: Launch the Application

Run the FastAPI development server:

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using FastAPI CLI
fastapi dev app/main.py
```

Visit:

- Public Landing Page: `http://localhost:8000/`
- Admin Dashboard: `http://localhost:8000/admin/login`

---

## 6. Project Structure

```text
Syllabus-Feedback-System/
├── app/
│   ├── main.py                 # FastAPI application root & lifespan setup
│   ├── database.py             # Database engine & multi-dialect connection manager
│   ├── models.py               # SQLAlchemy ORM declarative models
│   ├── auth.py                 # Argon2 hashing & JWT cookie verification
│   ├── supabase_client.py      # Supabase Python SDK client wrapper
│   ├── create_admin.py         # Admin user creation & password reset CLI
│   ├── seed_supabase.py        # Automated PostgreSQL/Supabase database seeder
│   ├── seed_questions.py       # Legacy question seeding utility
│   ├── check_data.py           # Diagnostic script for database verification
│   ├── check_stakeholders.py   # Diagnostic script for stakeholder checking
│   ├── reset_db.py             # Database teardown utility
│   ├── routes/
│   │   ├── client.py           # Public feedback routes (GET forms, POST submit)
│   │   └── admin.py            # Admin routes (dashboard, login, CSV export, toggle)
│   ├── templates/              # Jinja2 HTML templates
│   │   ├── index.html          # Public landing page
│   │   ├── categoryselection.html # Stakeholder category selector
│   │   ├── thankyou.html       # Submission confirmation page
│   │   ├── admin_login.html    # Secure administrator login
│   │   ├── admin_dashboard.html# Analytics dashboard & response pivot table
│   │   ├── 401.html            # Unauthorized access template
│   │   └── feedbackForms/      # Stakeholder-specific survey forms
│   │       ├── studentfeedback.html
│   │       ├── internalfaculty.html
│   │       ├── externalfaculty.html
│   │       ├── alumnifeedback.html
│   │       ├── industryrep.html
│   │       └── parentfeedback.html
│   └── static/                 # Static assets (images, logos, scripts)
├── pyproject.toml              # Project metadata & uv dependencies
├── requirements.txt            # Python pip dependencies
├── setup_supabase.sql          # Full Supabase PostgreSQL initialization script
├── setup_database.sql          # Legacy MySQL setup script
├── .env.example                # Environment variables template
├── Documentation.MD            # Comprehensive technical documentation
└── README.md                   # Quickstart guide
```

---

## 7. API & Route Reference

### 7.1 Public / Client Routes

| Method | Endpoint                | Description                  | Auth Required | Parameters / Body                 | Response                                  |
| :----- | :---------------------- | :--------------------------- | :------------ | :-------------------------------- | :---------------------------------------- |
| `GET`  | `/`                     | Renders public landing page  | No            | None                              | `index.html` (200 OK)                     |
| `GET`  | `/select-category`      | Stakeholder selection portal | No            | None                              | `categoryselection.html` (200 OK)         |
| `GET`  | `/feedback/{form_name}` | Loads survey for stakeholder | No            | `form_name` path parameter        | Form HTML (200 OK) or Closed Notice (403) |
| `POST` | `/submit-feedback`      | Processes survey responses   | No            | Form data (`form_name`, `q_{id}`) | `303 See Other` -> `/submitted-feedback`  |
| `GET`  | `/submitted-feedback`   | Submission success screen    | No            | None                              | `thankyou.html` (200 OK)                  |

### 7.2 Administrator Routes

| Method | Endpoint                    | Description                            | Auth Required | Parameters / Body                                    | Response                          |
| :----- | :-------------------------- | :------------------------------------- | :------------ | :--------------------------------------------------- | :-------------------------------- |
| `GET`  | `/admin/login`              | Administrator login portal             | No            | None                                                 | `admin_login.html` (200 OK)       |
| `POST` | `/admin/login`              | Verifies credentials & sets JWT cookie | No            | `username`, `password` form                          | `302 Found` -> `/admin/dashboard` |
| `GET`  | `/admin/logout`             | Clears cookie & logs out               | Yes           | None                                                 | `302 Found` -> `/admin/login`     |
| `GET`  | `/admin/dashboard`          | Analytics dashboard & pivot table      | Yes           | `stakeholder_id` (opt), `stream` (opt)               | `admin_dashboard.html` (200 OK)   |
| `POST` | `/admin/update-responses`   | Inline updates to demographic data     | Yes           | JSON list: `[{"person_id", "question_id", "value"}]` | `{"status": "ok"}` (200 OK)       |
| `POST` | `/admin/toggle-forms`       | Toggles submission open/closed state   | Yes           | None                                                 | `{"status": boolean}` (200 OK)    |
| `GET`  | `/admin/export/stakeholder` | Streams stakeholder CSV report         | Yes           | `stakeholder_id` (int), `stream` (opt)               | `StreamingResponse` (`text/csv`)  |
| `GET`  | `/admin/export/all`         | Streams complete database CSV report   | Yes           | None                                                 | `StreamingResponse` (`text/csv`)  |

---

## 8. Security & Authentication Model

### 8.1 Password Hashing with Argon2

Passwords are encrypted using Argon2 (via `passlib.context.CryptContext(schemes=["argon2"])`). Argon2 is the winner of the Password Hashing Competition (PHC) and provides superior resistance against GPU/ASIC brute-force attacks compared to legacy SHA or MD5.

### 8.2 Stateless Session Management via JWT

1. When an administrator logs in at `/admin/login`, the backend verifies the Argon2 hash.
2. Upon verification, `create_access_token()` mints a signed JSON Web Token (JWT) containing the `sub` (admin ID) and an `exp` claim.
3. The JWT is transmitted in a secure cookie named `access_token` with the following attributes:
   - `httponly=True`: Prevents client-side JavaScript access (mitigating XSS theft).
   - `samesite="lax"`: Protects against Cross-Site Request Forgery (CSRF).
   - `secure=False` for local testing, toggleable to `True` in production HTTPS environments.

### 8.3 Route Protection

Protected admin routes depend on the `admin_required` dependency:

- Extracts `access_token` from incoming request cookies.
- Decodes and validates signature and expiration with `SECRET_KEY`.
- Unauthenticated requests trigger a `401 Unauthorized` exception handled by `unauthorized_handler` in `app/main.py`, redirecting the user to `/admin/login` and purging stale cookies.

---

## 9. Production Deployment Checklist

When moving the application to production:

1. **Enable HTTPS / SSL**:
   - In [`app/routes/admin.py`](file:///Users/rakesh/Documents/WORKING_DIR/Syllabus-Feedback-System/app/routes/admin.py#L75), set `response.set_cookie(..., secure=True)` so tokens are only sent over TLS.
2. **Generate a Unique `SECRET_KEY`**:
   - Generate via `openssl rand -hex 32` and place in `.env`. Never commit `.env` to source control.
3. **Database Connection Pooling**:
   - Ensure you are using Supabase's port `6543` connection pooler to avoid database connection exhaustion.
4. **Reverse Proxy (Nginx / Caddy)**:
   - Run Uvicorn behind Nginx or Caddy with proxy headers enabled (`--proxy-headers --forwarded-allow-ips='*'`).
5. **Form Active State**:
   - Ensure the form toggle is set to `active` at the start of feedback collection cycles.

---

## 10. Frequently Asked Questions (FAQ)

### Q1: Can I still run this project with MySQL?

**Yes.** The refactored database engine in [`app/database.py`](file:///Users/rakesh/Documents/WORKING_DIR/Syllabus-Feedback-System/app/database.py) detects MySQL connection details automatically. If your `.env` contains `DB_PORT=3306` or `mysql+pymysql://`, it connects to MySQL without modification.

### Q2: Why does Supabase require `?sslmode=require`?

Supabase PostgreSQL instances require encrypted SSL connections to prevent eavesdropping and man-in-the-middle attacks over the public Internet. The database connection manager appends `?sslmode=require` automatically if connecting to Supabase domains.

### Q3: What happens to existing answers if a question is deleted?

The database uses `ON DELETE CASCADE` on all foreign keys. If a question is deleted, associated answers in `feedback_answers` are cleaned up automatically without leaving orphaned records.

### Q4: How do I change an admin password?

Run the CLI script:

```bash
python app/create_admin.py admin new_password_here
```

If the user exists, the script updates the password hash immediately.

## Documentation

For complete technical documentation, database schemas, ER diagrams, and migration details, please refer to [Documentation.MD](Documentation.MD).

## License

MIT
