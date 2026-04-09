"""
PostgreSQL Integration Test Script

Tests database connection, table creation, and CRUD operations.
Run this to verify PostgreSQL is properly configured.
"""

import sys
from datetime import datetime

def test_imports():
    """Test that all required modules can be imported."""
    print("=" * 60)
    print("Test 1: Importing modules...")
    print("=" * 60)
    try:
        from database_postgres import (
            User, Job, Candidate, Ranking,
            init_db, check_connection, get_session, session_scope,
            get_database_status
        )
        from database import save_job, save_candidate, save_ranking, get_all_rankings
        from auth import hash_password, verify_password, add_user, get_user_by_username
        print("✓ All modules imported successfully\n")
        return True
    except Exception as e:
        print(f"✗ Import failed: {str(e)}\n")
        return False


def test_connection():
    """Test database connectivity."""
    print("=" * 60)
    print("Test 2: Database connection...")
    print("=" * 60)
    try:
        from database_postgres import check_connection
        if check_connection():
            print("✓ Database connection successful\n")
            return True
        else:
            print("✗ Database connection failed")
            print("  Please ensure PostgreSQL is running and DATABASE_URL is correct\n")
            return False
    except Exception as e:
        print(f"✗ Connection test failed: {str(e)}\n")
        return False


def test_table_creation():
    """Test that tables can be created."""
    print("=" * 60)
    print("Test 3: Table creation...")
    print("=" * 60)
    try:
        from database_postgres import init_db
        init_db()
        print("✓ Tables created successfully\n")
        return True
    except Exception as e:
        print(f"✗ Table creation failed: {str(e)}\n")
        return False


def test_user_crud():
    """Test user CRUD operations."""
    print("=" * 60)
    print("Test 4: User CRUD operations...")
    print("=" * 60)
    try:
        from auth import add_user, get_user_by_username, get_all_users, update_user, delete_user
        import uuid

        # Create test user
        test_username = f"test_user_{uuid.uuid4().hex[:8]}"
        print(f"  Creating user: {test_username}")
        user = add_user(
            username=test_username,
            password="testpass123",
            role="recruiter",
            name="Test User",
            email=f"{test_username}@test.com"
        )
        print(f"  ✓ User created: {user['username']}")

        # Read user
        print(f"  Reading user: {test_username}")
        fetched_user = get_user_by_username(test_username)
        if fetched_user and fetched_user['username'] == test_username:
            print(f"  ✓ User fetched successfully")
        else:
            print(f"  ✗ User fetch failed")
            return False

        # Update user
        print(f"  Updating user name")
        update_user(fetched_user['user_id'], name="Updated Test User")
        updated_user = get_user_by_username(test_username)
        if updated_user['name'] == "Updated Test User":
            print(f"  ✓ User updated successfully")
        else:
            print(f"  ✗ User update failed")
            return False

        # Delete user
        print(f"  Deleting user")
        delete_user(fetched_user['user_id'])
        deleted_user = get_user_by_username(test_username)
        if not deleted_user:
            print(f"  ✓ User deleted successfully")
        else:
            print(f"  ✗ User deletion failed")
            return False

        print("✓ User CRUD operations test passed\n")
        return True

    except Exception as e:
        print(f"✗ User CRUD test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_job_candidate_ranking():
    """Test job, candidate, and ranking operations."""
    print("=" * 60)
    print("Test 5: Job, Candidate, and Ranking operations...")
    print("=" * 60)
    try:
        from database import save_job, save_candidate, save_ranking, get_all_rankings
        import uuid

        # Create test job
        test_job_id = f"test_job_{uuid.uuid4().hex[:8]}"
        print(f"  Creating job: {test_job_id}")
        job_data = {
            "job_id": test_job_id,
            "job_title": "Software Engineer",
            "description": "We are looking for a software engineer",
            "required_skills": ["Python", "SQL", "React"],
            "experience_required": 3,
        }
        save_job(job_data)
        print(f"  ✓ Job saved successfully")

        # Create test candidate
        test_candidate_id = f"test_candidate_{uuid.uuid4().hex[:8]}"
        print(f"  Creating candidate: {test_candidate_id}")
        candidate_data = {
            "candidate_id": test_candidate_id,
            "name": "Test Candidate",
            "email": "candidate@test.com",
            "phone": "123-456-7890",
            "skills": ["Python", "SQL"],
            "education": [{"degree": "BS CS", "institution": "Test University"}],
            "experience": [{"title": "Developer", "company": "Test Corp"}],
            "years_of_experience": 2,
            "resume_text": "Sample resume text",
        }
        save_candidate(candidate_data)
        print(f"  ✓ Candidate saved successfully")

        # Create test ranking
        test_ranking_id = f"test_ranking_{uuid.uuid4().hex[:8]}"
        print(f"  Creating ranking: {test_ranking_id}")
        ranking_data = {
            "ranking_id": test_ranking_id,
            "job_id": test_job_id,
            "candidate_id": test_candidate_id,
            "score": 0.75,
            "skills_matched": ["Python", "SQL"],
            "skills_missing": ["React"],
            "rank": 1,
        }
        save_ranking(ranking_data)
        print(f"  ✓ Ranking saved successfully")

        # Fetch rankings
        print(f"  Fetching rankings for job: {test_job_id}")
        rankings = get_all_rankings(test_job_id)
        if rankings and len(rankings) > 0:
            print(f"  ✓ Rankings fetched successfully: {len(rankings)} record(s)")
        else:
            print(f"  ✗ Rankings fetch failed")
            return False

        print("✓ Job, Candidate, and Ranking operations test passed\n")
        return True

    except Exception as e:
        print(f"✗ Job/Candidate/Ranking test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_database_status():
    """Test database status reporting."""
    print("=" * 60)
    print("Test 6: Database status...")
    print("=" * 60)
    try:
        from database import get_database_status
        status = get_database_status()
        print(f"  Database Status:")
        print(f"    Connected: {status.get('connected')}")
        print(f"    Type: {status.get('database_type')}")
        print(f"    Users: {status.get('user_count', 0)}")
        print(f"    Candidates: {status.get('candidate_count', 0)}")
        print(f"    Rankings: {status.get('ranking_count', 0)}")
        print("✓ Database status check passed\n")
        return True
    except Exception as e:
        print(f"✗ Database status check failed: {str(e)}\n")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PostgreSQL Integration Tests")
    print("=" * 60 + "\n")

    tests = [
        test_imports,
        test_connection,
        test_table_creation,
        test_user_crud,
        test_job_candidate_ranking,
        test_database_status,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test crashed: {str(e)}\n")
            results.append(False)

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if all(results):
        print("\n✓ All tests passed! PostgreSQL integration is working correctly.")
        print("\nYou can now run: streamlit run app.py")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the errors above.")
        print("Check POSTGRESQL_SETUP.md for configuration help.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
