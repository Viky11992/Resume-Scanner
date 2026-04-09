# AI Resume Screener

A modular, AI-powered resume screening system that uses semantic similarity matching, NLP-based parsing, and AI interview question generation to streamline candidate evaluation.

## 🆕 What's New: PostgreSQL Integration

**✅ Migrated from MongoDB to PostgreSQL** for better data integrity, relational queries, and industry-standard practices.

**Benefits:**
- 🔒 **Data Integrity** - Foreign keys prevent orphan records
- 📊 **Better Queries** - JOINs for ranking + candidate + job data in one query
- 🚀 **Performance** - Connection pooling handles more concurrent users
- 🔍 **Type Safety** - SQLAlchemy validators catch errors early
- 📈 **Scalability** - Production-ready relational database

**See `POSTGRESQL_SETUP.md` for detailed setup instructions.**

---

## Features

- **🔐 Secure Authentication** — Role-based access control with JWT tokens (Admin & Recruiter roles)
- **👥 Admin Panel** — User management, system settings, and password management
- **🗄️ PostgreSQL Database** - Relational data storage with proper schema design
- **📄 PDF & DOCX Parsing** — Extract text from resume files using `pdfminer.six` and `python-docx`
- **🧠 NLP Information Extraction** — spaCy-powered extraction of name, email, phone, skills, education, and experience
- **🔗 Semantic Similarity Matching** — SentenceTransformer embeddings (`all-MiniLM-L6-v2`) for resume-to-JD matching
- **📊 Skills Gap Analysis** — Identify matched and missing skills per candidate
- **🏆 Candidate Ranking** — Sort, shortlist, and color-code candidates by match score
- **🎤 Interview Question Generation** — GPT-4/Gemini generates 10 tailored questions (technical, behavioral, situational, role-specific)
- **📥 Export to Excel & PDF** — Formatted reports with styling and color coding

## Project Structure

```
resume_screener/
  app.py                  — Streamlit web interface
  auth.py                 — Authentication & user management
  parser.py               — Resume & job description parsing
  matcher.py              — Semantic similarity matching
  ranker.py               — Ranking, shortlisting, export
  question_generator.py   — GPT-4/Gemini interview question generation
  database.py             — PostgreSQL database operations (SQLAlchemy)
  database_postgres.py    — SQLAlchemy ORM models & engine
  migrate_data.py         — MongoDB → PostgreSQL migration script
  test_postgres.py        — PostgreSQL integration tests
  requirements.txt        — Python dependencies
  .env.example            — Environment variables template
  POSTGRESQL_SETUP.md     — Detailed PostgreSQL setup guide
```

## Prerequisites

- Python 3.10+
- **PostgreSQL 14+** (required for database persistence and user storage)
- OpenAI API key or Google Gemini API key (optional, for interview question generation)

## Setup Instructions

### Quick Start

1. **Install PostgreSQL:**
   - Download from: https://www.postgresql.org/download/
   - Remember the password you set for the `postgres` user

2. **Clone or download this project:**
   ```bash
   cd resume_screener
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download the spaCy model:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Create PostgreSQL database:**
   ```bash
   psql -U postgres -c "CREATE DATABASE resume_screener;"
   ```

6. **Set up environment variables:**
   ```bash
   copy .env.example .env
   # Edit .env and update DATABASE_URL with your PostgreSQL password
   ```

7. **Test the database connection:**
   ```bash
   python test_postgres.py
   ```

8. **Run the application:**
   ```bash
   streamlit run app.py
   ```

9. **Open your browser:** The app will be available at `http://localhost:8501`

10. **Login:** Use the default credentials (shown on login page):
    - **Admin:** `admin` / `admin123`
    - **Recruiter:** `recruiter` / `recruiter123`

    ⚠️ **Important:** Change default passwords immediately after first login!

### Detailed PostgreSQL Setup

**See `POSTGRESQL_SETUP.md` for:**
- Step-by-step database setup
- Connection string configuration
- Data migration from MongoDB
- Backup and restore procedures
- Performance optimization tips

## Usage

### 0. Authentication
- Login with your username and password on the authentication page
- **Admin users** have access to the Admin Panel for user management
- **Recruiter users** can access all screening features but not user management
- Change your password via the Admin Panel > System Settings tab

### 1. Upload & Screen
- Paste or upload a **job description**
- Upload multiple **resume files** (PDF or DOCX)
- Click **"Screen Candidates"** to process and match

