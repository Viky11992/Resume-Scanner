"""
Resume Parser Module

Extracts and parses text from resume files (PDF, DOCX) and job descriptions.
Uses pdfminer.six for PDF parsing, python-docx for DOCX parsing, and spaCy
for NLP-based information extraction.
"""

import re
import streamlit as st
from pdfminer.high_level import extract_text as pdf_extract
from docx import Document


@st.cache_resource(show_spinner=False)
def get_nlp_model():
    """
    Load spaCy model with caching to avoid reloading on every rerun.

    Returns:
        spacy.Language: Loaded spaCy NLP model.
    """
    import spacy

    return spacy.load("en_core_web_sm")


def extract_text_from_pdf(file_path):
    """
    Extract text content from a PDF file using pdfminer.six.

    Args:
        file_path (str): Absolute or relative path to the PDF file.

    Returns:
        str: Extracted text content from the PDF.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        Exception: If there is an error reading the PDF file.
    """
    try:
        text = pdf_extract(file_path)
        if not text.strip():
            raise ValueError(f"No text could be extracted from PDF: {file_path}")
        return text
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error extracting text from PDF '{file_path}': {str(e)}")


def extract_text_from_docx(file_path):
    """
    Extract text content from a DOCX file using python-docx.

    Args:
        file_path (str): Absolute or relative path to the DOCX file.

    Returns:
        str: Extracted text content from the DOCX file.

    Raises:
        FileNotFoundError: If the DOCX file does not exist.
        Exception: If there is an error reading the DOCX file.
    """
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        if not text.strip():
            raise ValueError(f"No text could be extracted from DOCX: {file_path}")
        return text
    except FileNotFoundError:
        raise FileNotFoundError(f"DOCX file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error extracting text from DOCX '{file_path}': {str(e)}")


