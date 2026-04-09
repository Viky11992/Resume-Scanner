"""
Database Module

PostgreSQL integration using SQLAlchemy ORM for persisting jobs, candidates, and rankings.
Replaces MongoDB with a relational database for better data integrity and query performance.
"""

import os
import json
from datetime import datetime
from typing import List, Optional

from database_postgres import (
    Job,
    Candidate,
    Ranking,
    session_scope,
    get_session,
    init_db,
    check_connection,
)


# ─── Job Operations ───────────────────────────────────────────────────────────

def save_job(job_data: dict) -> str:
    """
    Save a job description and its parsed data to the database.

    Args:
        job_data (dict): Job data containing at minimum:
            - job_id (str): Unique identifier for the job.
            - job_title (str): Title of the position.
            - description (str): Full job description text.
            - required_skills (list): List of required skills.
            - experience_required (int): Years of experience required.
            - created_at (datetime, optional): Creation timestamp.

    Returns:
        str: The job_id of the inserted/updated record.

    Raises:
        ValueError: If job_data is missing required fields.
        Exception: If there is a database error.
    """
    try:
        if not job_data or "job_id" not in job_data:
            raise ValueError("job_data must contain a 'job_id' field")

        with session_scope() as session:
            # Check if job exists
            existing_job = session.query(Job).filter_by(job_id=job_data["job_id"]).first()

            if existing_job:
                # Update existing job
                if "job_title" in job_data:
                    existing_job.job_title = job_data["job_title"]
                if "description" in job_data:
                    existing_job.description = job_data["description"]
                if "required_skills" in job_data:
                    existing_job.required_skills = json.dumps(job_data["required_skills"])
                if "experience_required" in job_data:
                    existing_job.experience_required = job_data["experience_required"]
                existing_job.updated_at = datetime.utcnow()
            else:
                # Create new job
                new_job = Job(
                    job_id=job_data["job_id"],
                    job_title=job_data.get("job_title"),
                    description=job_data.get("description"),
                    required_skills=json.dumps(job_data.get("required_skills", [])),
                    experience_required=job_data.get("experience_required", 0),
                    created_at=job_data.get("created_at", datetime.utcnow()),
                )
                session.add(new_job)

        return job_data["job_id"]

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Database error while saving job: {str(e)}")


# ─── Candidate Operations ─────────────────────────────────────────────────────

def save_candidate(candidate_data: dict) -> str:
    """
    Save a candidate's resume data to the database.

    Args:
        candidate_data (dict): Candidate data containing at minimum:
            - candidate_id (str): Unique identifier for the candidate.
            - name (str): Candidate's full name.
            - email (str): Candidate's email address.
            - phone (str): Candidate's phone number.
            - skills (list): List of candidate's skills.
            - education (list): Education history.
            - experience (list): Work experience.
            - years_of_experience (int): Total years of experience.
            - resume_text (str): Full resume text content.
            - created_at (datetime, optional): Creation timestamp.

    Returns:
        str: The candidate_id of the inserted/updated record.

    Raises:
        ValueError: If candidate_data is missing required fields.
        Exception: If there is a database error.
    """
    try:
        if not candidate_data or "candidate_id" not in candidate_data:
            raise ValueError("candidate_data must contain a 'candidate_id' field")

        with session_scope() as session:
            # Check if candidate exists
            existing_candidate = session.query(Candidate).filter_by(
                candidate_id=candidate_data["candidate_id"]
            ).first()

            if existing_candidate:
                # Update existing candidate
                if "name" in candidate_data:
                    existing_candidate.name = candidate_data["name"]
                if "email" in candidate_data:
                    existing_candidate.email = candidate_data["email"]
                if "phone" in candidate_data:
                    existing_candidate.phone = candidate_data["phone"]
                if "skills" in candidate_data:
                    existing_candidate.skills = json.dumps(candidate_data["skills"])
                if "education" in candidate_data:
                    existing_candidate.education = json.dumps(candidate_data["education"])
                if "experience" in candidate_data:
                    existing_candidate.experience = json.dumps(candidate_data["experience"])
                if "years_of_experience" in candidate_data:
                    existing_candidate.years_of_experience = candidate_data["years_of_experience"]
                if "resume_text" in candidate_data:
                    existing_candidate.resume_text = candidate_data["resume_text"]
                existing_candidate.updated_at = datetime.utcnow()
            else:
                # Create new candidate
                new_candidate = Candidate(
                    candidate_id=candidate_data["candidate_id"],
                    name=candidate_data.get("name", "Unknown"),
                    email=candidate_data.get("email"),
                    phone=candidate_data.get("phone"),
                    skills=json.dumps(candidate_data.get("skills", [])),
                    education=json.dumps(candidate_data.get("education", [])),
                    experience=json.dumps(candidate_data.get("experience", [])),
                    years_of_experience=candidate_data.get("years_of_experience", 0),
                    resume_text=candidate_data.get("resume_text"),
                    created_at=candidate_data.get("created_at", datetime.utcnow()),
                )
                session.add(new_candidate)

        return candidate_data["candidate_id"]

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Database error while saving candidate: {str(e)}")


# ─── Ranking Operations ───────────────────────────────────────────────────────

