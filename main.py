"""
Smart Resume Screening and Candidate Ranking Tool
===================================================
CLI entry point.

Usage:
    python main.py --job sample_data/job_description.txt --resumes sample_data/resumes --top 5

The job description file can optionally start with a small metadata header:

    REQUIRED_SKILLS: python, sql, machine learning
    MIN_YEARS_EXPERIENCE: 3
    MIN_EDUCATION: bachelor
    ---
    <free text job description below this line>

If no header is given, the tool falls back to sensible defaults (no hard
skill/experience/education requirements — pure text-similarity ranking).
"""

import argparse
import csv
import json
import os
import sys

from screener import parser as resume_parser
from screener import extractor
from screener import ranker


def parse_job_file(job_filepath: str):
    with open(job_filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    requirements = {"required_skills": [], "min_years_experience": 0, "min_education": ""}
    body = content

    if "---" in content:
        header, body = content.split("---", 1)
        for line in header.strip().splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().upper()
            value = value.strip()
            if key == "REQUIRED_SKILLS":
                requirements["required_skills"] = [s.strip() for s in value.split(",") if s.strip()]
            elif key == "MIN_YEARS_EXPERIENCE":
                try:
                    requirements["min_years_experience"] = float(value)
                except ValueError:
                    pass
            elif key == "MIN_EDUCATION":
                requirements["min_education"] = value.lower()

    return body.strip(), requirements


def main():
    ap = argparse.ArgumentParser(description="Smart Resume Screening and Candidate Ranking Tool")
    ap.add_argument("--job", required=True, help="Path to job description .txt file")
    ap.add_argument("--resumes", required=True, help="Folder containing candidate resumes (.pdf/.docx/.txt)")
    ap.add_argument("--top", type=int, default=10, help="Number of top candidates to display")
    ap.add_argument("--out-csv", default=None, help="Optional path to write full ranked results as CSV")
    ap.add_argument("--out-json", default=None, help="Optional path to write full ranked results as JSON")
    args = ap.parse_args()

    if not os.path.isfile(args.job):
        sys.exit(f"Job description file not found: {args.job}")
    if not os.path.isdir(args.resumes):
        sys.exit(f"Resumes folder not found: {args.resumes}")

    job_text, job_requirements = parse_job_file(args.job)

    print(f"Job requirements detected:")
    print(f"  Required skills : {', '.join(job_requirements['required_skills']) or '(none specified)'}")
    print(f"  Min experience  : {job_requirements['min_years_experience']} years")
    print(f"  Min education   : {job_requirements['min_education'] or '(none specified)'}")
    print()

    raw_resumes = resume_parser.load_resumes_from_folder(args.resumes)
    if not raw_resumes:
        sys.exit("No parsable resumes found in the given folder.")

    candidates = []
    for fname, text in raw_resumes.items():
        profile = extractor.extract_profile(text)
        candidates.append({"filename": fname, "raw_text": text, "profile": profile})

    results = ranker.rank_candidates(job_text, candidates, job_requirements)

    print(f"Ranked {len(results)} candidate(s):\n")
    for r in results[: args.top]:
        print(f"#{r['rank']}  {r['name']}  —  {r['final_score']}/100")
        print(f"    file: {r['filename']}   experience: {r['years_experience']}y   education: {r['education']}")
        print(f"    breakdown: text={r['breakdown']['text_similarity']}  "
              f"skills={r['breakdown']['skill_match']}  "
              f"experience={r['breakdown']['experience_fit']}  "
              f"education={r['breakdown']['education_fit']}")
        if r["matched_skills"]:
            print(f"    matched skills: {', '.join(r['matched_skills'])}")
        if r["missing_skills"]:
            print(f"    missing skills: {', '.join(r['missing_skills'])}")
        print()

    if args.out_csv:
        with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["rank", "name", "filename", "email", "phone", "final_score",
                          "years_experience", "education", "matched_skills", "missing_skills"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                row = {k: r[k] for k in fieldnames if k in r}
                row["matched_skills"] = "; ".join(r["matched_skills"])
                row["missing_skills"] = "; ".join(r["missing_skills"])
                writer.writerow(row)
        print(f"Full results written to {args.out_csv}")

    if args.out_json:
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Full results written to {args.out_json}")


if __name__ == "__main__":
    main()
