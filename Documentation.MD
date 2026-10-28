# Syllabus Feedback System - Technical Documentation

> **Institution:** SIES (Nerul) College of Arts, Science and Commerce (Autonomous)  
> **Application:** Multi-Stakeholder Syllabus Feedback & Analytics Platform  
> **Backend Framework:** FastAPI (Python 3.11+)  
> **ORM & Database:** SQLAlchemy 2.0 with PostgreSQL (Supabase) / MySQL fallback  
> **Frontend:** Jinja2 Templates with Tailwind CSS  
> **Deployment:** Vercel Serverless (via `@vercel/python`)  
> **Security:** Argon2 password hashing + JWT in HTTP-Only Cookies  

---

## 1. System Overview & Architecture

The **Syllabus Feedback System** is a full-stack web application developed to collect, manage, and analyze structured curriculum feedback across six distinct stakeholder groups for academic quality assurance and National Education Policy (NEP) compliance.

The system replaces manual survey workflows with dynamic, database-driven forms, automated aggregation, and an interactive admin analytics dashboard featuring live data pivoting, filtering, inline updates, and streaming CSV exports.

### High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientLayer["Client Layer (Browser)"]
        UserBrowser["Stakeholder (Student, Faculty, Alumni, Parent, Employer)"]
        AdminBrowser["College Administrator"]
    end

    subgraph FastAPILayer["FastAPI Application Layer (Vercel Serverless)"]
        VercelHandler["Vercel Handler (api/index.py)"]
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

    UserBrowser -->|HTTP GET / POST| VercelHandler
    AdminBrowser -->|HTTP GET / POST with JWT Cookie| VercelHandler

    VercelHandler --> RouterClient
    VercelHandler --> RouterAdmin

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

| Stakeholder Category | Code Identifier | Target Audience | Key Focus Areas |
| :--- | :--- | :--- | :--- |
| **Internal Faculty** | `TEACHER` | College professors & lecturers | Syllabus depth, pedagogical effectiveness, learning outcomes alignment |
| **External Faculty** | `OUTSIDE_TEACHER` | Visiting faculty & peer professors | Skill relevance, comparative syllabus standards, employability |
| **Students** | `STUDENT` | Current enrolled students | Comprehension, delivery pacing, NEP alignment, career readiness |
| **Alumni** | `ALUMNI` | Graduated alumni in industry/higher ed | Practical relevance, real-world utility, career preparation |
| **Parents** | `PARENT` | Parents & guardians of students | Holistic growth, discipline, overall institutional satisfaction |
| **Industry / Employers** | `EMPLOYER` | Recruiters & industry leaders | Skill gap analysis, modern tools/trends, recruitment readiness |

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

---

## 4. Converting to Supabase

Supabase is a hosted backend platform built on PostgreSQL. Moving from local MySQL to Supabase provides automated backups, connection pooling, high availability, an intuitive SQL/table editor, and SSL encryption.

### 4.1 Connection Modes in Supabase

Supabase provides two distinct connection URIs for PostgreSQL:

| Mode | Port | Recommended Use | URI Structure |
| :--- | :--- | :--- | :--- |
| **Transaction Pooler (Supavisor)** | `6543` | **FastAPI & Vercel Serverless (Best)** | `postgresql://postgres.[REF]:[PWD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require` |
| **Session Pooler** | `5432` | Long-lived migrations/DDL | `postgresql://postgres.[REF]:[PWD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require` |
| **Direct Connection** | `5432` | Standard direct client | `postgresql://postgres:[PWD]@db.[REF].supabase.co:5432/postgres?sslmode=require` |

> [!IMPORTANT]
> When deploying to **Vercel Serverless**, always use **Transaction Mode (Port 6543)** with Supavisor. Since serverless functions scale dynamically, direct database connections can quickly exceed PostgreSQL connection limits.

---

## 5. Deploying to Vercel

The project is pre-configured for zero-friction deployment to Vercel using the official `@vercel/python` builder.

