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
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment variables")
    return key


def read_resume_file(path: str) -> str:
    """Reads .txt, .pdf, or .docx and returns plain text."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt":
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    elif ext == ".pdf":
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == ".docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def evaluate_resume(client, model: str, job_description: str, resume_text: str) -> dict:
    """
    Sends job description & resume to OpenAI and returns a dict:
    {
      "name": str,
      "match_score": int,
      "verdict": "Strong Fit" | "Weak Fit",
      "green_flags": [str, ...],
      "red_flags": [str, ...]
    }
    """
    prompt = f"""
You are a recruiter assistant. Given a job description and a candidate resume, evaluate how well the candidate fits.

Return a single JSON object with exactly these keys:
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
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"Could not parse JSON response:\n{content}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate resumes from the CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--job-file", help="Path to the job description text file")
    group.add_argument("-t", "--job-text", help="Job description provided as a string")
    parser.add_argument(
        "-r", "--resumes",
        required=True,
        nargs="+",
        help="Paths to resume files (.txt, .pdf, .docx)"
    )
    parser.add_argument("-m", "--model", default="gpt-4", help="OpenAI model to use")
    args = parser.parse_args()

    # Load job description
    if args.job_text:
        job_description = args.job_text
    else:
        with open(args.job_file, "r", encoding="utf-8") as f:
            job_description = f.read()

    # Initialize OpenAI client
    api_key = load_api_key()
    client = OpenAI(api_key=api_key)

    # Evaluate each resume
    results = []
    for path in args.resumes:
        try:
            resume_text = read_resume_file(path)
            data = evaluate_resume(client, args.model, job_description, resume_text)
            results.append(data)
        except Exception as e:
            print(f"Error processing {path}: {e}")

    # Sort by match_score descending
    results.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    # Print results with detailed reasons
    for i, cand in enumerate(results, start=1):
        flag = "[green flag]" if cand.get("verdict") == "Strong Fit" else "[red flag]"
        print(f"{i}. {cand.get('name')} - {cand.get('match_score')}% match - {cand.get('verdict')} {flag}")
        # Print individual reasons
        for reason in cand.get("green_flags", []) + cand.get("red_flags", []):
            print(f"- {reason}")


if __name__ == "__main__":
    main()
