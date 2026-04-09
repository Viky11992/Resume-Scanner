"""
Data Migration Script: MongoDB → PostgreSQL

One-time use script to migrate existing data from MongoDB to PostgreSQL.
Reads all data from MongoDB collections and inserts them into PostgreSQL tables.

Usage:
    python migrate_data.py

Prerequisites:
    1. MongoDB must be running and accessible
    2. PostgreSQL must be running and accessible
    3. Both databases must be configured in .env file
    4. Required packages: pymongo, psycopg2, sqlalchemy
"""

import os
import json
from datetime import datetime

from pymongo import MongoClient
from sqlalchemy import text

from database_postgres import (
    User,
    Job,
    Candidate,
    Ranking,
    init_db,
    get_session,
    session_scope,
)


# ─── MongoDB Configuration ────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DATABASE = "resume_screener"

# ─── Migration Statistics ─────────────────────────────────────────────────────
stats = {
    "users": {"migrated": 0, "skipped": 0, "errors": 0},
    "jobs": {"migrated": 0, "skipped": 0, "errors": 0},
    "candidates": {"migrated": 0, "skipped": 0, "errors": 0},
    "rankings": {"migrated": 0, "skipped": 0, "errors": 0},
}


def get_mongo_client():
    """Create MongoDB client connection."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        print("✓ Successfully connected to MongoDB")
        return client
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {str(e)}")
        return None


def migrate_users(mongo_db, pg_session):
    """Migrate users collection from MongoDB to PostgreSQL."""
    print("\n" + "=" * 60)
    print("Migrating Users...")
    print("=" * 60)

    try:
        mongo_users = mongo_db.users.find()
        total = mongo_users.count()
        print(f"Found {total} users in MongoDB")

        for mongo_user in mongo_users:
            try:
                # Check if user already exists in PostgreSQL
                existing = pg_session.query(User).filter_by(
                    user_id=mongo_user.get("user_id")
                ).first()

                if existing:
                    print(f"  ⏭  Skipped user: {mongo_user.get('username')} (already exists)")
                    stats["users"]["skipped"] += 1
                    continue

                # Create new user in PostgreSQL
                pg_user = User(
                    id=mongo_user.get("id"),  # Keep same ID if possible
                    user_id=mongo_user.get("user_id"),
                    username=mongo_user.get("username"),
                    password_hash=mongo_user.get("password_hash"),
                    role=mongo_user.get("role", "recruiter"),
                    name=mongo_user.get("name", ""),
                    email=mongo_user.get("email", ""),
                    created_at=mongo_user.get("created_at", datetime.utcnow()),
                    last_login=mongo_user.get("last_login"),
                    is_active=mongo_user.get("is_active", True),
                )
                pg_session.add(pg_user)
                stats["users"]["migrated"] += 1
                print(f"  ✓ Migrated user: {mongo_user.get('username')}")

            except Exception as e:
                print(f"  ✗ Error migrating user {mongo_user.get('username')}: {str(e)}")
                stats["users"]["errors"] += 1

        print(f"\n✓ Users migration complete: {stats['users']}")

    except Exception as e:
        print(f"✗ Users migration failed: {str(e)}")
        stats["users"]["errors"] += 1


def migrate_jobs(mongo_db, pg_session):
    """Migrate jobs collection from MongoDB to PostgreSQL."""
    print("\n" + "=" * 60)
    print("Migrating Jobs...")
    print("=" * 60)

    try:
        mongo_jobs = mongo_db.jobs.find()
        total = mongo_jobs.count()
        print(f"Found {total} jobs in MongoDB")

        for mongo_job in mongo_jobs:
            try:
                # Check if job already exists in PostgreSQL
                existing = pg_session.query(Job).filter_by(
                    job_id=mongo_job.get("job_id")
                ).first()

                if existing:
                    print(f"  ⏭  Skipped job: {mongo_job.get('job_id')} (already exists)")
                    stats["jobs"]["skipped"] += 1
                    continue

                # Convert required_skills to JSON string
                required_skills = mongo_job.get("required_skills", [])
                if isinstance(required_skills, list):
                    skills_json = json.dumps(required_skills)
                else:
                    skills_json = required_skills

                # Create new job in PostgreSQL
                pg_job = Job(
                    job_id=mongo_job.get("job_id"),
                    job_title=mongo_job.get("job_title"),
                    description=mongo_job.get("description"),
                    required_skills=skills_json,
                    experience_required=mongo_job.get("experience_required", 0),
                    created_at=mongo_job.get("created_at", datetime.utcnow()),
                    updated_at=mongo_job.get("updated_at", datetime.utcnow()),
                )
                pg_session.add(pg_job)
                stats["jobs"]["migrated"] += 1
                print(f"  ✓ Migrated job: {mongo_job.get('job_title', 'N/A')}")

            except Exception as e:
                print(f"  ✗ Error migrating job {mongo_job.get('job_id')}: {str(e)}")
                stats["jobs"]["errors"] += 1

        print(f"\n✓ Jobs migration complete: {stats['jobs']}")

    except Exception as e:
        print(f"✗ Jobs migration failed: {str(e)}")
        stats["jobs"]["errors"] += 1


def migrate_candidates(mongo_db, pg_session):
    """Migrate candidates collection from MongoDB to PostgreSQL."""
    print("\n" + "=" * 60)
    print("Migrating Candidates...")
    print("=" * 60)

    try:
        mongo_candidates = mongo_db.candidates.find()
        total = mongo_candidates.count()
        print(f"Found {total} candidates in MongoDB")

        for mongo_candidate in mongo_candidates:
            try:
                # Check if candidate already exists in PostgreSQL
                existing = pg_session.query(Candidate).filter_by(
                    candidate_id=mongo_candidate.get("candidate_id")
                ).first()

                if existing:
                    print(f"  ⏭  Skipped candidate: {mongo_candidate.get('name')} (already exists)")
                    stats["candidates"]["skipped"] += 1
                    continue

                # Convert lists to JSON strings
                def to_json_string(data):
                    if isinstance(data, list):
                        return json.dumps(data)
                    return data

                # Create new candidate in PostgreSQL
                pg_candidate = Candidate(
                    candidate_id=mongo_candidate.get("candidate_id"),
                    name=mongo_candidate.get("name", "Unknown"),
                    email=mongo_candidate.get("email"),
                    phone=mongo_candidate.get("phone"),
                    skills=to_json_string(mongo_candidate.get("skills")),
                    education=to_json_string(mongo_candidate.get("education")),
                    experience=to_json_string(mongo_candidate.get("experience")),
                    years_of_experience=mongo_candidate.get("years_of_experience", 0),
                    resume_text=mongo_candidate.get("resume_text"),
                    created_at=mongo_candidate.get("created_at", datetime.utcnow()),
                    updated_at=mongo_candidate.get("updated_at", datetime.utcnow()),
                )
                pg_session.add(pg_candidate)
                stats["candidates"]["migrated"] += 1
                print(f"  ✓ Migrated candidate: {mongo_candidate.get('name')}")

            except Exception as e:
                print(f"  ✗ Error migrating candidate {mongo_candidate.get('name')}: {str(e)}")
                stats["candidates"]["errors"] += 1

        print(f"\n✓ Candidates migration complete: {stats['candidates']}")

    except Exception as e:
        print(f"✗ Candidates migration failed: {str(e)}")
        stats["candidates"]["errors"] += 1


def migrate_rankings(mongo_db, pg_session):
    """Migrate rankings collection from MongoDB to PostgreSQL."""
    print("\n" + "=" * 60)
    print("Migrating Rankings...")
    print("=" * 60)

    try:
        mongo_rankings = mongo_db.rankings.find()
        total = mongo_rankings.count()
        print(f"Found {total} rankings in MongoDB")

        for mongo_ranking in mongo_rankings:
            try:
                # Check if ranking already exists in PostgreSQL
                existing = pg_session.query(Ranking).filter_by(
                    ranking_id=mongo_ranking.get("ranking_id")
                ).first()

                if existing:
                    print(f"  ⏭  Skipped ranking: {mongo_ranking.get('ranking_id')} (already exists)")
                    stats["rankings"]["skipped"] += 1
                    continue

                # Convert lists to JSON strings
                def to_json_string(data):
                    if isinstance(data, list):
                        return json.dumps(data)
                    return data

                # Validate score
                score = mongo_ranking.get("score", 0)
                if not (0 <= score <= 1):
                    print(f"  ⚠  Invalid score {score} for ranking {mongo_ranking.get('ranking_id')}, clamping to [0, 1]")
                    score = max(0, min(1, score))

                # Create new ranking in PostgreSQL
                pg_ranking = Ranking(
                    ranking_id=mongo_ranking.get("ranking_id"),
                    job_id=mongo_ranking.get("job_id"),
                    candidate_id=mongo_ranking.get("candidate_id"),
                    score=score,
                    skills_matched=to_json_string(mongo_ranking.get("skills_matched", [])),
                    skills_missing=to_json_string(mongo_ranking.get("skills_missing", [])),
                    rank=mongo_ranking.get("rank"),
                    created_at=mongo_ranking.get("created_at", datetime.utcnow()),
                )
                pg_session.add(pg_ranking)
                stats["rankings"]["migrated"] += 1
                print(f"  ✓ Migrated ranking: {mongo_ranking.get('ranking_id')} (score: {score:.2f})")

            except Exception as e:
                print(f"  ✗ Error migrating ranking {mongo_ranking.get('ranking_id')}: {str(e)}")
                stats["rankings"]["errors"] += 1

        print(f"\n✓ Rankings migration complete: {stats['rankings']}")

    except Exception as e:
        print(f"✗ Rankings migration failed: {str(e)}")
        stats["rankings"]["errors"] += 1


def main():
    """Main migration function."""
    print("\n" + "=" * 60)
    print("MongoDB → PostgreSQL Data Migration")
    print("=" * 60)
    print()

    # Step 1: Initialize PostgreSQL database
    print("Step 1: Initializing PostgreSQL database...")
    try:
        init_db()
        print("✓ PostgreSQL initialized")
    except Exception as e:
        print(f"✗ Failed to initialize PostgreSQL: {str(e)}")
        print("Please ensure PostgreSQL is running and DATABASE_URL is correct in .env")
        return

    # Step 2: Connect to MongoDB
    print("\nStep 2: Connecting to MongoDB...")
    mongo_client = get_mongo_client()
    if not mongo_client:
        print("Cannot proceed without MongoDB connection.")
        print("If you don't have MongoDB data to migrate, you can skip this step.")
        response = input("Continue without migration? (y/n): ").strip().lower()
        if response == 'y':
            print("Skipping migration. PostgreSQL tables have been created.")
        return

    mongo_db = mongo_client[MONGO_DATABASE]

    # Step 3: Confirm migration
    print("\n" + "=" * 60)
    print("WARNING: This will migrate all data from MongoDB to PostgreSQL.")
    print("=" * 60)
    print(f"MongoDB: {MONGO_URI}{MONGO_DATABASE}")
    print(f"PostgreSQL: {os.getenv('DATABASE_URL', 'Not configured')}")
    print()

    response = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Migration cancelled by user.")
        return

    # Step 4: Perform migration
    print("\nStep 4: Starting migration...")
    try:
        with session_scope() as pg_session:
            migrate_users(mongo_db, pg_session)
            migrate_jobs(mongo_db, pg_session)
            migrate_candidates(mongo_db, pg_session)
            migrate_rankings(mongo_db, pg_session)

            # Commit all changes
            print("\n" + "=" * 60)
            print("Committing changes to PostgreSQL...")
            print("=" * 60)
            # session_scope() automatically commits

    except Exception as e:
        print(f"\n✗ Migration failed with error: {str(e)}")
        print("No data was committed to PostgreSQL.")
        return

    # Step 5: Print summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Users:      {stats['users']['migrated']} migrated, {stats['users']['skipped']} skipped, {stats['users']['errors']} errors")
    print(f"Jobs:       {stats['jobs']['migrated']} migrated, {stats['jobs']['skipped']} skipped, {stats['jobs']['errors']} errors")
    print(f"Candidates: {stats['candidates']['migrated']} migrated, {stats['candidates']['skipped']} skipped, {stats['candidates']['errors']} errors")
    print(f"Rankings:   {stats['rankings']['migrated']} migrated, {stats['rankings']['skipped']} skipped, {stats['rankings']['errors']} errors")
    print("=" * 60)

    total_migrated = sum(s['migrated'] for s in stats.values())
    total_errors = sum(s['errors'] for s in stats.values())

    if total_errors == 0:
        print(f"\n✓ Migration completed successfully! {total_migrated} records migrated.")
        print("\nNext steps:")
        print("1. Verify the data in PostgreSQL")
        print("2. Update your application to use PostgreSQL")
        print("3. Backup MongoDB data before removing it")
    else:
        print(f"\n⚠  Migration completed with {total_errors} errors.")
        print("Please review the errors above and manually migrate failed records.")

    # Close MongoDB connection
    mongo_client.close()
    print("\nMongoDB connection closed.")


if __name__ == "__main__":
    main()
