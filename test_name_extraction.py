"""
Test script for name extraction logic
"""
from parser import extract_name_from_resume

# Test Case 1: Resume with name at the top
test_resume_1 = """John Michael Smith
Software Engineer
Email: john.smith@email.com | Phone: (555) 123-4567
LinkedIn: linkedin.com/in/johnsmith

EXPERIENCE
Senior Software Engineer at Tech Corp (2020-Present)
- Developed microservices using Python and Django
"""

# Test Case 2: Resume with labeled name field
test_resume_2 = """RESUME

Name: Sarah Jane Williams
Email: sarah.williams@email.com
Phone: 555-987-6543

EDUCATION
Master of Science in Computer Science
University of California, 2019
"""

# Test Case 3: Resume with centered header
test_resume_3 = """
========================================
       MUHAMMAD AHMED KHAN
       Data Scientist
========================================
ahmed.khan@email.com | +1-555-234-5678

PROFESSIONAL SUMMARY
Experienced data scientist with 5+ years...
"""

# Test Case 4: Resume with name in contact section
test_resume_4 = """Ali Hassan Butt
Email: ali.butt@email.com
Mobile: +92-300-1234567

CAREER OBJECTIVE
To work as a software developer...
"""

# Test Case 5: Simple resume format
test_resume_5 = """Fatima Zahra
Junior Developer

Education:
BS Computer Science, 2023
NUST, Islamabad

Skills: Python, JavaScript, React
"""

print("Testing Name Extraction Logic")
print("=" * 50)

test_cases = [
    (test_resume_1, "John Michael Smith"),
    (test_resume_2, "Sarah Jane Williams"),
    (test_resume_3, "MUHAMMAD AHMED KHAN"),
    (test_resume_4, "Ali Hassan Butt"),
    (test_resume_5, "Fatima Zahra"),
]

for i, (resume, expected) in enumerate(test_cases, 1):
    extracted_name = extract_name_from_resume(resume)
    status = "✓ PASS" if extracted_name.lower() == expected.lower() else "✗ FAIL"
    print(f"\nTest {i}: {status}")
    print(f"Expected: {expected}")
    print(f"Extracted: {extracted_name}")

print("\n" + "=" * 50)
print("Test completed!")
