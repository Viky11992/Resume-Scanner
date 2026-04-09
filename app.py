"""
Resume Screener — Streamlit Web Interface

A modular AI-based resume screening application that allows users to:
1. Upload resumes and screen them against a job description
2. View ranked candidates with color-coded scores
3. Generate tailored interview questions
4. Export results to Excel and PDF
5. Secure authentication and role-based access control
"""

import os
import uuid
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import streamlit as st

# Initialize database on startup
from database_postgres import init_db, check_connection
from database import initialize_database

# Initialize database tables
if "db_initialized" not in st.session_state:
    try:
        initialize_database()
        st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"Database initialization failed: {str(e)}")

from auth import (
    initialize_auth_session,
    initialize_default_users,
    require_auth,
    show_login_page,
    show_user_profile,
    show_admin_panel,
    login_user,
    logout_user,
)
from parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    parse_resume,
    parse_job_description,
)
from matcher import batch_match
from ranker import rank_candidates, shortlist_candidates, export_to_excel, export_to_pdf
from question_generator import generate_interview_questions
from database import save_job, save_candidate, save_ranking


# ─── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Authentication & Session State Initialization ─────────────────────────────
# Run only once per session (not on every rerun)
if "auth_initialized" not in st.session_state:
    initialize_auth_session()
    initialize_default_users()
    st.session_state.auth_initialized = True

# Check if user is authenticated
if not st.session_state.get("authenticated", False):
    show_login_page()
    st.stop()

# ─── Session State Initialization (Post-Auth) ─────────────────────────────────
if "screened" not in st.session_state:
    st.session_state.screened = False
if "ranked_list" not in st.session_state:
    st.session_state.ranked_list = []
if "parsed_resumes" not in st.session_state:
    st.session_state.parsed_resumes = []
if "parsed_jd" not in st.session_state:
    st.session_state.parsed_jd = None
if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""


# ─── Helper Functions ─────────────────────────────────────────────────────────
def process_uploaded_resumes(uploaded_files):
    """
    Extract and parse text from uploaded resume files.

    Args:
        uploaded_files: List of Streamlit UploadedFile objects.

    Returns:
        tuple: (resumes_list for matching, parsed_resumes for display)
    """
    resumes_list = []
    parsed_resumes = []

    for uploaded_file in uploaded_files:
        try:
            # Save to temp file
            suffix = Path(uploaded_file.name).suffix.lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            # Extract text based on file type
            if suffix == ".pdf":
                text = extract_text_from_pdf(tmp_path)
            elif suffix in (".docx", ".doc"):
                text = extract_text_from_docx(tmp_path)
            else:
                st.error(f"Unsupported file type: {uploaded_file.name}")
                continue

            # Parse resume
            parsed = parse_resume(text)
            parsed["raw_text"] = text
            parsed["file_name"] = uploaded_file.name

            resumes_list.append({
                "name": parsed.get("name", uploaded_file.name),
                "text": text,
                "skills": parsed.get("skills", []),
            })
            parsed_resumes.append(parsed)

            # Clean up temp file
            os.unlink(tmp_path)

        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            continue

    return resumes_list, parsed_resumes


# ─── Sidebar Navigation ───────────────────────────────────────────────────────
st.sidebar.title("📄 AI Resume Screener")

# Show user profile in sidebar
show_user_profile()

# Determine available pages based on role
current_role = st.session_state.current_user.get("role", "recruiter")

if current_role == "admin":
    nav_options = ["Upload & Screen", "Rankings", "Interview Prep", "Export", "Admin Panel"]
else:
    nav_options = ["Upload & Screen", "Rankings", "Interview Prep", "Export"]

page = st.sidebar.radio(
    "Navigation",
    nav_options,
)

# Handle Admin Panel selection
if page == "Admin Panel":
    if current_role != "admin":
        st.error("Access denied. Admin privileges required.")
        st.stop()
    else:
        show_admin_panel()
        st.stop()


