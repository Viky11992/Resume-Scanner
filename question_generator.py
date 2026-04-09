"""
Question Generator Module

Generates tailored interview questions using either OpenAI's GPT-4 or Google's Gemini API
based on candidate profile, job requirements, and difficulty level.
"""

import json
import os
from openai import OpenAI


def generate_interview_questions_gemini(
    candidate_skills, job_title, experience_years, difficulty="medium"
):
    """
    Generate interview questions using Google's Gemini API (free tier).

    Uses Gemini to produce 10 questions across categories:
    3 technical, 3 behavioral, 2 situational, 2 role-specific.

    Args:
        candidate_skills (list): List of the candidate's skills.
        job_title (str): Title of the position being interviewed for.
        experience_years (int): Candidate's years of experience.
        difficulty (str): Question difficulty — "easy", "medium", or "hard".
                          Defaults to "medium".

    Returns:
        list: List of 10 dicts, each containing:
            - question (str): The interview question.
            - type (str): Category — technical, behavioral, situational, role-specific.
            - difficulty (str): Difficulty level.
            - expected_answer_hints (list): Key points the interviewer should listen for.

    Raises:
        ValueError: If inputs are invalid.
        EnvironmentError: If GEMINI_API_KEY is not set.
        Exception: If the API call fails or the response is malformed.
    """
    try:
        import google.generativeai as genai

        # Validate inputs
        if not candidate_skills:
            raise ValueError("candidate_skills cannot be empty")
        if not job_title or not job_title.strip():
            raise ValueError("job_title is required")
        if not isinstance(experience_years, int) or experience_years < 0:
            raise ValueError("experience_years must be a non-negative integer")

        valid_difficulties = ["easy", "medium", "hard"]
        if difficulty not in valid_difficulties:
            raise ValueError(f"difficulty must be one of {valid_difficulties}")

        # Get API key from environment
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please set it before calling this function."
            )

        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Build the prompt
        prompt = (
            "You are an expert technical interviewer. Generate interview questions "
            "that are tailored to the candidate's background and the job they are applying for. "
            "Return ONLY valid JSON with no markdown formatting, no code blocks, no explanations. "
            "The JSON must be a list of exactly 10 objects with keys: "
            '"question", "type", "difficulty", "expected_answer_hints". '
            "Types: technical, behavioral, situational, role-specific. "
            "Provide exactly: 3 technical, 3 behavioral, 2 situational, 2 role-specific. "
            "expected_answer_hints should be a list of 2-4 short bullet points.\n\n"
            f"Candidate Skills: {', '.join(candidate_skills)}\n"
            f"Job Title: {job_title}\n"
            f"Years of Experience: {experience_years}\n"
            f"Difficulty Level: {difficulty}\n\n"
            f"Make the questions appropriately challenging for a candidate "
            f"with {experience_years} years of experience applying for a "
            f"{job_title} role who knows these skills: {', '.join(candidate_skills)}.\n\n"
            f"Return only the JSON array."
        )

        response = model.generate_content(prompt)
        raw_text = response.text

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```", 2)[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        questions = json.loads(raw_text)

        # Validate the response structure
        if not isinstance(questions, list) or len(questions) != 10:
            raise Exception(
                f"Expected exactly 10 questions, got {len(questions)}"
            )

        required_keys = {"question", "type", "difficulty", "expected_answer_hints"}
        for i, q in enumerate(questions):
            if not required_keys.issubset(q.keys()):
                raise Exception(
                    f"Question {i+1} is missing required keys: {required_keys - q.keys()}"
                )

        return questions

    except ImportError:
        raise Exception(
            "google-generativeai package is not installed. "
            "Install it with: pip install google-generativeai"
        )
    except (ValueError, EnvironmentError):
        raise
    except json.JSONDecodeError as e:
        raise Exception(
            f"Failed to parse Gemini response as JSON: {str(e)}\nRaw response: {raw_text}"
        )
    except Exception as e:
        if isinstance(e, (ValueError, EnvironmentError)):
            raise
        raise Exception(f"Error generating interview questions with Gemini: {str(e)}")


def generate_interview_questions_groq(
    candidate_skills, job_title, experience_years, difficulty="medium"
):
    """
    Generate interview questions using Groq API (free tier).

    Uses Groq to produce 10 questions across categories:
    3 technical, 3 behavioral, 2 situational, 2 role-specific.

    Args:
        candidate_skills (list): List of the candidate's skills.
        job_title (str): Title of the position being interviewed for.
        experience_years (int): Candidate's years of experience.
        difficulty (str): Question difficulty — "easy", "medium", or "hard".
                          Defaults to "medium".

    Returns:
        list: List of 10 dicts, each containing:
            - question (str): The interview question.
            - type (str): Category — technical, behavioral, situational, role-specific.
            - difficulty (str): Difficulty level.
            - expected_answer_hints (list): Key points the interviewer should listen for.

    Raises:
        ValueError: If inputs are invalid.
        EnvironmentError: If GROQ_API_KEY is not set.
        Exception: If the API call fails or the response is malformed.
    """
    try:
        from groq import Groq

        # Validate inputs
        if not candidate_skills:
            raise ValueError("candidate_skills cannot be empty")
        if not job_title or not job_title.strip():
            raise ValueError("job_title is required")
        if not isinstance(experience_years, int) or experience_years < 0:
            raise ValueError("experience_years must be a non-negative integer")

        valid_difficulties = ["easy", "medium", "hard"]
        if difficulty not in valid_difficulties:
            raise ValueError(f"difficulty must be one of {valid_difficulties}")

        # Get API key from environment
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY environment variable is not set. "
                "Please set it before calling this function."
            )

        client = Groq(api_key=api_key)

        # Build the system and user prompt
        system_prompt = (
            "You are an expert technical interviewer. Generate interview questions "
            "that are tailored to the candidate's background and the job they are applying for. "
            "Return ONLY valid JSON with no markdown formatting, no code blocks, no explanations. "
            "The JSON must be a list of exactly 10 objects with keys: "
            '"question", "type", "difficulty", "expected_answer_hints". '
            "Types: technical, behavioral, situational, role-specific. "
            "Provide exactly: 3 technical, 3 behavioral, 2 situational, 2 role-specific. "
            "expected_answer_hints should be a list of 2-4 short bullet points."
        )

        user_prompt = (
            f"Generate interview questions with the following details:\n\n"
            f"Candidate Skills: {', '.join(candidate_skills)}\n"
            f"Job Title: {job_title}\n"
            f"Years of Experience: {experience_years}\n"
            f"Difficulty Level: {difficulty}\n\n"
            f"Make the questions appropriately challenging for a candidate "
            f"with {experience_years} years of experience applying for a "
            f"{job_title} role who knows these skills: {', '.join(candidate_skills)}.\n\n"
            f"Return only the JSON array."
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        # Parse the response
        raw_text = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```", 2)[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        questions = json.loads(raw_text)

        # Validate the response structure
        if not isinstance(questions, list) or len(questions) != 10:
            raise Exception(
                f"Expected exactly 10 questions, got {len(questions)}"
            )

        required_keys = {"question", "type", "difficulty", "expected_answer_hints"}
        for i, q in enumerate(questions):
            if not required_keys.issubset(q.keys()):
                raise Exception(
                    f"Question {i+1} is missing required keys: {required_keys - q.keys()}"
                )

        return questions

    except ImportError:
        raise Exception(
            "groq package is not installed. "
            "Install it with: pip install groq"
        )
    except (ValueError, EnvironmentError):
        raise
    except json.JSONDecodeError as e:
        raise Exception(
            f"Failed to parse Groq response as JSON: {str(e)}\nRaw response: {raw_text}"
        )
    except Exception as e:
        if isinstance(e, (ValueError, EnvironmentError)):
            raise
        raise Exception(f"Error generating interview questions with Groq: {str(e)}")