### 5.1 Vercel Deployment Architecture
- **[`vercel.json`](file:///Users/rakesh/Documents/WORKING_DIR/Syllabus-Feedback-System/vercel.json)**: Directs all traffic (`/(.*)`) to the serverless entrypoint `api/index.py`.
- **[`api/index.py`](file:///Users/rakesh/Documents/WORKING_DIR/Syllabus-Feedback-System/api/index.py)**: Resolves paths dynamically and exports the FastAPI `app` instance.
- **[`.vercelignore`](file:///Users/rakesh/Documents/WORKING_DIR/Syllabus-Feedback-System/.vercelignore)**: Excludes local virtual environments (`.venv/`, `venv/`), `.git/`, and SQLite databases to keep the serverless bundle fast and lightweight.
- **Absolute Template Resolution**: FastAPI template and static mounts use absolute paths derived from `Path(__file__)`, preventing missing template errors inside Vercel Lambda containers.

### 5.2 Step-by-Step Vercel Deployment

#### Step 1: Push your Code to GitHub
Ensure all files are committed and pushed to your GitHub repository:
```bash
git add .
git commit -m "Configure Vercel serverless deployment"
git push origin main
```

#### Step 2: Import into Vercel
1. Log in to [https://vercel.com](https://vercel.com).
2. Click **Add New...** ➔ **Project**.
3. Select your GitHub repository (`Syllabus-Feedback-System`) and click **Import**.

#### Step 3: Configure Environment Variables in Vercel
In the Vercel project configuration screen, open the **Environment Variables** section and add:

| Variable Name | Example Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://postgres.[REF]:[PWD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require` | **Supabase Transaction Pooler URL** |
| `SECRET_KEY` | `9a2b8e34c567812f890123456789abcdef0123456789abcdef...` | 64-char random hex key for JWT encryption |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Cookie session timeout |
| `ADMIN_USERNAME` | `admin` | Initial admin username |
| `ADMIN_PASSWORD` | `your_secure_password` | Initial admin password |

#### Step 4: Click Deploy!
Vercel will install dependencies from `requirements.txt`, compile the serverless function, and assign you a live HTTPS URL (e.g., `https://syllabus-feedback-system.vercel.app`).

---

## 6. Project Structure

```text
├── api/
│   └── index.py                # Vercel serverless entrypoint
├── app/
│   ├── main.py                 # FastAPI application root & lifespan setup
│   ├── database.py             # Database engine & multi-dialect connection manager
│   ├── models.py               # SQLAlchemy ORM declarative models
│   ├── auth.py                 # Argon2 hashing & JWT cookie verification
│   ├── supabase_client.py      # Supabase Python SDK client wrapper
│   ├── create_admin.py         # Admin user creation & password reset CLI
│   ├── seed_supabase.py        # Automated PostgreSQL/Supabase database seeder
│   ├── routes/
│   │   ├── admin.py           # Admin dashboard, export & management routes
│   │   └── client.py          # Public feedback collection routes
│   ├── templates/             # Jinja2 HTML templates
│   │   ├── index.html          # Public landing page
│   │   ├── categoryselection.html # Stakeholder category selector
│   │   ├── thankyou.html       # Submission confirmation page
│   │   ├── admin_login.html    # Secure administrator login
│   │   ├── admin_dashboard.html# Analytics dashboard & response pivot table
│   │   ├── 401.html            # Unauthorized access template
│   │   └── feedbackForms/      # Stakeholder-specific survey forms
│   └── static/                 # Static assets (images, logos, scripts)
├── vercel.json                 # Vercel serverless routing configuration
├── .vercelignore               # Bundle exclusion list for Vercel
├── pyproject.toml              # uv & project configuration
├── requirements.txt            # Python pip dependencies
├── setup_supabase.sql          # Full Supabase PostgreSQL initialization script
├── setup_database.sql          # Legacy MySQL setup script
├── .env.example                # Environment variables template
├── Documentation.MD            # Comprehensive technical documentation
└── README.md                   # Project overview & quickstart
```

---

## 7. API & Route Reference

### 7.1 Public / Client Routes

| Method | Endpoint | Description | Auth Required | Parameters / Body | Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Renders public landing page | No | None | `index.html` (200 OK) |
| `GET` | `/select-category` | Stakeholder selection portal | No | None | `categoryselection.html` (200 OK) |
| `GET` | `/feedback/{form_name}` | Loads survey for stakeholder | No | `form_name` path parameter | Form HTML (200 OK) or Closed Notice (403) |
| `POST` | `/submit-feedback` | Processes survey responses | No | Form data (`form_name`, `q_{id}`) | `303 See Other` -> `/submitted-feedback` |
| `GET` | `/submitted-feedback` | Submission success screen | No | None | `thankyou.html` (200 OK) |

### 7.2 Administrator Routes

| Method | Endpoint | Description | Auth Required | Parameters / Body | Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/admin/login` | Administrator login portal | No | None | `admin_login.html` (200 OK) |
| `POST` | `/admin/login` | Verifies credentials & sets JWT cookie | No | `username`, `password` form | `302 Found` -> `/admin/dashboard` |
| `GET` | `/admin/logout` | Clears cookie & logs out | Yes | None | `302 Found` -> `/admin/login` |
| `GET` | `/admin/dashboard` | Analytics dashboard & pivot table | Yes | `stakeholder_id` (opt), `stream` (opt) | `admin_dashboard.html` (200 OK) |
| `POST` | `/admin/update-responses` | Inline updates to demographic data | Yes | JSON list: `[{"person_id", "question_id", "value"}]` | `{"status": "ok"}` (200 OK) |
| `POST` | `/admin/toggle-forms` | Toggles submission open/closed state | Yes | None | `{"status": boolean}` (200 OK) |
| `GET` | `/admin/export/stakeholder` | Streams stakeholder CSV report | Yes | `stakeholder_id` (int), `stream` (opt) | `StreamingResponse` (`text/csv`) |
| `GET` | `/admin/export/all` | Streams complete database CSV report | Yes | None | `StreamingResponse` (`text/csv`) |

---

## 8. License
MIT



% python app/create_admin.py SIES_ADMIN_NAME SIES_ADMIN_PASSWORD