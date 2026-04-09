# 📊 Complete Project Flow - AI Resume Screener

This document explains the complete data flow, user journey, and system architecture of the AI Resume Screener application.

---

## 🗺️ Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Application Startup Flow](#application-startup-flow)
3. [User Authentication Flow](#user-authentication-flow)
4. [Resume Screening Pipeline](#resume-screening-pipeline)
5. [Database Storage Flow](#database-storage-flow)
6. [Interview Question Generation](#interview-question-generation)
7. [Export & Reporting](#export--reporting)
8. [Session State Management](#session-state-management)
9. [Error Handling Flow](#error-handling-flow)
10. [Complete Data Flow Diagram](#complete-data-flow-diagram)

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER (Browser)                           │
│              (Admin or Recruiter Role)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Streamlit Web Interface                     │
│                        (app.py)                              │
│                                                              │
│  ┌──────────────┐  ┌──────────┐  ┌─────────────┐  ┌───────┐│
│  │ Upload &     │  │ Rankings │  │ Interview   │  │Export ││
│  │ Screen       │  │          │  │ Prep        │  │       ││
│  └──────┬───────┘  └────┬─────┘  └──────┬──────┘  └───┬───┘│
└─────────┼───────────────┼───────────────┼─────────────┼────┘
          │               │               │             │
          ▼               ▼               ▼             ▼
┌──────────────┐  ┌──────────────┐  ┌───────────┐  ┌────────┐
│  parser.py   │  │  ranker.py   │  │ question_ │  │ ranker │
│  matcher.py  │  │  database.py │  │ generator │  │ .py    │
└──────┬───────┘  └──────┬──────┘  │ .py       │  └────────┘
       │                 │         └─────┬─────┘
       ▼                 ▼               ▼
┌──────────────────────────────────────────────────────────┐
│              Database Layer (SQLite/PostgreSQL)           │
│                   (resume_screener.db)                    │
│                                                           │
│  Tables: users | jobs | candidates | rankings            │
└──────────────────────────────────────────────────────────┘
```

---

## 🚀 Application Startup Flow

When you run `streamlit run app.py`, the following happens:

### **Step 1: Environment Setup**
```
app.py starts
    ↓
load_dotenv() → Loads .env file
    ↓
DATABASE_URL read (defaults to sqlite:///resume_screener.db)
    ↓
AI API Keys loaded (GROQ, GEMINI, OPENAI)
```

### **Step 2: Database Initialization**
```
Import database_postgres.py
    ↓
check_connection() → Tests DB connectivity
    ↓
initialize_database() → Creates tables if not exist
    ↓
Tables created: users, jobs, candidates, rankings
    ↓
Session state: db_initialized = True
```

### **Step 3: Authentication Setup**
```
Import auth.py
    ↓
initialize_auth_session()
    ↓
  - authenticated = False
  - current_user = None
  - auth_token = None
    ↓
initialize_default_users()
    ↓
  - Creates admin/admin123 (if not exists)
  - Creates recruiter/recruiter123 (if not exists)
    ↓
Session state: auth_initialized = True
```

### **Step 4: Session State Initialization**
```
Initialize UI states:
  - screened = False
  - ranked_list = []
  - parsed_resumes = []
  - parsed_jd = None
  - jd_text = ""
```

### **Step 5: Authentication Check**
```
If authenticated == False:
    → Show login page
    → Stop execution
Else:
    → Show main application
```

---

## 🔐 User Authentication Flow

### **Login Process**
```
User enters username + password
    ↓
login_user(username, password) called
    ↓
authenticate_user() → Queries database for user
    ↓
  ┌─ User found? ──NO──→ Return None → Show error
  │
 YES
  ↓
verify_password(password, password_hash)
  │
  ├─ Password wrong? ──→ Return None → Show error
  │
  └─ Password correct?
       ↓
  Update last_login timestamp
       ↓
  create_token(user_data) → Generate JWT token
       ↓
  Set session state:
    - authenticated = True
    - current_user = {user data}
    - auth_token = {JWT token}
       ↓
  st.rerun() → Reload app with authenticated view
```

### **Role-Based Access**
```
After login, check user role:
    ↓
┌─ Admin ──→ Sidebar shows:
│             Upload & Screen | Rankings | Interview Prep | Export | Admin Panel
│
└─ Recruiter ──→ Sidebar shows:
                Upload & Screen | Rankings | Interview Prep | Export
```

### **Logout Process**
```
User clicks "Logout" button
    ↓
logout_user() called
    ↓
Clear session state:
  - authenticated = False
  - current_user = None
  - auth_token = None
  - screened = False
  - ranked_list = []
  - parsed_resumes = []
    ↓
st.rerun() → Redirect to login page
```

---

## 🔍 Resume Screening Pipeline

This is the core feature. Here's the complete flow:

### **Step 1: Input Collection**
```
User provides:
  1. Job Description (Text input OR PDF/DOCX upload)
  2. Resume files (Multiple PDF/DOCX uploads)
    ↓
"Screen Candidates" button clicked
    ↓
Validation:
  ├─ No JD? → Error: "Provide job description first"
  └─ No resumes? → Error: "Upload at least one resume"
```

### **Step 2: Job Description Parsing**
```
parse_job_description(jd_text) called
    ↓
Extract:
  ├─ Job Title (regex patterns: "title:", "position:", etc.)
  ├─ Required Skills (keyword matching against 60+ skills list)
  ├─ Experience Required (regex: "X years of experience")
  └─ Responsibilities (sentence extraction)
    ↓
Store in session state:
  - st.session_state.parsed_jd = {parsed data}
  - st.session_state.jd_text = raw text
```

### **Step 3: Resume Processing**
```
process_uploaded_resumes(uploaded_files) called
    ↓
For each uploaded file:
    ↓
  1. Save to temporary file
       ↓
  2. Extract text:
       ├─ If .pdf → extract_text_from_pdf() [pdfminer.six]
       └─ If .docx → extract_text_from_docx() [python-docx]
       ↓
  3. Parse resume:
       parse_resume(extracted_text)
         ↓
       Extract:
         ├─ Name (4-strategy cascade: regex → header → spaCy NER → strict validation)
         ├─ Email (regex pattern)
         ├─ Phone (regex pattern)
         ├─ Skills (keyword matching against 60+ skills)
         ├─ Education (sentence extraction with edu keywords)
         ├─ Experience (sentence extraction with exp keywords)
         └─ Years of Experience (regex: "X years" or date ranges)
         ↓
  4. Store results:
       - resumes_list: For matching (name, text, skills)
       - parsed_resumes: For display (full parsed data)
         ↓
  5. Delete temporary file (os.unlink)
```

### **Step 4: Semantic Matching**
```
batch_match(resumes_list, jd_text) called
    ↓
For each resume:
    ↓
  1. Load SentenceTransformer model (all-MiniLM-L6-v2)
       ↓
  2. Encode texts to embeddings:
       - resume_embedding = model.encode(resume_text)
       - jd_embedding = model.encode(jd_text)
       ↓
  3. Compute cosine similarity:
       score = cos_sim(resume_embedding, jd_embedding)
       ↓
  4. Skills gap analysis:
       - Compare resume skills vs JD required skills
       - skills_matched = common skills
       - skills_missing = JD skills not in resume
       ↓
  5. Return result:
       {
         "name": "John Doe",
         "score": 0.75,
         "skills_matched": ["Python", "SQL"],
         "skills_missing": ["React", "AWS"]
       }
```

### **Step 5: Ranking**
```
rank_candidates(batch_results) called
    ↓
Sort by score (descending):
    ↓
Result:
  #1 - Alice (0.92)
  #2 - Bob (0.85)
  #3 - Charlie (0.67)
  ...
    ↓
Store in session state:
  - st.session_state.ranked_list = [sorted results]
  - st.session_state.screened = True
```

### **Step 6: Database Storage**
```
Save to database:
    ↓
1. Generate job_id (UUID)
2. save_job(job_data)
   └─ Upsert to 'jobs' table
    ↓
3. For each candidate in ranked_list:
   ├─ Generate candidate_id (UUID)
   ├─ save_candidate(candidate_data)
   │   └─ Upsert to 'candidates' table
   │
   └─ save_ranking(ranking_data)
       └─ Insert to 'rankings' table
          (links job_id + candidate_id + score)
```

---

## 💾 Database Storage Flow

### **SQLite vs PostgreSQL Detection**
```
On app startup:
    ↓
Read DATABASE_URL from .env
    ↓
Check prefix:
    ├─ Starts with "sqlite://"?
    │   └─ YES → Use SQLite
    │       ├─ Engine: StaticPool
    │       ├─ Enable PRAGMA foreign_keys=ON
    │       └─ File: resume_screener.db
    │
    └─ NO → Use PostgreSQL
        ├─ Engine: QueuePool (10 connections)
        ├─ Max overflow: 20
        └─ Connection: postgres://user:pass@host:port/db
```

### **Table Creation Flow**
```
init_db() called
    ↓
SQLAlchemy creates tables:
    ↓
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  user_id VARCHAR(36) UNIQUE,
  username VARCHAR(100) UNIQUE,
  password_hash VARCHAR(255),
  role VARCHAR(50) CHECK (role IN ('admin', 'recruiter')),
  name VARCHAR(200),
  email VARCHAR(255) UNIQUE,
  created_at DATETIME,
  last_login DATETIME,
  is_active BOOLEAN
);
    ↓
CREATE TABLE jobs (
  id INTEGER PRIMARY KEY,
  job_id VARCHAR(36) UNIQUE,
  job_title VARCHAR(255),
  description TEXT,
  required_skills TEXT,  -- JSON string
  experience_required INTEGER,
  created_at DATETIME,
  updated_at DATETIME
);
    ↓
CREATE TABLE candidates (
  id INTEGER PRIMARY KEY,
  candidate_id VARCHAR(36) UNIQUE,
  name VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(50),
  skills TEXT,  -- JSON string
  education TEXT,  -- JSON string
  experience TEXT,  -- JSON string
  years_of_experience INTEGER,
  resume_text TEXT,
  created_at DATETIME,
  updated_at DATETIME
);
    ↓
CREATE TABLE rankings (
  id INTEGER PRIMARY KEY,
  ranking_id VARCHAR(36) UNIQUE,
  job_id VARCHAR(36) REFERENCES jobs(job_id) ON DELETE CASCADE,
  candidate_id VARCHAR(36) REFERENCES candidates(candidate_id) ON DELETE CASCADE,
  score FLOAT CHECK (score >= 0 AND score <= 1),
  skills_matched TEXT,  -- JSON string
  skills_missing TEXT,  -- JSON string
  rank INTEGER,
  created_at DATETIME
);
```

### **Data Storage Example**
```
User screens 3 resumes for "Software Engineer" position
    ↓
Database operations:
    ↓
1. INSERT INTO jobs:
   {
     job_id: "job_a1b2c3d4",
     job_title: "Software Engineer",
     required_skills: '["Python", "SQL", "React"]',
     experience_required: 3
   }
    ↓
2. INSERT INTO candidates (3 times):
   {
     candidate_id: "cand_e5f6g7h8",
     name: "John Doe",
     email: "john@example.com",
     skills: '["Python", "Django", "PostgreSQL"]',
     years_of_experience: 5
   }
    ↓
3. INSERT INTO rankings (3 times):
   {
     ranking_id: "rank_i9j0k1l2",
     job_id: "job_a1b2c3d4",
     candidate_id: "cand_e5f6g7h8",
     score: 0.85,
     skills_matched: '["Python", "SQL"]',
     skills_missing: '["React"]',
     rank: 1
   }
```

---

## 🎤 Interview Question Generation

### **Flow**
```
User navigates to "Interview Prep" page
    ↓
Select candidate from dropdown
    ↓
Select difficulty: Easy / Medium / Hard
    ↓
Click "Generate Questions"
    ↓
generate_interview_questions(
  candidate_skills=["Python", "SQL"],
  job_title="Software Engineer",
  experience_years=5,
  difficulty="medium",
  provider="groq"  // default
)
    ↓
Check provider:
    ├─ "groq" → Use Groq API (llama-3.3-70b-versatile)
    ├─ "gemini" → Use Google Gemini (gemini-2.5-flash)
    └─ "openai" → Use OpenAI (gpt-4)
    ↓
Send prompt to AI:
  "Generate 10 interview questions for a Software Engineer 
   with 5 years experience, skills in Python and SQL,
   difficulty: medium. Format as JSON."
    ↓
AI returns:
  [
    {"question": "...", "type": "technical", 
     "difficulty": "medium", 
     "expected_answer_hints": ["...", "..."]},
    ...
  ]
    ↓
Parse and validate JSON
    ↓
Display grouped by category:
  ├─ Technical (3 questions)
  ├─ Behavioral (3 questions)
  ├─ Situational (2 questions)
  └─ Role-Specific (2 questions)
```

---

## 📥 Export & Reporting

### **Excel Export**
```
User clicks "Export" → "Excel Export"
    ↓
export_to_excel(ranked_list, "candidate_rankings.xlsx")
    ↓
Create workbook with openpyxl:
    ├─ Headers: Rank, Name, Score %, Skills Matched, Skills Missing
    ├─ Style header row (blue background, white bold text)
    ├─ For each candidate:
    │   ├─ Color-code score cell:
    │   │   ├─ Green if >= 70%
    │   │   ├─ Yellow if >= 50%
    │   │   └─ Red if < 50%
    │   └─ Add borders to all cells
    ├─ Freeze header row
    └─ Adjust column widths
    ↓
Serve file via st.download_button
    ↓
Delete file after download (os.remove)
```

### **PDF Export**
```
User clicks "Export" → "PDF Export"
    ↓
export_to_pdf(ranked_list, "candidate_rankings.pdf")
    ↓
Create PDF with fpdf2:
    ├─ Custom header: "AI Resume Screener - Candidate Rankings"
    ├─ Summary section:
    │   ├─ Total Candidates: X
    │   └─ Average Score: Y%
    ├─ Table:
    │   ├─ Headers with blue background
    │   ├─ Alternating row colors (white/light gray)
    │   └─ Auto page-break handling
    └─ Footer: Page numbers
    ↓
Serve file via st.download_button
    ↓
Delete file after download (os.remove)
```

---

## 🧠 Session State Management

### **Session State Variables**

| Variable | Type | Purpose | Set When |
|----------|------|---------|----------|
| `auth_initialized` | bool | Prevents re-initialization | App startup |
| `db_initialized` | bool | Prevents re-initialization | App startup |
| `authenticated` | bool | User login status | After login |
| `current_user` | dict | Logged-in user data | After login |
| `auth_token` | str | JWT token | After login |
| `screened` | bool | Has screening been done? | After screening |
| `ranked_list` | list | Sorted candidate results | After screening |
| `parsed_resumes` | list | Full parsed resume data | After file upload |
| `parsed_jd` | dict | Parsed job description | After JD input |
| `jd_text` | str | Raw job description text | After JD input |
| `current_job_id` | str | Last screening job ID | After screening |
| `generated_questions` | list | Interview questions | After generation |

### **Session Lifecycle**
```
App Starts → Initialize all states to defaults
    ↓
User Logs In → Set auth states
    ↓
User Uploads Files → Set parsed_resumes, parsed_jd
    ↓
User Screens → Set ranked_list, screened=True, current_job_id
    ↓
User Generates Questions → Set generated_questions
    ↓
User Logs Out → Clear ALL session states
    ↓
App Restarts → Re-initialize to defaults
```

---

## ⚠️ Error Handling Flow

### **File Processing Errors**
```
For each uploaded file:
    try:
        extract text
        parse resume
        add to results
    except Exception as e:
        st.error(f"Error processing {filename}: {str(e)}")
        continue (process next file)
```

### **Database Errors**
```
try:
    save to database
except Exception as db_err:
    st.warning(f"Screening successful, but failed to save: {str(db_err)}")
    // Screening still works, just not saved
```

### **AI API Errors**
```
try:
    generate questions via API
except Exception as e:
    st.error(f"Failed to generate questions: {str(e)}")
    questions = None
```

### **Authentication Errors**
```
if not authenticated:
    st.warning("Please login to access this page.")
    show_login_page()
    st.stop()
```

---

## 📊 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        START APP                             │
│              streamlit run app.py                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  1. LOAD ENVIRONMENT                                         │
│     - Read .env file                                         │
│     - Load DATABASE_URL, API keys, JWT secret               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  2. INITIALIZE DATABASE                                      │
│     - Create engine (SQLite/PostgreSQL)                      │
│     - Create tables: users, jobs, candidates, rankings       │
│     - Test connection                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  3. INITIALIZE AUTHENTICATION                                │
│     - Create default users (admin, recruiter)               │
│     - Check if already logged in                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
     NOT LOGGED IN          LOGGED IN
            │                     │
            │                     ▼
            │            ┌────────────────┐
            │            │ Show Sidebar   │
            │            │ Navigation     │
            │            └────────┬───────┘
            │                     │
            ▼                     ▼
┌──────────────────┐   ┌──────────────────────────────────┐
│  LOGIN PAGE      │   │  USER SELECTS PAGE               │
│                  │   │                                  │
│  - Username      │   │  ┌─ Upload & Screen              │
│  - Password      │   │  ├─ Rankings                     │
│  - Submit        │   │  ├─ Interview Prep               │
│                  │   │  └─ Export                       │
└────────┬─────────┘   └─────────┬────────────────────────┘
         │                       │
         │         ┌─────────────┼──────────────┐
         │         │             │              │
         │         ▼             ▼              ▼
         │  ┌──────────┐  ┌──────────┐  ┌──────────┐
         │  │ UPLOAD & │  │ RANKINGS │  │ INTERVIEW│
         │  │ SCREEN   │  │          │  │ PREP     │
         │  └────┬─────┘  └────┬─────┘  └────┬─────┘
         │       │             │             │
         │       ▼             ▼             ▼
         │  ┌──────────┐  ┌──────────┐  ┌──────────┐
         │  │ Parse JD │  │ Display  │  │ Generate │
         │  │ Parse    │  │ Rankings │  │ Questions│
         │  │ Resumes  │  │ (colors) │  │ via AI   │
         │  │ Match    │  │          │  │          │
         │  │ Rank     │  │          │  │          │
         │  │ Save DB  │  │          │  │          │
         │  └────┬─────┘  └────┬─────┘  └────┬─────┘
         │       │             │             │
         │       └─────────────┴─────────────┘
         │                       │
         │                       ▼
         │              ┌──────────────┐
         │              │ EXPORT       │
         │              │ Excel / PDF  │
         │              └──────┬───────┘
         │                     │
         └─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  DATA PERSISTED IN DATABASE                                  │
│  (resume_screener.db for SQLite)                             │
│                                                              │
│  - Users (login credentials)                                 │
│  - Jobs (descriptions)                                       │
│  - Candidates (resumes)                                      │
│  - Rankings (screening results)                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Takeaways

1. **Modular Design**: Each module has a single responsibility (parsing, matching, ranking, etc.)
2. **Dual Database Support**: Automatically switches between SQLite and PostgreSQL based on `.env`
3. **Session-Based UI**: Streamlit reruns the entire script on every interaction, so state management is crucial
4. **AI-Powered**: Uses SentenceTransformer for matching, LLMs for question generation
5. **Production-Ready**: Proper error handling, connection pooling, and data validation

---

**For technical implementation details, see `TECHNICAL_GUIDE.md`**