# ─── Page: Upload & Screen ────────────────────────────────────────────────────
if page == "Upload & Screen":
    st.title("📤 Upload & Screen Candidates")
    st.markdown("Upload a job description and multiple resumes to screen candidates.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Job Description")
        jd_input_method = st.radio("Input method", ["Text Input", "Upload File"], key="jd_method")

        jd_text_raw = ""
        if jd_input_method == "Text Input":
            jd_text_raw = st.text_area(
                "Paste the job description below:",
                height=250,
                placeholder="Paste job description here...",
                key="jd_text_area",
            )
        else:
            jd_file = st.file_uploader("Upload job description (PDF/DOCX):", type=["pdf", "docx"])
            if jd_file:
                suffix = Path(jd_file.name).suffix.lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(jd_file.getvalue())
                    tmp_path = tmp.name
                try:
                    if suffix == ".pdf":
                        jd_text_raw = extract_text_from_pdf(tmp_path)
                    else:
                        jd_text_raw = extract_text_from_docx(tmp_path)
                    st.success(f"Job description loaded: {jd_file.name}")
                except Exception as e:
                    st.error(f"Error reading job description: {str(e)}")
                    jd_text_raw = ""
                finally:
                    os.unlink(tmp_path)

        # Parse JD if text is available
        parsed_jd = None
        if jd_text_raw and jd_text_raw.strip():
            try:
                parsed_jd = parse_job_description(jd_text_raw)
                st.session_state.parsed_jd = parsed_jd
                st.session_state.jd_text = jd_text_raw

                with st.expander("📋 Parsed Job Description"):
                    st.write(f"**Job Title:** {parsed_jd.get('job_title', 'N/A')}")
                    st.write(f"**Experience Required:** {parsed_jd.get('experience_required', 0)} years")
                    st.write(f"**Required Skills:** {', '.join(parsed_jd.get('required_skills', []))}")
                    st.write(f"**Responsibilities:** {len(parsed_jd.get('responsibilities', []))} identified")
            except Exception as e:
                st.warning(f"Could not parse job description fully: {str(e)}")

    with col2:
        st.subheader("Resume Upload")
        uploaded_files = st.file_uploader(
            "Upload resumes (PDF or DOCX):",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            key="resume_uploader",
        )

        if uploaded_files:
            st.info(f"{len(uploaded_files)} file(s) selected")

    # Screen button
    if st.button("🔍 Screen Candidates", type="primary", use_container_width=True):
        if not jd_text_raw or not jd_text_raw.strip():
            st.error("Please provide a job description first.")
        elif not uploaded_files:
            st.error("Please upload at least one resume.")
        else:
            with st.spinner("Processing resumes and computing matches..."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Step 1: Process uploaded resumes
                status_text.text("Extracting text from resumes...")
                progress_bar.progress(20)

                resumes_list, parsed_resumes = process_uploaded_resumes(uploaded_files)
                st.session_state.parsed_resumes = parsed_resumes

                if not resumes_list:
                    st.error("No resumes could be processed.")
                    progress_bar.empty()
                    status_text.empty()
                    st.stop()

                # Step 2: Batch matching
                status_text.text("Computing similarity scores...")
                progress_bar.progress(50)

                try:
                    batch_results = batch_match(resumes_list, jd_text_raw)
                except Exception as e:
                    st.error(f"Matching failed: {str(e)}")
                    progress_bar.empty()
                    status_text.empty()
                    st.stop()

                # Step 3: Ranking
                status_text.text("Ranking candidates...")
                progress_bar.progress(75)

                ranked_list = rank_candidates(batch_results)
                st.session_state.ranked_list = ranked_list
                st.session_state.screened = True

                # Step 4: Save to Database
                try:
                    job_id = f"job_{uuid.uuid4().hex[:8]}"
                    job_data = {
                        "job_id": job_id,
                        "job_title": parsed_jd.get("job_title", "Unknown Role"),
                        "description": jd_text_raw,
                        "required_skills": parsed_jd.get("required_skills", []),
                        "experience_required": parsed_jd.get("experience_required", 0),
                    }
                    save_job(job_data)
                    st.session_state.current_job_id = job_id

                    # Save candidates and rankings
                    for i, candidate_result in enumerate(ranked_list):
                        candidate_name = candidate_result["name"]
                        
                        # Find full parsed data for this candidate
                        parsed_data = next(
                            (p for p in parsed_resumes if p.get("name") == candidate_name), 
                            {}
                        )
                        
                        candidate_id = f"cand_{uuid.uuid4().hex[:8]}"
                        
                        # Save Candidate
                        candidate_data = {
                            "candidate_id": candidate_id,
                            "name": candidate_name,
                            "email": parsed_data.get("email", ""),
                            "phone": parsed_data.get("phone", ""),
                            "skills": parsed_data.get("skills", []),
                            "education": parsed_data.get("education", []),
                            "experience": parsed_data.get("experience", []),
                            "years_of_experience": parsed_data.get("years_of_experience", 0),
                            "resume_text": parsed_data.get("raw_text", ""),
                        }
                        save_candidate(candidate_data)

                        # Save Ranking
                        ranking_data = {
                            "ranking_id": f"rank_{uuid.uuid4().hex[:8]}",
                            "job_id": job_id,
                            "candidate_id": candidate_id,
                            "score": candidate_result["score"],
                            "skills_matched": candidate_result.get("skills_matched", []),
                            "skills_missing": candidate_result.get("skills_missing", []),
                            "rank": i + 1,
                        }
                        save_ranking(ranking_data)
                    
                except Exception as db_err:
                    st.warning(f"Screening successful, but failed to save to database: {str(db_err)}")

                progress_bar.progress(100)
                status_text.text("Done!")

            st.success(f"Successfully screened {len(ranked_list)} candidates!")

            # Quick preview
            st.subheader("Quick Preview")
            for i, candidate in enumerate(ranked_list[:5]):
                score_pct = round(candidate["score"] * 100, 1)
                st.metric(
                    f"#{i+1} — {candidate['name']}",
                    f"{score_pct}%",
                    f"{len(candidate['skills_matched'])} skills matched",
                )

            progress_bar.empty()
            status_text.empty()


# ─── Page: Rankings ───────────────────────────────────────────────────────────
elif page == "Rankings":
    st.title("🏆 Candidate Rankings")

    if not st.session_state.screened or not st.session_state.ranked_list:
        st.warning("No screening results found. Please go to 'Upload & Screen' first.")
    else:
        ranked_list = st.session_state.ranked_list

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        total = len(ranked_list)
        avg_score = round(sum(c["score"] for c in ranked_list) / total * 100, 1) if total > 0 else 0
        top_score = round(ranked_list[0]["score"] * 100, 1) if ranked_list else 0

        col1.metric("Total Candidates", total)
        col2.metric("Average Score", f"{avg_score}%")
        col3.metric("Top Score", f"{top_score}%")

        st.divider()

        # Display table with color coding
        st.subheader("Detailed Rankings")

        for i, candidate in enumerate(ranked_list):
            score_pct = round(candidate["score"] * 100, 1)

            # Color coding
            if score_pct > 70:
                color = "🟢"
            elif score_pct >= 50:
                color = "🟡"
            else:
                color = "🔴"

            with st.container(border=True):
                col_name, col_score, col_skills = st.columns([2, 1, 3])

                col_name.markdown(f"### {color} #{i+1} — {candidate['name']}")
                col_score.metric("", f"{score_pct}%")

                skills_col = col_skills.columns(2)
                skills_col[0].markdown(
                    f"**Matched:** {', '.join(candidate.get('skills_matched', [])) or 'None'}"
                )
                skills_col[1].markdown(
                    f"**Missing:** {', '.join(candidate.get('skills_missing', [])) or 'None'}"
                )


# ─── Page: Interview Prep ──────────────────────────────────────────────────────
elif page == "Interview Prep":
    st.title("🎤 Interview Question Generator")

    if not st.session_state.screened or not st.session_state.parsed_resumes:
        st.warning("No screened candidates found. Please screen resumes first.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            # Candidate selector
            candidate_names = [p.get("name", "Unknown") for p in st.session_state.parsed_resumes]
            selected_name = st.selectbox("Select a candidate:", candidate_names)

            # Difficulty selector
            difficulty = st.selectbox(
                "Difficulty Level:",
                ["Easy", "Medium", "Hard"],
                index=1,
            )

            # Find selected candidate data
            selected_candidate = next(
                (p for p in st.session_state.parsed_resumes if p.get("name") == selected_name),
                None,
            )

            generate_btn = st.button(
                "🤖 Generate Questions",
                type="primary",
                use_container_width=True,
            )

        with col2:
            if selected_candidate:
                st.subheader("Candidate Profile")
                st.write(f"**Name:** {selected_candidate.get('name', 'N/A')}")
                st.write(f"**Experience:** {selected_candidate.get('years_of_experience', 0)} years")
                st.write(f"**Skills:** {', '.join(selected_candidate.get('skills', []))}")
                st.write(
                    f"**Education:** {len(selected_candidate.get('education', []))} entries found"
                )

        # Generate and display questions
        if generate_btn and selected_candidate:
            job_title = "N/A"
            if st.session_state.parsed_jd:
                job_title = st.session_state.parsed_jd.get("job_title", job_title)

            candidate_skills = selected_candidate.get("skills", [])
            experience_years = selected_candidate.get("years_of_experience", 0)

            if not candidate_skills:
                st.warning("No skills detected for this candidate. Questions may be generic.")
                candidate_skills = ["general software engineering"]

            with st.spinner(f"Generating {difficulty.lower()} difficulty questions..."):
                try:
                    questions = generate_interview_questions(
                        candidate_skills=candidate_skills,
                        job_title=job_title,
                        experience_years=experience_years,
                        difficulty=difficulty.lower(),
                    )

                    st.session_state.generated_questions = questions
                    st.success(f"Generated {len(questions)} interview questions!")

                except Exception as e:
                    st.error(f"Failed to generate questions: {str(e)}")
                    questions = None
        else:
            questions = st.session_state.get("generated_questions", None)

        # Display questions grouped by category
        if questions:
            st.divider()
            categories = {
                "Technical": [],
                "Behavioral": [],
                "Situational": [],
                "Role-Specific": [],
            }

            for q in questions:
                q_type = q.get("type", "").lower()
                if "technical" in q_type:
                    categories["Technical"].append(q)
                elif "behavioral" in q_type:
                    categories["Behavioral"].append(q)
                elif "situational" in q_type:
                    categories["Situational"].append(q)
                elif "role" in q_type:
                    categories["Role-Specific"].append(q)

            for category, cat_questions in categories.items():
                with st.expander(f"📌 {category} Questions ({len(cat_questions)})", expanded=True):
                    for i, q in enumerate(cat_questions, 1):
                        st.markdown(f"**Q{i}.** {q['question']}")
                        hints = q.get("expected_answer_hints", [])
                        if hints:
                            st.markdown(
                                f"**Expected answer hints:**\n"
                                + "\n".join(f"- {h}" for h in hints)
                            )
                        st.divider()


# ─── Page: Export ─────────────────────────────────────────────────────────────
elif page == "Export":
    st.title("📥 Export Results")

    if not st.session_state.screened or not st.session_state.ranked_list:
        st.warning("No screening results to export. Please screen candidates first.")
    else:
        ranked_list = st.session_state.ranked_list

        st.markdown(f"Ready to export **{len(ranked_list)}** candidate results.")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Excel Export")
            st.markdown("Download a formatted Excel spreadsheet with candidate rankings.")

            excel_path = Path("candidate_rankings.xlsx")
            try:
                export_to_excel(ranked_list, str(excel_path))
                with open(excel_path, "rb") as f:
                    st.download_button(
                        label="📊 Download Excel Report",
                        data=f,
                        file_name="candidate_rankings.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
            except Exception as e:
                st.error(f"Excel export failed: {str(e)}")

        with col2:
            st.subheader("PDF Export")
            st.markdown("Download a clean PDF report with candidate rankings.")

            pdf_path = Path("candidate_rankings.pdf")
            try:
                export_to_pdf(ranked_list, str(pdf_path))
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=f,
                        file_name="candidate_rankings.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            except Exception as e:
                st.error(f"PDF export failed: {str(e)}")

        # Cleanup generated files after download
        if excel_path.exists():
            os.remove(excel_path)
        if pdf_path.exists():
            os.remove(pdf_path)
