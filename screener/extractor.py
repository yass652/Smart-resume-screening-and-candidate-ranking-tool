"""
extractor.py
------------
Pulls structured signals out of raw resume text:
  - candidate name (best-effort, first non-empty line)
  - contact email / phone
  - years of experience (regex over date ranges + explicit mentions)
  - education level
  - skills (matched against a configurable skill vocabulary)
"""

import re
from datetime import datetime

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(\+?\d{1,3}[\s.-]?)?(\(?\d{3,4}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}")
YEAR_RANGE_RE = re.compile(
    r"(19|20)\d{2}\s*(?:-|to|–|—)\s*(?:(19|20)\d{2}|present|current)",
    re.IGNORECASE,
)
EXPLICIT_EXP_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)\s*(?:of)?\s*experience", re.IGNORECASE
)

EDUCATION_LEVELS = [
    ("phd", ["phd", "ph.d", "doctorate"]),
    ("master", ["master", "m.tech", "mtech", "msc", "m.sc", "mba", "ms "]),
    ("bachelor", ["bachelor", "b.tech", "btech", "bsc", "b.sc", "b.e", " be "]),
    ("diploma", ["diploma"]),
]

DEFAULT_SKILLS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "sql", "r",
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "data analysis", "data science", "pandas", "numpy",
    "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras",
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "linux",
    "react", "node.js", "django", "flask", "fastapi", "html", "css",
    "excel", "power bi", "tableau", "spark", "hadoop", "airflow",
    "rest api", "microservices", "agile", "scrum", "communication",
    "leadership", "project management", "problem solving",
]


def extract_email(text: str) -> str:
    m = EMAIL_RE.search(text)
    return m.group(0) if m else ""


def extract_phone(text: str) -> str:
    m = PHONE_RE.search(text)
    return m.group(0).strip() if m else ""


def extract_name(text: str) -> str:
    for line in text.strip().splitlines():
        clean = line.strip()
        if 2 <= len(clean.split()) <= 4 and not EMAIL_RE.search(clean) and len(clean) < 60:
            return clean
    return "Unknown Candidate"


def extract_years_experience(text: str) -> float:
    explicit = EXPLICIT_EXP_RE.findall(text)
    if explicit:
        return max(float(x) for x in explicit)

    current_year = datetime.now().year
    total_years = 0.0
    for match in re.finditer(r"((19|20)\d{2})\s*(?:-|to|–|—)\s*((19|20)\d{2}|present|current)", text, re.IGNORECASE):
        start_year = int(match.group(1))
        end_raw = match.group(3).lower()
        end_year = current_year if end_raw in ("present", "current") else int(end_raw)
        if end_year >= start_year:
            total_years += (end_year - start_year)
    return round(total_years, 1)


def extract_education(text: str) -> str:
    lowered = text.lower()
    for level, keywords in EDUCATION_LEVELS:
        for kw in keywords:
            pattern = r"\b" + re.escape(kw.strip()) + r"\b"
            if re.search(pattern, lowered):
                return level
    return "unspecified"


def extract_skills(text: str, skill_vocab=None) -> list:
    vocab = skill_vocab if skill_vocab is not None else DEFAULT_SKILLS
    lowered = text.lower()
    found = []
    for skill in vocab:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, lowered):
            found.append(skill)
    return sorted(set(found))


def extract_profile(text: str, skill_vocab=None) -> dict:
    """Bundles all extracted signals into a single candidate profile dict."""
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "years_experience": extract_years_experience(text),
        "education": extract_education(text),
        "skills": extract_skills(text, skill_vocab),
    }