def generate_interview_questions(
    candidate_skills, job_title, experience_years, difficulty="medium", provider="groq"
):
    """
    Generate interview questions tailored to a specific candidate and role.

    Uses either OpenAI GPT-4, Google Gemini, or Groq to produce 10 questions across categories:
    3 technical, 3 behavioral, 2 situational, 2 role-specific.

    Args:
        candidate_skills (list): List of the candidate's skills.
        job_title (str): Title of the position being interviewed for.
        experience_years (int): Candidate's years of experience.
        difficulty (str): Question difficulty — "easy", "medium", or "hard".
                          Defaults to "medium".
        provider (str): AI provider to use — "groq" (default), "gemini", or "openai".

    Returns:
        list: List of 10 dicts, each containing:
            - question (str): The interview question.
            - type (str): Category — technical, behavioral, situational, role-specific.
            - difficulty (str): Difficulty level.
            - expected_answer_hints (list): Key points the interviewer should listen for.

    Raises:
        ValueError: If inputs are invalid.
        EnvironmentError: If required API key is not set.
        Exception: If the API call fails or the response is malformed.
    """
    provider = provider.lower()
    if provider == "groq":
        return generate_interview_questions_groq(
            candidate_skills, job_title, experience_years, difficulty
        )
    elif provider == "gemini":
        return generate_interview_questions_gemini(
            candidate_skills, job_title, experience_years, difficulty
        )
    else:
        return generate_interview_questions_openai(
            candidate_skills, job_title, experience_years, difficulty
        )


