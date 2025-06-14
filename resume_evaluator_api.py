#!/usr/bin/env python3
# resume_evaluator_api.py

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
    ext = os.path.splitext(path)[1].lower()
    if ext == '.txt':
        return open(path, 'r', encoding='utf-8').read()
    elif ext == '.pdf':
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == '.docx':
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def evaluate_resume(client, model, job_description: str, resume_text: str) -> dict:
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
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role":"user","content":prompt}]
    )
    content = resp.choices[0].message.content.strip()
    return json.loads(content)

def main():
    parser = argparse.ArgumentParser(description="Evaluate resumes from the CLI")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("-f","--job-file", help="Path to job description .txt")
    grp.add_argument("-t","--job-text", help="Job description as a string")
    parser.add_argument("-r","--resumes", nargs="+", required=True,
                        help="One or more resume files (.txt/.pdf/.docx)")
    parser.add_argument("-m","--model", default="gpt-4")
    args = parser.parse_args()

    job = args.job_text or open(args.job_file,"r",encoding="utf-8").read()

    client = OpenAI(api_key=load_api_key())
    results = []
    for path in args.resumes:
        try:
            text = read_resume_file(path)
            data = evaluate_resume(client, args.model, job, text)
            flag = "[green flag]" if data["verdict"]=="Strong Fit" else "[red flag]"
            results.append((data["name"], data["match_score"], data["verdict"], flag))
        except Exception as e:
            print(f"Error with {path}: {e}")
    # sort & print
    for i,(n,score,verdict,flag) in enumerate(sorted(results, key=lambda x:-x[1]),1):
        print(f"{i}. {n} - {score}% match - {verdict} {flag}")

if __name__=="__main__":
    main()
