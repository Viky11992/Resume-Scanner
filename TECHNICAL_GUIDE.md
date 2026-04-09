# 🔧 Technical Guide - AI Resume Screener

Complete technical documentation for developers, covering architecture, modules, database schema, AI models, deployment, and best practices.

---

## 📑 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Module Documentation](#module-documentation)
   - 5.1 [database_postgres.py](#51-database_postgrespy)
   - 5.2 [database.py](#52-databasepy)
   - 5.3 [auth.py](#53-authpy)
   - 5.4 [parser.py](#54-parserpy)
   - 5.5 [matcher.py](#55-matcherpy)
   - 5.6 [ranker.py](#56-rankerpy)
   - 5.7 [question_generator.py](#57-question_generatorpy)
   - 5.8 [app.py](#58-apppy)
6. [Database Schema](#database-schema)
7. [AI Models & Configuration](#ai-models--configuration)
8. [Environment Variables](#environment-variables)
9. [API Integrations](#api-integrations)
10. [Security Considerations](#security-considerations)
11. [Performance Optimization](#performance-optimization)
12. [Testing Guide](#testing-guide)
13. [Deployment Guide](#deployment-guide)
14. [Troubleshooting](#troubleshooting)
15. [Future Enhancements](#future-enhancements)

---

## 📋 Project Overview

**AI Resume Screener** is a web-based application that automates the initial screening of job candidates. It uses Natural Language Processing (NLP) and semantic similarity matching to evaluate resumes against job descriptions, ranks candidates by match score, and generates tailored interview questions.

### **Key Features**
- ✅ Role-based authentication (Admin/Recruiter)
- ✅ PDF & DOCX resume parsing
- ✅ Semantic similarity matching using SentenceTransformer
- ✅ Skills gap analysis
- ✅ Candidate ranking with color-coded scores
- ✅ AI-powered interview question generation (Groq/Gemini/OpenAI)
- ✅ Excel & PDF export
- ✅ Dual database support (SQLite for development, PostgreSQL for production)

### **Use Cases**
- HR departments screening hundreds of resumes
- Recruitment agencies matching candidates to multiple positions
- Hiring managers preparing for interviews
- FYP/academic projects demonstrating AI integration

---

## 🏗️ System Architecture

### **Architecture Pattern**
Modular Monolith with Layered Architecture:

```
┌─────────────────────────────────────────────┐
│           Presentation Layer                │
│         (Streamlit UI - app.py)             │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│           Business Logic Layer              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ parser   │  │ matcher  │  │ ranker   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────────────────────────────────┐   │
│  │  question_generator + auth           │   │
│  └──────────────────────────────────────┘   │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│           Data Access Layer                 │
│         (database.py)                       │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│           Database Layer                    │
│    (SQLite / PostgreSQL via SQLAlchemy)     │
└─────────────────────────────────────────────┘
```

### **Design Patterns Used**
1. **Singleton Pattern**: Database engine, AI models (cached via `@st.cache_resource`)
2. **Factory Pattern**: Session creation, AI provider selection
3. **Context Manager**: Database sessions (`session_scope()`)
4. **Strategy Pattern**: Multiple AI providers (Groq/Gemini/OpenAI)
5. **Repository Pattern**: Database CRUD operations

---

## 💻 Technology Stack

### **Backend**
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Core programming language |
| **Streamlit** | >=1.30.0 | Web framework (reactive UI) |
| **SQLAlchemy** | >=2.0.0 | ORM for database operations |
| **psycopg2-binary** | >=2.9.9 | PostgreSQL adapter |
| **PyJWT** | >=2.8.0 | JWT token management |
| **bcrypt** | >=4.1.2 | Password hashing |

### **AI & NLP**
| Technology | Model | Purpose |
|------------|-------|---------|
| **SentenceTransformers** | all-MiniLM-L6-v2 | Semantic similarity embeddings |
| **spaCy** | en_core_web_sm | NER, sentence segmentation, POS tagging |
| **Groq API** | llama-3.3-70b-versatile | Interview question generation (default) |
| **Google Gemini** | gemini-2.5-flash | Alternative AI for questions |
| **OpenAI** | gpt-4 | Alternative AI for questions |

### **File Processing**
| Library | Purpose |
|---------|---------|
| **pdfminer.six** | PDF text extraction |
| **python-docx** | DOCX text extraction |

### **Export**
| Library | Purpose |
|---------|---------|
| **openpyxl** | Excel file creation with styling |
| **fpdf2** | PDF report generation |

### **Utilities**
| Library | Purpose |
|---------|---------|
| **python-dotenv** | Environment variable loading |
| **uuid** | Unique ID generation |

---

## 📁 Project Structure

```
resume_screener/
│
├── 📄 app.py                      # Main Streamlit application (entry point)
├── 🔐 auth.py                     # Authentication & user management
├── 💾 database.py                 # Database CRUD operations
├── 🗄️ database_postgres.py        # SQLAlchemy models & engine
├── 📝 parser.py                   # Resume & job description parsing
├── 🔗 matcher.py                  # Semantic similarity matching
├── 🏆 ranker.py                   # Ranking & export (Excel/PDF)
├── 🤖 question_generator.py       # AI interview question generation
│
├── 📦 requirements.txt            # Python dependencies
├── ⚙️ .env                        # Environment variables (local)
├── ⚙️ .env.example                # Environment variables template
│
├── 📂 .streamlit/
│   └── config.toml                # Streamlit runtime config
│
├── 📚 Documentation/
│   ├── README.md                  # Project overview & setup
│   ├── PROJECT_FLOW.md            # Complete data flow diagrams
│   ├── TECHNICAL_GUIDE.md         # This file
│   ├── POSTGRESQL_SETUP.md        # PostgreSQL setup guide
│   ├── CLIENT_HANDOVER.md         # Client delivery guide
│   └── MIGRATION_SUMMARY.md       # MongoDB→PostgreSQL migration
│
├── 🧪 test_postgres.py            # Database integration tests
├── 🔄 migrate_data.py             # MongoDB→PostgreSQL migration script
└── 📊 resume_screener.db          # SQLite database (created on first run)
```

---

## 📖 Module Documentation

### 5.1 `database_postgres.py`

**Purpose**: SQLAlchemy ORM models and database engine setup.

**Key Components**:

#### **Models**
```python
class User(Base):
    # Authentication & user profiles
    # Constraints: UNIQUE(username, email), CHECK(role)
    # Indexes: username, email, user_id

class Job(Base):
    # Job descriptions
    # Constraints: UNIQUE(job_id)
    # Relationships: 1 Job → ∞ Rankings

class Candidate(Base):
    # Resume parsing results
    # Constraints: UNIQUE(candidate_id)
    # Indexes: candidate_id, email, name
    # Relationships: 1 Candidate → ∞ Rankings

class Ranking(Base):
    # Screening results
    # Constraints: UNIQUE(ranking_id), CHECK(0 <= score <= 1)
    # Foreign Keys: job_id → jobs.job_id, candidate_id → candidates.candidate_id
    # Indexes: job_id, candidate_id, score, composite(job_id, score)
```

#### **Database Engine**
```python
def get_engine():
    # Auto-detects SQLite vs PostgreSQL
    # SQLite: StaticPool + PRAGMA foreign_keys=ON
    # PostgreSQL: QueuePool (10 connections, max_overflow 20)
    
def session_scope():
    # Context manager for transactions
    # Automatically commits or rollback
    # Closes session after use
```

**Key Functions**:
- `init_db()` - Create all tables
- `check_connection()` - Test connectivity
- `get_session()` - Get fresh database session

---

### 5.2 `database.py`

**Purpose**: High-level database operations (CRUD).

**Functions**:

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `save_job()` | `job_data: dict` | `str: job_id` | Upsert job by job_id |
| `save_candidate()` | `candidate_data: dict` | `str: candidate_id` | Upsert candidate by candidate_id |
| `save_ranking()` | `ranking_data: dict` | `str: ranking_id` | Upsert ranking by ranking_id |
| `get_all_rankings()` | `job_id: str` | `list[dict]` | Get rankings sorted by score DESC |
| `get_rankings_with_details()` | `job_id: str` | `list[dict]` | JOIN rankings + candidates + jobs |
| `initialize_database()` | None | `bool` | Create tables + test connection |
| `get_database_status()` | None | `dict` | Connection status + record counts |

**Data Serialization**:
- Lists (skills, education, etc.) → JSON strings before storage
- JSON strings → Lists after retrieval via `json.loads()`

---

### 5.3 `auth.py`

**Purpose**: Authentication, authorization, and user management.

**Password Security**:
```python
hash_password(password) → bcrypt hash
verify_password(password, hash) → bool
```

**User Management**:
```python
add_user(username, password, role, name, email)
get_all_users()
get_user_by_username(username)
update_user(user_id, **kwargs)
delete_user(user_id)
```

**Authentication Flow**:
```python
authenticate_user(username, password) → user dict or None
create_token(user_data) → JWT string
decode_token(token) → payload dict or None
```

**Session Management**:
```python
initialize_auth_session()
login_user(username, password) → bool
logout_user()
require_auth(roles=None) → decorator-like guard
```

**UI Components**:
```python
show_login_page()
show_user_profile()
show_admin_panel()
```

**Security Features**:
- bcrypt password hashing (cost factor 12)
- JWT tokens with 24-hour expiry
- Role-based access control (Admin/Recruiter)
- Cannot delete last admin user
- Password minimum 6 characters

---

### 5.4 `parser.py`

**Purpose**: Extract structured data from resumes and job descriptions.

**File Extraction**:
```python
extract_text_from_pdf(file_path) → str
extract_text_from_docx(file_path) → str
```

**NLP Model**:
```python
get_nlp_model() → spacy.Language
# Cached via @st.cache_resource
# Model: en_core_web_sm
```

**Resume Parsing**:
```python
parse_resume(text) → dict:
    {
        "name": str,
        "email": str,
        "phone": str,
        "skills": list[str],
        "education": list[str],
        "experience": list[str],
        "years_of_experience": int
    }
```

**Name Extraction (4-Strategy Cascade)**:
1. **Regex**: Match "Name:" patterns in first 5 lines
2. **Header Analysis**: First 5 non-empty lines, check capitalization, validate with spaCy NER
3. **spaCy NER (First 200 chars)**: Look for PERSON entities
4. **Full-text NER**: Strict validation (2-4 words, letters only, no titles)

**Skill Matching**:
- Hardcoded list of 60+ skills
- Case-insensitive keyword matching
- Skills: Python, JavaScript, React, SQL, AWS, Docker, etc.

**Job Description Parsing**:
```python
parse_job_description(text) → dict:
    {
        "job_title": str,
        "required_skills": list[str],
        "experience_required": int,
        "responsibilities": list[str]
    }
```

---

### 5.5 `matcher.py`

**Purpose**: Semantic similarity matching between resumes and job descriptions.

**AI Model**:
```python
get_model() → SentenceTransformer
# Model: all-MiniLM-L6-v2 (22M parameters)
# Cached via @st.cache_resource
# Output: 384-dimensional embeddings
```

**Functions**:

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `compute_similarity()` | resume_text, jd_text | float [0, 1] | Cosine similarity of embeddings |
| `batch_match()` | resumes_list, jd_text | list[dict] | Match multiple resumes to one JD |
| `skills_gap_analysis()` | resume_skills, required_skills | dict | Matched vs missing skills |

**Matching Algorithm**:
```python
1. Encode texts: embedding = model.encode(text, convert_to_tensor=True)
2. Compute cosine similarity: score = cos_sim(resume_emb, jd_emb)
3. Clamp to [0, 1]: max(0.0, min(1.0, score.item()))
4. Skills gap: set(resume_skills) ∩ set(required_skills)
```

**Performance**:
- Single match: ~50ms (CPU)
- Batch of 10: ~200ms (batched encoding)

---

### 5.6 `ranker.py`

**Purpose**: Candidate ranking and export functionality.

**Functions**:
```python
rank_candidates(batch_results) → list[dict]
# Sort by score descending

shortlist_candidates(ranked_list, top_n=10) → list[dict]
# Return top N candidates

export_to_excel(ranked_list, output_path)
# Styled workbook with color-coded scores

export_to_pdf(ranked_list, output_path)
# Formatted PDF report with headers/footers
```

**Excel Styling**:
- Header: Blue (#2F5496), white bold text
- Score cells: Green (≥70%), Yellow (≥50%), Red (<50%)
- Frozen header row
- Auto column widths

**PDF Features**:
- Custom header with title
- Summary section (total candidates, avg score)
- Alternating row colors
- Auto page breaks with header redraw
- Footer with page numbers

---

### 5.7 `question_generator.py`

**Purpose**: Generate tailored interview questions using AI APIs.

**Supported Providers**:

| Provider | Model | Env Variable | Cost |
|----------|-------|--------------|------|
| **Groq** | llama-3.3-70b-versatile | `GROQ_API_KEY` | Free tier available |
| **Google** | gemini-2.5-flash | `GEMINI_API_KEY` | Free tier available |
| **OpenAI** | gpt-4 | `OPENAI_API_KEY` | Paid |

**Main Function**:
```python
generate_interview_questions(
    candidate_skills: list[str],
    job_title: str,
    experience_years: int,
    difficulty: str = "medium",  # easy, medium, hard
    provider: str = "groq"       # groq, gemini, openai
) → list[dict]
```

**Output Format**:
```python
[
    {
        "question": "Explain the difference between...",
        "type": "technical",  # technical/behavioral/situational/role-specific
        "difficulty": "medium",
        "expected_answer_hints": ["Hint 1", "Hint 2", "Hint 3"]
    },
    # ... 10 questions total
    # Distribution: 3 technical, 3 behavioral, 2 situational, 2 role-specific
]
```

**Prompt Engineering**:
```
System prompt requests:
- Exactly 10 questions
- JSON format
- Specific difficulty
- Based on candidate skills and job title
- Experience-appropriate questions
- Answer hints for interviewers
```

**Error Handling**:
- Input validation (non-empty skills, valid difficulty)
- API key check before calling
- JSON parsing with markdown stripping
- Structure validation (10 items, required keys)

---

### 5.8 `app.py`

**Purpose**: Main Streamlit application orchestrating all modules.

**Page Configuration**:
```python
st.set_page_config(
    page_title="AI Resume Screener",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

**Initialization Sequence**:
1. Load environment variables
2. Initialize database (create tables)
3. Initialize authentication (create default users)
4. Check authentication status
5. Initialize session states

**Navigation**:
```python
Sidebar radio:
  - Admin: Upload & Screen | Rankings | Interview Prep | Export | Admin Panel
  - Recruiter: Upload & Screen | Rankings | Interview Prep | Export
```

**Screening Pipeline**:
```python
1. Parse job description
2. Process uploaded resumes (extract text, parse)
3. Batch match (semantic similarity + skills gap)
4. Rank candidates (sort by score)
5. Save to database (job, candidates, rankings)
6. Display results
```

**Helper Functions**:
```python
process_uploaded_resumes(uploaded_files)
# Returns: (resumes_list for matching, parsed_resumes for display)
# Handles: PDF/DOCX extraction, temp file cleanup
```

---

## 🗄️ Database Schema

### **Entity Relationship Diagram**

```
┌──────────────┐
│    users     │
├──────────────┤
│ id (PK)      │
│ user_id      │
│ username     │── UNIQUE
│ password_hash│
│ role         │── CHECK (admin/recruiter)
│ name         │
│ email        │── UNIQUE
│ created_at   │
│ last_login   │
│ is_active    │
└──────────────┘

┌──────────────┐                    ┌──────────────────┐
│    jobs      │                    │    candidates    │
├──────────────┤                    ├──────────────────┤
│ id (PK)      │                    │ id (PK)          │
│ job_id       │── UNIQUE           │ candidate_id     │── UNIQUE
│ job_title    │                    │ name             │
│ description  │                    │ email            │
│ required_    │                    │ phone            │
│   skills     │── JSON             │ skills           │── JSON
│ experience_  │                    │ education        │── JSON
│   required   │                    │ experience       │── JSON
│ created_at   │                    │ years_of_exp     │
│ updated_at   │                    │ resume_text      │
└──────┬───────┘                    │ created_at       │
       │                           │ updated_at       │
       │                           └────────┬─────────┘
       │                                    │
       │ 1                                  │ 1
       │                                    │
       ▼ ∞                                  ▼ ∞
┌────────────────────────────────────────────────┐
│                  rankings                       │
├────────────────────────────────────────────────┤
│ id (PK)                                        │
│ ranking_id    ────────────────────── UNIQUE    │
│ job_id        ────────── FK → jobs.job_id      │
│ candidate_id  ────────── FK → candidates.id    │
│ score         ────────── CHECK (0-1)           │
│ skills_matched ───────── JSON                  │
│ skills_missing ────────── JSON                 │
│ rank                                         │
│ created_at                                   │
└────────────────────────────────────────────────┘
```

### **Indexes**

| Table | Index | Purpose |
|-------|-------|---------|
| users | username, email | Fast login lookups |
| jobs | job_id, created_at | Job retrieval, sorting |
| candidates | candidate_id, email, name | Candidate search |
| rankings | job_id, candidate_id, score | Filtering, sorting |
| rankings | (job_id, score) composite | Job-specific ranking queries |

### **Constraints**

| Constraint | Table | Rule |
|------------|-------|------|
| UNIQUE | users.username | No duplicate usernames |
| UNIQUE | users.email | No duplicate emails |
| UNIQUE | jobs.job_id | No duplicate job IDs |
| UNIQUE | candidates.candidate_id | No duplicate candidate IDs |
| CHECK | users.role | Must be 'admin' or 'recruiter' |
| CHECK | rankings.score | Must be between 0 and 1 |
| FOREIGN KEY | rankings.job_id | CASCADE DELETE |
| FOREIGN KEY | rankings.candidate_id | CASCADE DELETE |

---

## 🤖 AI Models & Configuration

### **1. SentenceTransformer (all-MiniLM-L6-v2)**

**Specifications**:
- **Parameters**: 22 million
- **Dimensions**: 384
- **Size**: ~80 MB
- **Speed**: ~2800 sentences/sec on CPU
- **Accuracy**: 58.8% on STS benchmark

**Usage**:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(["text1", "text2"], convert_to_tensor=True)
similarity = util.cos_sim(embeddings[0], embeddings[1])
```

**Why This Model?**
- ✅ Lightweight (fast loading)
- ✅ Works on CPU (no GPU needed)
- ✅ Good accuracy for short texts
- ✅ Apache 2.0 license (commercial use OK)

---

### **2. spaCy (en_core_web_sm)**

**Specifications**:
- **Size**: ~12 MB
- **Components**: Tokenizer, POS tagger, NER, parser
- **Speed**: ~5000 words/sec on CPU

**Usage in Project**:
```python
import spacy
nlp = spacy.load("en_core_web_sm")
doc = nlp(resume_text)

# Name extraction
for ent in doc.ents:
    if ent.label_ == "PERSON":
        candidate_name = ent.text

# Sentence segmentation
for sent in doc.sents:
    if "engineer" in sent.text.lower():
        experiences.append(sent.text)
```

---

### **3. LLM Providers (Interview Questions)**

| Model | Context Window | Speed | Cost | Best For |
|-------|---------------|-------|------|----------|
| **Llama 3.3 70B (Groq)** | 128K | ⚡ Fastest | Free tier | Default choice |
| **Gemini 2.5 Flash** | 1M | ⚡ Fast | Free tier | Long contexts |
| **GPT-4 (OpenAI)** | 128K | 🐢 Slower | Paid | Highest quality |

**Selection Logic**:
```python
if provider == "groq":
    return generate_via_groq(...)  # Default
elif provider == "gemini":
    return generate_via_gemini(...)
elif provider == "openai":
    return generate_via_openai(...)
```

---

## ⚙️ Environment Variables

### **Required Variables**

| Variable | Type | Example | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | `sqlite:///resume_screener.db` | Database connection string |
| `JWT_SECRET` | string | `your-secret-key` | JWT signing key |

### **Optional Variables**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GROQ_API_KEY` | string | None | Groq API key (for questions) |
| `GEMINI_API_KEY` | string | None | Google Gemini API key |
| `OPENAI_API_KEY` | string | None | OpenAI API key |
| `DB_POOL_SIZE` | int | 10 | PostgreSQL pool size |
| `DB_MAX_OVERFLOW` | int | 20 | PostgreSQL max overflow |
| `DB_POOL_TIMEOUT` | int | 30 | Pool timeout (seconds) |
| `DB_POOL_RECYCLE` | int | 1800 | Connection recycle interval (seconds) |

### **Generate Secure Values**

**JWT Secret**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Database URL Examples**:
```env
# SQLite (Development)
DATABASE_URL=sqlite:///resume_screener.db

# PostgreSQL (Production)
DATABASE_URL=postgresql://postgres:password@localhost:5432/resume_screener

# Neon DB (Cloud)
DATABASE_URL=postgresql://user:password@ep-xyz.region.neon.tech/dbname
```

---

## 🔌 API Integrations

### **1. Groq API**

**Setup**:
1. Sign up at https://console.groq.com/
2. Create API key
3. Add to `.env`: `GROQ_API_KEY=gsk_...`

**Usage**:
```python
from groq import Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    max_tokens=2000
)
```

**Rate Limits** (Free Tier):
- 30 requests/minute
- 14,400 requests/day

---

### **2. Google Gemini API**

**Setup**:
1. Sign up at https://aistudio.google.com/
2. Create API key
3. Add to `.env`: `GEMINI_API_KEY=...`

**Usage**:
```python
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content(prompt)
```

**Rate Limits** (Free Tier):
- 15 requests/minute
- 1,500 requests/day

---

### **3. OpenAI API**

**Setup**:
1. Sign up at https://platform.openai.com/
2. Add billing info (paid)
3. Create API key
4. Add to `.env`: `OPENAI_API_KEY=sk-...`

**Usage**:
```python
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    max_tokens=2000
)
```

**Cost**: ~$0.03 per 1K tokens (~$0.30 per question generation)

---

## 🔒 Security Considerations

### **Password Security**
- ✅ bcrypt hashing with random salt
- ✅ Minimum 6 characters enforced
- ✅ Passwords never stored in plain text
- ⚠️ **Recommendation**: Increase minimum to 8 characters

### **JWT Security**
- ✅ HS256 algorithm
- ✅ 24-hour expiry
- ⚠️ **Issue**: JWT_SECRET in `.env` should be 32+ characters
- ⚠️ **Issue**: Tokens not validated on every request (only checked at login)

### **Database Security**
- ✅ Parameterized queries (SQLAlchemy prevents SQL injection)
- ✅ Foreign key constraints (data integrity)
- ⚠️ **Recommendation**: Encrypt sensitive fields (email, phone) in production

### **File Upload Security**
- ✅ Temp files deleted after processing
- ✅ File type validation (PDF/DOCX only)
- ⚠️ **Recommendation**: Add file size limit (e.g., 10 MB)
- ⚠️ **Recommendation**: Scan for malware in production

### **API Key Security**
- ✅ Stored in `.env` (not hardcoded)
- ⚠️ **Recommendation**: Add validation on startup (fail fast if missing)
- ⚠️ **Issue**: `.env` should be in `.gitignore`

---

## ⚡ Performance Optimization

### **Current Optimizations**

1. **Model Caching**:
   ```python
   @st.cache_resource
   def get_nlp_model():
       return spacy.load("en_core_web_sm")
   
   @st.cache_resource
   def get_model():
       return SentenceTransformer('all-MiniLM-L6-v2')
   ```

2. **Connection Pooling** (PostgreSQL):
   - 10 persistent connections
   - 20 overflow connections
   - 30-minute recycle interval

3. **Batch Processing**:
   - Resumes encoded in batches for SentenceTransformer
   - Database operations use transactions (session_scope)

### **Optimization Recommendations**

1. **Add File Size Limits**:
   ```python
   MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
   if uploaded_file.size > MAX_FILE_SIZE:
       st.error("File too large")
   ```

2. **Add Pagination** for large result sets:
   ```python
   def get_rankings_page(job_id, page=1, per_page=20):
       offset = (page - 1) * per_page
       return session.query(Ranking).offset(offset).limit(per_page).all()
   ```

3. **Add Caching** for API responses:
   ```python
   @st.cache_data(ttl=3600)
   def cached_generate_questions(skills, job_title, exp, difficulty):
       return generate_interview_questions(...)
   ```

4. **Use Async** for file processing:
   ```python
   import asyncio
   async def process_resume_async(file):
       # Non-blocking I/O
   ```

### **Performance Benchmarks**

| Operation | Time (avg) | Notes |
|-----------|-----------|-------|
| Load spaCy model | ~500ms | Cached after first load |
| Load SentenceTransformer | ~800ms | Cached after first load |
| Parse single resume | ~100ms | Depends on text length |
| Match 10 resumes | ~200ms | Batch encoding |
| Save to database | ~50ms | SQLite, single transaction |
| Generate questions (Groq) | ~2s | API latency |
| Export to Excel | ~100ms | 10 candidates |
| Export to PDF | ~150ms | 10 candidates |

---

## 🧪 Testing Guide

### **Run Integration Tests**
```bash
python test_postgres.py
```

**Tests Covered**:
- ✅ Database connectivity
- ✅ Table creation
- ✅ User CRUD operations
- ✅ Job/Candidate/Ranking save & retrieve
- ✅ Database status reporting

### **Manual Testing Checklist**

**Authentication**:
- [ ] Login with admin/admin123
- [ ] Login with recruiter/recruiter123
- [ ] Login with wrong credentials (should fail)
- [ ] Logout and verify redirect to login
- [ ] Add new user via Admin Panel
- [ ] Delete user (not last admin)
- [ ] Change password

**Resume Screening**:
- [ ] Upload JD (text input)
- [ ] Upload JD (file upload)
- [ ] Upload 1 resume (PDF)
- [ ] Upload 1 resume (DOCX)
- [ ] Upload multiple resumes
- [ ] Screen candidates
- [ ] Verify results in Rankings page
- [ ] Check color coding (green/yellow/red)

**Interview Questions**:
- [ ] Select candidate
- [ ] Select difficulty (Easy/Medium/Hard)
- [ ] Generate questions
- [ ] Verify 10 questions displayed
- [ ] Check all 4 categories present

**Export**:
- [ ] Download Excel file
- [ ] Open Excel and verify formatting
- [ ] Download PDF file
- [ ] Open PDF and verify layout

**Database**:
- [ ] Check `resume_screener.db` exists
- [ ] Open with SQLite viewer
- [ ] Verify users table has data
- [ ] Verify jobs table has data
- [ ] Verify candidates table has data
- [ ] Verify rankings table has data

---

## 🚀 Deployment Guide

### **Option 1: Local Deployment (Recommended for FYP)**

**Requirements**:
- Python 3.10+
- 4 GB RAM minimum
- Internet connection (for AI APIs)

**Steps**:
```bash
# 1. Clone project
cd resume_screener

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy model
python -m spacy download en_core_web_sm

# 4. Configure environment
copy .env.example .env
# Edit .env and set DATABASE_URL

# 5. Run application
streamlit run app.py
```

**Access**: http://localhost:8501

---

### **Option 2: Cloud Deployment (Streamlit Community Cloud)**

**Steps**:
1. Push code to GitHub
2. Go to https://share.streamlit.io/
3. Connect repository
4. Add environment variables in Streamlit dashboard:
   - `DATABASE_URL`
   - `JWT_SECRET`
   - `GROQ_API_KEY` (or other AI provider)
5. Deploy

**Limitations**:
- Free tier: 1000 compute hours/month
- Database must be cloud-based (Neon DB, Supabase)
- Cannot use SQLite (ephemeral filesystem)

---

### **Option 3: Docker Deployment**

**Create `Dockerfile`**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Build & Run**:
```bash
docker build -t resume-screener .
docker run -p 8501:8501 --env-file .env resume-screener
```

---

## 🐛 Troubleshooting

### **Database Issues**

| Problem | Solution |
|---------|----------|
| "Database locked" | Close other instances of the app |
| "Table does not exist" | Delete `resume_screener.db` and restart app |
| "Connection refused" (PostgreSQL) | Check if PostgreSQL service is running |
| "Password authentication failed" | Verify DATABASE_URL in `.env` |

### **AI Model Issues**

| Problem | Solution |
|---------|----------|
| "Model not found" | Run: `python -m spacy download en_core_web_sm` |
| "Out of memory" | Reduce batch size or use smaller model |
| Slow matching | SentenceTransformer loads on first use (cached after) |

### **API Key Issues**

| Problem | Solution |
|---------|----------|
| "Missing API key" | Add key to `.env` file |
| "Invalid API key" | Regenerate key from provider dashboard |
| "Rate limit exceeded" | Wait or switch to different provider |

### **Streamlit Issues**

| Problem | Solution |
|---------|----------|
| "Port already in use" | Kill process: `netstat -ano | findstr :8501` then `taskkill /PID <pid> /F` |
| "Module not found" | Run: `pip install -r requirements.txt` |
| "Fast reruns not working" | Check `.streamlit/config.toml` |

---

## 🔮 Future Enhancements

### **Short-Term (1-2 weeks)**
1. **Add file size validation** (max 10 MB)
2. **Add pagination** for rankings page
3. **Add search/filter** for candidates
4. **Add caching** for AI question generation
5. **Improve name extraction** with ML model

### **Medium-Term (1-2 months)**
1. **Add email notifications** for screening results
2. **Add dashboard** with analytics (charts, trends)
3. **Add resume templates** detection
4. **Add skill normalization** (Python = python = PYTHON)
5. **Add multi-language** support (Urdu, Spanish, etc.)

### **Long-Term (3-6 months)**
1. **Add candidate matching** (match candidate to multiple jobs)
2. **Add interview scheduling** (calendar integration)
3. **Add ATS integration** (Greenhouse, Lever, etc.)
4. **Add bias detection** (flag biased language in JDs)
5. **Mobile app** (React Native)

---

## 📚 Additional Resources

- **Streamlit Docs**: https://docs.streamlit.io/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **SentenceTransformers**: https://www.sbert.net/
- **spaCy Docs**: https://spacy.io/usage/spacy-101
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

---

## 🎓 FYP Evaluation Points

### **What This Project Demonstrates**
1. ✅ Full-stack development (UI + Backend + Database)
2. ✅ AI/ML integration (NLP, semantic search, LLMs)
3. ✅ Database design (relational schema, constraints, indexes)
4. ✅ Security best practices (password hashing, JWT, SQL injection prevention)
5. ✅ Modular architecture (separation of concerns)
6. ✅ Error handling & validation
7. ✅ Production-ready features (connection pooling, caching)
8. ✅ Documentation (setup guides, flow diagrams, technical specs)

### **Technical Complexity**
- **Lines of Code**: ~3,500+
- **Modules**: 8 Python files
- **Database Tables**: 4 with relationships
- **AI Models**: 5 (spaCy, SentenceTransformer, 3 LLMs)
- **External APIs**: 3 (Groq, Gemini, OpenAI)

### **Scalability**
- **Current**: Handles 100+ resumes efficiently
- **With PostgreSQL**: Can scale to 10,000+ resumes
- **With indexing**: Sub-second query responses
- **With caching**: Reduced API costs

---

**For user journey and data flow, see `PROJECT_FLOW.md`**

**For client handover guide, see `CLIENT_HANDOVER.md`**

**For PostgreSQL setup, see `POSTGRESQL_SETUP.md`**