def extract_name_from_resume(text):
    """
    Extract candidate name from resume text using multiple strategies.
    Uses a strict, prioritized approach for accurate name detection.

    Args:
        text (str): Raw text content of the resume.

    Returns:
        str: Extracted name or empty string if not found.
    """
    nlp = get_nlp_model()
    doc = nlp(text)
    lines = text.split('\n')
    
    # Strategy 1: Look for name in contact info section (first 10-15 lines)
    # Common patterns: "Name:", "Full Name:", or just the name at the top
    name_patterns = [
        r'(?:name|full\s*name|candidate\s*name)\s*[:\-]\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+?)(?:\n|$)',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up - remove anything after newline
            name = name.split('\n')[0].strip()
            if name and 2 <= len(name.split()) <= 4:  # Valid name length
                return name
    
    # Strategy 2: Check the first few lines (header section of resume)
    # Names are typically in the first 1-3 lines and are often capitalized
    header_lines = [line.strip() for line in lines[:10] if line.strip()]
    
    for line in header_lines[:5]:  # Check first 5 non-empty lines
        # Skip lines that are clearly not names (too long, contain special chars, etc.)
        if len(line) > 50:
            continue
        if any(char in line for char in ['@', 'http', 'www', '.com', '.org']):
            continue
        # Skip lines with numbers (phone numbers, addresses, etc.)
        if re.search(r'\d', line):
            continue
        # Skip common section headers
        if re.match(r'^(contact|experience|education|skills|summary|objective|profile|references)', line, re.IGNORECASE):
            continue
        # Skip lines with decorative characters
        if re.search(r'[=\*\#\-\_]{3,}', line):
            continue
        
        # Check if line looks like a name (mostly capitalized words)
        words = line.split()
        if len(words) >= 2 and len(words) <= 4:  # Typical name length
            # Check if most words start with capital letter
            capitalized_count = sum(1 for word in words if word and word[0].isupper())
            if capitalized_count >= len(words) * 0.7:  # At least 70% capitalized
                # Verify it's not contact info keywords
                if not re.search(r'\b(email|phone|tel|mob|cell|address|linkedin|github)\b', line, re.IGNORECASE):
                    potential_name = line.strip()
                    # Additional validation with spaCy
                    temp_doc = nlp(potential_name)
                    for ent in temp_doc.ents:
                        if ent.label_ == "PERSON" and len(ent.text.strip()) >= 3:
                            return ent.text.strip()
                    # If no PERSON entity but passes other checks, still use it
                    if len(potential_name) >= 3:
                        return potential_name
    
    # Strategy 3: Use spaCy NER on the first 200 characters (header region)
    first_200_chars = text[:200]
    first_doc = nlp(first_200_chars)
    
    for ent in first_doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            # Validate: name should be reasonable length and not contain numbers/symbols
            if (2 <= len(name.split()) <= 4 and 
                len(name) >= 3 and 
                re.match(r'^[A-Za-z\s\.\-]+$', name)):
                return name
    
    # Strategy 4: Full text NER with strict validation (fallback)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            # Strict validation
            if (2 <= len(name.split()) <= 4 and  # 2-4 words
                len(name) >= 3 and  # At least 3 characters
                len(name) <= 50 and  # Not too long
                re.match(r'^[A-Za-z\s\.\-\']+$', name) and  # Only letters, spaces, hyphens, periods
                not re.search(r'\b(Mr|Mrs|Ms|Dr|Prof)\b', name, re.IGNORECASE)):  # Not a title
                return name
    
    return ""


def parse_resume(text):
    """
    Parse a resume text to extract key information using spaCy NLP.

    Extracts: name, email, phone, skills, education, experience,
    and calculates total years of experience.

    Args:
        text (str): Raw text content of the resume.

    Returns:
        dict: Parsed resume data with the following keys:
            - name (str): Candidate's full name.
            - email (str): Candidate's email address.
            - phone (str): Candidate's phone number.
            - skills (list): List of detected skills/technologies.
            - education (list): List of education entries.
            - experience (list): List of experience entries.
            - years_of_experience (int): Total years of experience.
    """
    nlp = get_nlp_model()
    doc = nlp(text)

    # Extract name using improved logic
    name = extract_name_from_resume(text)

    # Extract email using regex
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    email_match = re.search(email_pattern, text)
    email = email_match.group(0) if email_match else ""

    # Extract phone number using regex
    phone_pattern = r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}"
    phone_match = re.search(phone_pattern, text)
    phone = phone_match.group(0).strip() if phone_match else ""

    # Common skills to look for
    common_skills = [
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
        "rust", "swift", "kotlin", "php", "sql", "html", "css", "react", "angular",
        "vue", "node.js", "django", "flask", "fastapi", "spring", "rails",
        "machine learning", "deep learning", "nlp", "computer vision", "data science",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib",
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git",
        "linux", "windows", "macos", "agile", "scrum", "devops", "ci/cd",
        "rest api", "graphql", "microservices", "mongodb", "postgresql", "mysql",
        "redis", "elasticsearch", "tableau", "power bi", "excel", "statistics",
        "project management", "communication", "leadership", "problem solving",
        "teamwork", "critical thinking", "time management", "adaptability",
    ]

    text_lower = text.lower()
    skills = [skill for skill in common_skills if re.search(r'\b' + re.escape(skill) + r'\b', text_lower)]

    # Extract education (sentences containing education-related keywords)
    education_keywords = [
        "bachelor", "master", "phd", "ph.d", "degree", "university", "college",
        "institute", "school", "graduated", "graduation", "bsc", "ba", "msc", "ma",
        "mba", "btech", "mtech", "be", "me", "bs", "diploma", "certificate",
        "education", "academic",
    ]
    education = []
    for sent in doc.sents:
        sent_lower = sent.text.lower()
        if any(kw in sent_lower for kw in education_keywords):
            education.append(sent.text.strip())

    # Extract experience (sentences containing experience-related keywords)
    experience_keywords = [
        "experience", "experienced", "worked", "working", "internship", "intern",
        "position", "role", "responsibilities", "developed", "managed", "led",
        "created", "implemented", "designed", "built", "maintained", "collaborated",
        "engineer", "developer", "analyst", "manager", "consultant", "specialist",
        "associate", "senior", "junior", "lead", "head", "director",
    ]
    experience = []
    for sent in doc.sents:
        sent_lower = sent.text.lower()
        if any(kw in sent_lower for kw in experience_keywords):
            experience.append(sent.text.strip())

    # Calculate years of experience
    years_of_experience = 0
    year_pattern = r"(\d+)\s*(?:\+?\s*)?(?:years?|yrs?\.?)\s*(?:of\s*)?(?:experience|exp)"
    year_matches = re.findall(year_pattern, text_lower)
    if year_matches:
        years_of_experience = int(max(year_matches, key=int))
    else:
        # Try to find date ranges that might indicate experience
        date_range_pattern = r"(?:\b|((?:19|20)\d{2})\s*[-–—to]+\s*((?:19|20)\d{2})\b)"
        date_ranges = re.findall(r"((?:19|20)\d{2})\s*[-–—to]+\s*((?:19|20)\d{2})", text)
        if date_ranges:
            max_year = 0
            for start, end in date_ranges:
                duration = int(end) - int(start)
                if 0 < duration < 50:
                    max_year = max(max_year, duration)
            years_of_experience = max_year

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "education": education,
        "experience": experience,
        "years_of_experience": years_of_experience,
    }


