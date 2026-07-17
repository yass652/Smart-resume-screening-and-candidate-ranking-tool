# Smart Resume Screening and Candidate Ranking Tool

An NLP-based tool that parses resumes (PDF / DOCX / TXT), extracts structured
candidate profiles, and ranks candidates against a job description using a
weighted blend of text similarity, skill overlap, experience, and education fit.

## How it works

```
resumes (.pdf/.docx/.txt)          job_description.txt
        │                                  │
        ▼                                  ▼
  screener/parser.py            main.py parses optional
  (extract raw text)             REQUIRED_SKILLS / MIN_YEARS /
        │                        MIN_EDUCATION header
        ▼                                  │
  screener/extractor.py                    │
  (name, email, phone, years                │
   experience, education, skills)           │
        │                                  │
        └──────────────┬───────────────────┘
                        ▼
              screener/ranker.py
     TF-IDF + cosine similarity (text match)
     + skill overlap %
     + experience fit %
     + education fit %
     = weighted final_score (0-100)
                        │
                        ▼
              ranked candidate list
        (console, CSV, and/or JSON output)
```

### Scoring breakdown (default weights)
| Signal            | Weight | What it measures                                      |
|--------------------|--------|--------------------------------------------------------|
| Text similarity     | 40%    | TF-IDF cosine similarity between resume and job text   |
| Skill match         | 35%    | % of required skills found in the resume                |
| Experience fit       | 15%    | Candidate years vs. minimum years required               |
| Education fit         | 10%    | Candidate degree level vs. minimum required level         |

Weights are configurable in `screener/ranker.py` (`DEFAULT_WEIGHTS`), or can be
passed programmatically to `rank_candidates(..., weights={...})`.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py --job sample_data/job_description.txt --resumes sample_data/resumes --top 5
```

Optional flags:
- `--out-csv results.csv` — write full ranked results to CSV
- `--out-json results.json` — write full ranked results to JSON
- `--top N` — number of top candidates to print (default 10)

### Job description format

The job description file can optionally start with a metadata header:

```
REQUIRED_SKILLS: python, sql, machine learning
MIN_YEARS_EXPERIENCE: 3
MIN_EDUCATION: bachelor
---
<free-text job description goes here>
```

If the header is omitted, the tool ranks purely on text similarity with no
hard requirements.

## Project structure

```
resume_screener/
├── main.py                     # CLI entry point
├── requirements.txt
├── screener/
│   ├── parser.py                # PDF/DOCX/TXT text extraction
│   ├── extractor.py             # name, email, phone, skills, experience, education
│   └── ranker.py                 # TF-IDF similarity + weighted scoring
└── sample_data/
    ├── job_description.txt
    └── resumes/                 # 3 sample resumes (strong/medium/weak match)
```

## Extending it

- **Skill vocabulary**: edit `DEFAULT_SKILLS` in `screener/extractor.py`, or
  pass a custom list into `extract_profile(text, skill_vocab=[...])`.
- **Scoring weights**: edit `DEFAULT_WEIGHTS` in `screener/ranker.py`.
- **Better semantic matching**: swap the TF-IDF vectorizer in
  `compute_text_similarity` for sentence embeddings (e.g. `sentence-transformers`)
  if you need to catch synonyms/paraphrasing that keyword-based TF-IDF misses.
- **Web UI**: wrap `screener/` in a Flask/FastAPI app with a file-upload form,
  or build a React front end that calls the ranking logic as an API.

## Notes / limitations

- Text extraction quality depends on how the source PDF/DOCX is formatted
  (scanned/image-only PDFs won't extract text without OCR).
- Skill and education detection are keyword/pattern-based, not a full
  semantic parser — for production use, expand the vocab and review edge cases.
- This is a decision-support tool, not an autonomous hiring decision-maker;
  a human should always review shortlists, particularly to check for bias in
  the underlying resume data and job requirements.
# Project Screenshots

## working
<img width="2880" height="1796" alt="Screenshot 2026-07-17 224755" src="https://github.com/user-attachments/assets/7d254a37-39cc-447d-977c-e18d6e3a4ba2" />


## output 
<img width="1914" height="1176" alt="Screenshot 2026-07-17 224822" src="https://github.com/user-attachments/assets/6045c10c-0938-4dfd-9413-41cac1823132" />