def generate_interview_questions_openai(
    candidate_skills, job_title, experience_years, difficulty="medium"
):
    """
    Generate interview questions using OpenAI's GPT-4 API.

    Uses OpenAI GPT-4 to produce 10 questions across categories:
    3 technical, 3 behavioral, 2 situational, 2 role-specific.

    Args:
        candidate_skills (list): List of the candidate's skills.
        job_title (str): Title of the position being interviewed for.
        experience_years (int): Candidate's years of experience.
        difficulty (str): Question difficulty — "easy", "medium", or "hard".
                          Defaults to "medium".

    Returns:
        list: List of 10 dicts, each containing:
            - question (str): The interview question.
            - type (str): Category — technical, behavioral, situational, role-specific.
            - difficulty (str): Difficulty level.
            - expected_answer_hints (list): Key points the interviewer should listen for.

    Raises:
        ValueError: If inputs are invalid.
        EnvironmentError: If OPENAI_API_KEY is not set.
        Exception: If the API call fails or the response is malformed.
    """
    try:
        # Validate inputs
        if not candidate_skills:
            raise ValueError("candidate_skills cannot be empty")
        if not job_title or not job_title.strip():
            raise ValueError("job_title is required")
        if not isinstance(experience_years, int) or experience_years < 0:
            raise ValueError("experience_years must be a non-negative integer")

        valid_difficulties = ["easy", "medium", "hard"]
        if difficulty not in valid_difficulties:
            raise ValueError(f"difficulty must be one of {valid_difficulties}")

        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please set it before calling this function."
            )

        client = OpenAI(api_key=api_key)

        # Build the system and user prompt
        system_prompt = (
            "You are an expert technical interviewer. Generate interview questions "
            "that are tailored to the candidate's background and the job they are applying for. "
            "Return ONLY valid JSON with no markdown formatting, no code blocks, no explanations. "
            "The JSON must be a list of exactly 10 objects with keys: "
            '"question", "type", "difficulty", "expected_answer_hints". '
            "Types: technical, behavioral, situational, role-specific. "
            "Provide exactly: 3 technical, 3 behavioral, 2 situational, 2 role-specific. "
            "expected_answer_hints should be a list of 2-4 short bullet points."
        )

        user_prompt = (
            f"Generate interview questions with the following details:\n\n"
            f"Candidate Skills: {', '.join(candidate_skills)}\n"
            f"Job Title: {job_title}\n"
            f"Years of Experience: {experience_years}\n"
            f"Difficulty Level: {difficulty}\n\n"
            f"Make the questions appropriately challenging for a candidate "
            f"with {experience_years} years of experience applying for a "
            f"{job_title} role who knows these skills: {', '.join(candidate_skills)}.\n\n"
            f"Return only the JSON array."
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        # Parse the response
        raw_text = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```", 2)[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        questions = json.loads(raw_text)

        # Validate the response structure
        if not isinstance(questions, list) or len(questions) != 10:
            raise Exception(
                f"Expected exactly 10 questions, got {len(questions)}"
            )

        required_keys = {"question", "type", "difficulty", "expected_answer_hints"}
        for i, q in enumerate(questions):
            if not required_keys.issubset(q.keys()):
                raise Exception(
                    f"Question {i+1} is missing required keys: {required_keys - q.keys()}"
                )

        return questions

    except (ValueError, EnvironmentError):
        raise
    except json.JSONDecodeError as e:
        raise Exception(
            f"Failed to parse GPT-4 response as JSON: {str(e)}\nRaw response: {raw_text}"
        )
    except Exception as e:
        if isinstance(e, (ValueError, EnvironmentError)):
            raise
        raise Exception(f"Error generating interview questions: {str(e)}")