def parse_job_description(text):
    """
    Parse a job description text to extract key requirements.

    Extracts: required skills, experience required, job title,
    and responsibilities.

    Args:
        text (str): Raw text content of the job description.

    Returns:
        dict: Parsed job description data with the following keys:
            - required_skills (list): List of required skills/technologies.
            - experience_required (int): Minimum years of experience required.
            - job_title (str): Job title/position.
            - responsibilities (list): List of job responsibilities.
    """
    nlp = get_nlp_model()
    doc = nlp(text)
    text_lower = text.lower()

    # Common skills to look for in job descriptions
    common_skills = [
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
        "rust", "swift", "kotlin", "php", "sql", "html", "css", "react", "angular",
        "vue", "node.js", "django", "flask", "fastapi", "spring", "rails",
        "machine learning", "deep learning", "nlp", "computer vision", "data science",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib",
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git",
        "linux", "windows", "macos", "agile", "scrum", "devops", "ci/cd",
        "rest api", "graphql", "microservices", "mongodb", "postgresql", "mysql",
        "redis", "elasticsearch", "tableau", "power bi", "excel", "statistics",
        "project management", "communication", "leadership", "problem solving",
        "teamwork", "critical thinking", "time management", "adaptability",
    ]

    required_skills = [skill for skill in common_skills if re.search(r'\b' + re.escape(skill) + r'\b', text_lower)]

    # Extract experience required
    experience_required = 0
    exp_patterns = [
        r"(\d+)\s*\+?\s*(?:years?|yrs?\.?)\s*(?:of\s*)?(?:experience|exp)",
        r"(?:minimum|at least|requires?)\s*(\d+)\s*\+?\s*(?:years?|yrs?\.?)",
    ]
    for pattern in exp_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            experience_required = int(max(matches, key=int))
            break

    # Extract job title (look for common patterns)
    job_title = ""
    title_patterns = [
        r"(?:job\s+)?title[:\s]+([^\n]+)",
        r"(?:position|role)[:\s]+([^\n]+)",
        r"(?:we\s+are\s+(?:looking\s+for|seeking)\s+(?:a|an))\s+([^\n,.]+)",
        r"(?:hiring)\s+(?:a|an)\s+([^\n,.]+)",
    ]
    for pattern in title_patterns:
        match = re.search(pattern, text_lower)
        if match:
            job_title = match.group(1).strip().title()
            break

    # If no title found, try to extract from first line
    if not job_title:
        first_line = text.split("\n")[0].strip()
        if len(first_line.split()) <= 6:
            job_title = first_line

    # Extract responsibilities
    responsibility_keywords = [
        "responsible for", "responsibilities", "will", "must", "should",
        "expected to", "duties", "tasks", "manage", "develop", "design",
        "implement", "create", "build", "maintain", "collaborate", "work with",
        "analyze", "review", "test", "deploy", "monitor", "optimize",
        "lead", "guide", "mentor", "coordinate",
    ]

    responsibilities = []
    in_responsibilities_section = False

    for sent in doc.sents:
        sent_lower = sent.text.lower().strip()

        # Check if we're entering a responsibilities section
        if any(kw in sent_lower for kw in ["responsibilities", "what you'll do", "key duties", "job duties"]):
            in_responsibilities_section = True
            continue

        # If in responsibilities section, collect sentences
        if in_responsibilities_section:
            if any(kw in sent_lower for kw in ["requirements", "qualifications", "skills", "benefits", "about"]):
                in_responsibilities_section = False
                continue
            if sent_lower and len(sent_lower.split()) > 2:
                responsibilities.append(sent.text.strip())
        elif any(sent_lower.startswith(kw) for kw in responsibility_keywords):
            responsibilities.append(sent.text.strip())

    return {
        "required_skills": required_skills,
        "experience_required": experience_required,
        "job_title": job_title,
        "responsibilities": responsibilities,
    }
