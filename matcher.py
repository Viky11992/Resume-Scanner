"""
Matcher Module

Handles semantic similarity matching between resumes and job descriptions
using sentence embeddings from the SentenceTransformer model.
"""

import warnings
import numpy as np
import streamlit as st
from sentence_transformers import util

# Suppress transformers library warnings (unnecessary image models)
warnings.filterwarnings("ignore", category=Warning, module="transformers")
warnings.filterwarnings("ignore", message=".*torchvision.*")


@st.cache_resource(show_spinner=False)
def get_model():
    """
    Load SentenceTransformer model with caching to avoid reloading on every rerun.

    Returns:
        SentenceTransformer: Loaded model instance.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def compute_similarity(resume_text, jd_text):
    """
    Compute cosine similarity between a resume and a job description
    using sentence embeddings.

    Args:
        resume_text (str): Raw text content of the resume.
        jd_text (str): Raw text content of the job description.

    Returns:
        float: Cosine similarity score between 0 and 1.

    Raises:
        ValueError: If either text is empty or None.
        Exception: If there is an error during similarity computation.
    """
    try:
        if not resume_text or not resume_text.strip():
            raise ValueError("Resume text is empty or None")
        if not jd_text or not jd_text.strip():
            raise ValueError("Job description text is empty or None")

        # Encode texts to get embeddings
        model = get_model()
        resume_embedding = model.encode(resume_text, convert_to_tensor=True)
        jd_embedding = model.encode(jd_text, convert_to_tensor=True)

        # Compute cosine similarity
        similarity = util.cos_sim(resume_embedding, jd_embedding)
        score = similarity.item()

        # Clamp to [0, 1] range (cosine similarity can be negative)
        return max(0.0, min(1.0, score))

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error computing similarity: {str(e)}")


def batch_match(resumes_list, jd_text):
    """
    Match a batch of resumes against a single job description.

    Args:
        resumes_list (list): List of dicts, each containing:
            - name (str): Candidate name.
            - text (str): Resume text content.
            - skills (list): List of candidate's skills.
        jd_text (str): Job description text content.

    Returns:
        list: List of dicts with match results:
            - name (str): Candidate name.
            - score (float): Similarity score (0 to 1).
            - skills_matched (list): Skills that match the job description.
            - skills_missing (list): Skills from JD not found in resume.

    Raises:
        ValueError: If resumes_list is empty or jd_text is invalid.
        Exception: If there is an error during batch matching.
    """
    try:
        if not resumes_list:
            raise ValueError("Resumes list is empty")
        if not jd_text or not jd_text.strip():
            raise ValueError("Job description text is empty or None")

        # Extract required skills from JD text using basic keyword matching
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
        ]

        jd_lower = jd_text.lower()
        required_skills = [
            skill for skill in common_skills
            if skill in jd_lower
        ]

        results = []
        for resume in resumes_list:
            name = resume.get("name", "Unknown")
            text = resume.get("text", "")
            candidate_skills = [s.lower() for s in resume.get("skills", [])]

            # Compute similarity score
            score = compute_similarity(text, jd_text)

            # Perform skills gap analysis
            skills_matched = [
                skill for skill in required_skills
                if skill in candidate_skills
            ]
            skills_missing = [
                skill for skill in required_skills
                if skill not in candidate_skills
            ]

            results.append({
                "name": name,
                "score": round(score, 4),
                "skills_matched": skills_matched,
                "skills_missing": skills_missing,
            })

        return results

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error during batch matching: {str(e)}")


def skills_gap_analysis(resume_skills, required_skills):
    """
    Analyze the skills gap between a candidate's skills and required skills.

    Args:
        resume_skills (list): List of skills the candidate possesses.
        required_skills (list): List of skills required by the job.

    Returns:
        dict: Skills gap analysis with:
            - matched (list): Skills present in both lists.
            - missing (list): Required skills not found in resume.
            - match_percentage (float): Percentage of required skills matched.

    Raises:
        ValueError: If either skills list is None.
        Exception: If there is an error during analysis.
    """
    try:
        if resume_skills is None:
            raise ValueError("Resume skills list is None")
        if required_skills is None:
            raise ValueError("Required skills list is None")

        # Normalize to lowercase for comparison
        resume_lower = [s.lower().strip() for s in resume_skills]
        required_lower = [s.lower().strip() for s in required_skills]

        matched = [skill for skill in required_lower if skill in resume_lower]
        missing = [skill for skill in required_lower if skill not in resume_lower]

        match_percentage = (
            round((len(matched) / len(required_lower)) * 100, 2)
            if required_lower
            else 0.0
        )

        return {
            "matched": matched,
            "missing": missing,
            "match_percentage": match_percentage,
        }

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error during skills gap analysis: {str(e)}")
