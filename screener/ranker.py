"""
ranker.py
---------
Scores and ranks candidates against a job description using:
  1. TF-IDF + cosine similarity  -> overall semantic/textual match
  2. Skill overlap               -> % of required skills present
  3. Experience fit              -> how well years-of-experience meets the minimum
  4. Education fit               -> bonus if required degree level is met

Final score is a configurable weighted blend of the four signals (0-100).
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

EDUCATION_RANK = {"unspecified": 0, "diploma": 1, "bachelor": 2, "master": 3, "phd": 4}

DEFAULT_WEIGHTS = {
    "text_similarity": 0.40,
    "skill_match": 0.35,
    "experience_fit": 0.15,
    "education_fit": 0.10,
}


def compute_text_similarity(job_text: str, resume_texts: list) -> list:
    """TF-IDF cosine similarity between the job description and each resume."""
    corpus = [job_text] + resume_texts
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(corpus)
    job_vec = tfidf_matrix[0:1]
    resume_vecs = tfidf_matrix[1:]
    sims = cosine_similarity(job_vec, resume_vecs)[0]
    return [round(float(s) * 100, 2) for s in sims]


def compute_skill_match(required_skills: list, candidate_skills: list) -> float:
    if not required_skills:
        return 100.0
    req = set(s.lower() for s in required_skills)
    have = set(s.lower() for s in candidate_skills)
    overlap = req & have
    return round(100 * len(overlap) / len(req), 2)


def compute_experience_fit(min_years_required: float, candidate_years: float) -> float:
    if min_years_required <= 0:
        return 100.0
    if candidate_years >= min_years_required:
        # Meets or exceeds requirement -> full score (mild bonus capped at 100)
        return 100.0
    # Partial credit, scaled linearly toward zero
    return round(max(0.0, 100 * candidate_years / min_years_required), 2)


def compute_education_fit(min_education_required: str, candidate_education: str) -> float:
    req_rank = EDUCATION_RANK.get((min_education_required or "unspecified").lower(), 0)
    cand_rank = EDUCATION_RANK.get((candidate_education or "unspecified").lower(), 0)
    if req_rank == 0:
        return 100.0
    return 100.0 if cand_rank >= req_rank else round(100 * cand_rank / req_rank, 2)


def rank_candidates(job_description: str, candidates: list, job_requirements: dict,
                     weights: dict = None) -> list:
    """
    candidates: list of dicts, each containing:
        {"filename": str, "raw_text": str, "profile": {...from extractor.extract_profile...}}
    job_requirements: {
        "required_skills": [...],
        "min_years_experience": float,
        "min_education": "bachelor" | "master" | ... | ""
    }
    Returns candidates sorted by final_score (desc), each annotated with a score breakdown.
    """
    w = weights or DEFAULT_WEIGHTS
    resume_texts = [c["raw_text"] for c in candidates]
    text_sims = compute_text_similarity(job_description, resume_texts) if resume_texts else []

    results = []
    for cand, text_sim in zip(candidates, text_sims):
        profile = cand["profile"]
        skill_score = compute_skill_match(job_requirements.get("required_skills", []), profile["skills"])
        exp_score = compute_experience_fit(job_requirements.get("min_years_experience", 0), profile["years_experience"])
        edu_score = compute_education_fit(job_requirements.get("min_education", ""), profile["education"])

        final_score = (
            w["text_similarity"] * text_sim
            + w["skill_match"] * skill_score
            + w["experience_fit"] * exp_score
            + w["education_fit"] * edu_score
        )

        matched_skills = sorted(set(s.lower() for s in job_requirements.get("required_skills", []))
                                 & set(s.lower() for s in profile["skills"]))
        missing_skills = sorted(set(s.lower() for s in job_requirements.get("required_skills", []))
                                 - set(s.lower() for s in profile["skills"]))

        results.append({
            "filename": cand["filename"],
            "name": profile["name"],
            "email": profile["email"],
            "phone": profile["phone"],
            "years_experience": profile["years_experience"],
            "education": profile["education"],
            "final_score": round(final_score, 2),
            "breakdown": {
                "text_similarity": text_sim,
                "skill_match": skill_score,
                "experience_fit": exp_score,
                "education_fit": edu_score,
            },
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
        })

    results.sort(key=lambda r: r["final_score"], reverse=True)
    for i, r in enumerate(results, start=1):
        r["rank"] = i
    return results