### 2. Rankings
- View candidates sorted by match score
- Color-coded indicators: 🟢 >70%, 🟡 50–70%, 🔴 <50%
- See matched and missing skills per candidate

### 3. Interview Prep
- Select a screened candidate
- Choose difficulty: Easy / Medium / Hard
- Generate 10 tailored interview questions grouped by category

### 4. Export
- Download results as **Excel** (`.xlsx`) or **PDF**
- Reports include rank, name, score %, skills matched/missing

### 5. Admin Panel (Admin Only)
- **User Management**: Add, edit, and delete users
- **System Settings**: View system information and change your password
- **Role Management**: Assign Admin or Recruiter roles to users

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string (format: `postgresql://user:pass@host:port/dbname`) | **Yes** |
| `JWT_SECRET` | Secret key for JWT token generation (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`) | **Yes** |
| `GEMINI_API_KEY` | Google Gemini API key for interview question generation | Only for Interview Prep feature |
| `GROQ_API_KEY` | Groq API key for interview question generation (default provider) | Only for Interview Prep feature |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 question generation | Only for Interview Prep feature |
| `DB_POOL_SIZE` | Database connection pool size (default: 10) | No |
| `DB_MAX_OVERFLOW` | Max overflow connections (default: 20) | No |

### Database Schema

The PostgreSQL database includes the following tables:

- **`users`** - User authentication and profile data
- **`jobs`** - Job descriptions and parsed requirements
- **`candidates`** - Resume parsing results and candidate information
- **`rankings`** - Screening results linking jobs and candidates with scores

All tables are automatically created on first application startup.

### User Roles

| Role | Permissions |
|------|------------|
| **Admin** | Full access: Resume screening, rankings, interview prep, export, AND user management via Admin Panel |
| **Recruiter** | Standard access: Resume screening, rankings, interview prep, and export (no user management) |

### Data Migration from MongoDB

If you have existing data in MongoDB, use the migration script:

```bash
python migrate_data.py
```

This will:
- Connect to both MongoDB and PostgreSQL
- Migrate all users, jobs, candidates, and rankings
- Skip duplicate records
- Provide detailed migration statistics

### Backup & Restore

**Backup:**
```bash
pg_dump -U postgres resume_screener > backup.sql
```

**Restore:**
```bash
psql -U postgres resume_screener < backup.sql
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Web UI framework |
| `pdfminer.six` | PDF text extraction |
| `python-docx` | DOCX text extraction |
| `spacy` | NLP-based resume parsing |
| `sentence-transformers` | Semantic similarity embeddings |
| `openai` | GPT-4 API for question generation |
| `google-generativeai` | Google Gemini API for question generation |
| **`sqlalchemy`** | **ORM for database operations** |
| **`psycopg2-binary`** | **PostgreSQL adapter** |
| **`alembic`** | **Database migration tool** |
| `openpyxl` | Excel export |
| `fpdf2` | PDF export |
| `scikit-learn` | Utility for ML operations |
| `pandas` | Data manipulation |
| `PyJWT` | JWT token handling |
| `bcrypt` | Password hashing |

## Notes

- The `en_core_web_sm` spaCy model is required for resume parsing — download it with `python -m spacy download en_core_web_sm`
- **PostgreSQL is required** for database persistence and user storage
- GPT-4 question generation requires a valid OpenAI API key and will incur API costs
- Default credentials should be changed immediately after first login
- Database tables are automatically created on first application startup
- Use `python test_postgres.py` to verify database connectivity and operations

## Testing & Verification

Run the test suite to verify PostgreSQL integration:

```bash
python test_postgres.py
```

This will test:
- Database connectivity
- Table creation
- User CRUD operations
- Job/Candidate/Ranking operations
- Database status reporting

---

## 📚 Documentation

This project includes comprehensive documentation:

| Document | Description |
|----------|-------------|
| **[PROJECT_FLOW.md](PROJECT_FLOW.md)** | Complete data flow diagrams and user journey |
| **[TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)** | Deep technical documentation for developers |
| **[POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md)** | Step-by-step PostgreSQL setup guide |
| **[CLIENT_HANDOVER.md](CLIENT_HANDOVER.md)** | Client delivery and handover guide |
| **[MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)** | MongoDB to PostgreSQL migration details |