def save_ranking(ranking_data: dict) -> str:
    """
    Save a ranking result to the database.

    Args:
        ranking_data (dict): Ranking data containing:
            - ranking_id (str): Unique identifier for this ranking run.
            - job_id (str): Associated job ID.
            - candidate_id (str): Associated candidate ID.
            - score (float): Matching score.
            - skills_matched (list): Skills that matched.
            - skills_missing (list): Skills that were missing.
            - rank (int): Rank position.
            - created_at (datetime, optional): Creation timestamp.

    Returns:
        str: The ranking_id of the inserted/updated record.

    Raises:
        ValueError: If ranking_data is missing required fields.
        Exception: If there is a database error.
    """
    try:
        required_fields = ["ranking_id", "job_id", "candidate_id", "score"]
        if not ranking_data:
            raise ValueError("ranking_data cannot be None")
        for field in required_fields:
            if field not in ranking_data:
                raise ValueError(f"ranking_data must contain a '{field}' field")

        # Validate score range
        if not (0 <= ranking_data["score"] <= 1):
            raise ValueError(f"Score must be between 0 and 1, got {ranking_data['score']}")

        with session_scope() as session:
            # Check if ranking exists
            existing_ranking = session.query(Ranking).filter_by(
                ranking_id=ranking_data["ranking_id"]
            ).first()

            if existing_ranking:
                # Update existing ranking
                if "job_id" in ranking_data:
                    existing_ranking.job_id = ranking_data["job_id"]
                if "candidate_id" in ranking_data:
                    existing_ranking.candidate_id = ranking_data["candidate_id"]
                if "score" in ranking_data:
                    existing_ranking.score = ranking_data["score"]
                if "skills_matched" in ranking_data:
                    existing_ranking.skills_matched = json.dumps(ranking_data["skills_matched"])
                if "skills_missing" in ranking_data:
                    existing_ranking.skills_missing = json.dumps(ranking_data["skills_missing"])
                if "rank" in ranking_data:
                    existing_ranking.rank = ranking_data["rank"]
            else:
                # Create new ranking
                new_ranking = Ranking(
                    ranking_id=ranking_data["ranking_id"],
                    job_id=ranking_data["job_id"],
                    candidate_id=ranking_data["candidate_id"],
                    score=ranking_data["score"],
                    skills_matched=json.dumps(ranking_data.get("skills_matched", [])),
                    skills_missing=json.dumps(ranking_data.get("skills_missing", [])),
                    rank=ranking_data.get("rank"),
                    created_at=ranking_data.get("created_at", datetime.utcnow()),
                )
                session.add(new_ranking)

        return ranking_data["ranking_id"]

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Database error while saving ranking: {str(e)}")


def get_all_rankings(job_id: str) -> list:
    """
    Retrieve all rankings for a specific job.

    Args:
        job_id (str): The job ID to fetch rankings for.

    Returns:
        list: List of ranking dictionaries sorted by score descending.

    Raises:
        ValueError: If job_id is empty or None.
        Exception: If there is a database error.
    """
    try:
        if not job_id:
            raise ValueError("job_id is required")

        with session_scope() as session:
            rankings = (
                session.query(Ranking)
                .filter(Ranking.job_id == job_id)
                .order_by(Ranking.score.desc())
                .all()
            )

            # Convert to dictionaries
            return [ranking.to_dict() for ranking in rankings]

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Database error while fetching rankings: {str(e)}")


def get_rankings_with_details(job_id: str) -> list:
    """
    Retrieve all rankings for a specific job with candidate and job details.
    Uses JOINs to fetch related data in a single query.

    Args:
        job_id (str): The job ID to fetch rankings for.

    Returns:
        list: List of ranking dictionaries with candidate and job details.
    """
    try:
        if not job_id:
            raise ValueError("job_id is required")

        with session_scope() as session:
            rankings = (
                session.query(Ranking)
                .join(Candidate, Ranking.candidate_id == Candidate.candidate_id)
                .join(Job, Ranking.job_id == Job.job_id)
                .filter(Ranking.job_id == job_id)
                .order_by(Ranking.score.desc())
                .all()
            )

            result = []
            for ranking in rankings:
                data = ranking.to_dict()
                data["candidate_name"] = ranking.candidate.name
                data["candidate_email"] = ranking.candidate.email
                data["candidate_skills"] = json.loads(ranking.candidate.skills) if ranking.candidate.skills else []
                data["job_title"] = ranking.job.job_title
                result.append(data)

            return result

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Database error while fetching rankings with details: {str(e)}")


# ─── Database Initialization ──────────────────────────────────────────────────

def initialize_database():
    """
    Initialize the database by creating all tables.
    Safe to call multiple times (won't drop existing data).
    """
    try:
        init_db()
        if check_connection():
            print("✓ Database initialized successfully")
            return True
        else:
            print("✗ Database connection failed")
            return False
    except Exception as e:
        print(f"✗ Database initialization failed: {str(e)}")
        return False


def get_database_status() -> dict:
    """
    Get database connection status and basic statistics.

    Returns:
        dict: Database status information.
    """
    try:
        is_connected = check_connection()
        stats = {
            "connected": is_connected,
            "database_type": "PostgreSQL",
            "database_url": os.getenv("DATABASE_URL", "Not configured"),
        }

        if is_connected:
            with session_scope() as session:
                stats["user_count"] = session.query(Job).count()
                stats["candidate_count"] = session.query(Candidate).count()
                stats["ranking_count"] = session.query(Ranking).count()

        return stats
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
        }
