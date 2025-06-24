# resume_evaluator_api.py
#!/usr/bin/env python3

import os
import json
import argparse
from dotenv import load_dotenv
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document

def load_api_key():
    """Load OPENAI_API_KEY from .env and return it."""
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment variables")
    return key

def evaluate_resume(client: OpenAI, model: str,
                    job_description: str, resume_text: str) -> dict:
    """
    Sends job description & resume to OpenAI and returns a dict:
      {
        "name": str,
        "match_score": int,
        "verdict": "Strong Fit"|"Weak Fit",
        "green_flags": [str,...],
        "red_flags": [str,...]
      }
    """
    prompt = f"""
You are a recruiter assistant. Given a job description and a candidate resume, evaluate how well the candidate fits.

Return a JSON object with exactly these keys:
- "name": candidate's full name (string)
- "match_score": integer percentage match (0–100)
- "verdict": either "Strong Fit" or "Weak Fit"
- "green_flags": list of strings describing matching qualifications/skills
- "red_flags": list of strings describing missing requirements or issues

Job Description:
{job_description}

Candidate Resume:
{resume_text}
"""
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    content = resp.choices[0].message.content.strip()
    return json.loads(content)

def generate_interview_questions(client: OpenAI, model: str,
                                 job_description: str,
                                 resume_text: str) -> list:
    """
    Generates 5 tailored interview questions based on job description & resume.
    Returns a JSON array of strings.
    """
    prompt = f"""
Based on the following job description and candidate resume, generate 5 tailored interview questions
that a hiring manager could ask to assess fit. Return as a JSON array of strings.

Job Description:
{job_description}

Candidate Resume:
{resume_text}
"""
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    content = resp.choices[0].message.content.strip()
    return json.loads(content)

def main():
    parser = argparse.ArgumentParser(description="CLI resume evaluator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--job-file", help="Path to job description .txt")
    group.add_argument("-t", "--job-text", help="Job description as a string")
    parser.add_argument("-r", "--resumes", nargs="+", required=True,
                        help="Resume files (.txt, .pdf, .docx)")
    parser.add_argument("-m", "--model", default="gpt-4", help="Which OpenAI model to use")
    args = parser.parse_args()

    job_desc = args.job_text or open(args.job_file, "r", encoding="utf-8").read()
    client   = OpenAI(api_key=load_api_key())

    for path in args.resumes:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".txt":
            resume_text = open(path, encoding="utf-8").read()
        elif ext == ".pdf":
            reader = PdfReader(path)
            resume_text = "\n".join(p.extract_text() or "" for p in reader.pages)
        elif ext == ".docx":
            doc = Document(path)
            resume_text = "\n".join(p.text for p in doc.paragraphs)
        else:
            print(f"Unsupported file type: {path}")
            continue

        eval_data = evaluate_resume(client, args.model, job_desc, resume_text)
        questions = generate_interview_questions(client, args.model, job_desc, resume_text)

        print(f"\nCandidate: {eval_data['name']}")
        print(f"Match:   {eval_data['match_score']}%  Verdict: {eval_data['verdict']}")
        print("Top 4 reasons:")
        for r in (eval_data["green_flags"] + eval_data["red_flags"])[:4]:
            print(f"- {r}")
        print("Interview Questions:")
        for q in questions[:5]:
            print(f"- {q}")

if __name__ == "__main__":
    main()
