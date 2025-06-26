# main.py
#!/usr/bin/env python3

import os
import re
from io import BytesIO
from typing import List

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
from docx import Document
from docx.shared import RGBColor
from openai import OpenAI

from resume_evaluator_api import load_api_key, evaluate_resume, generate_interview_questions

# instantiate FastAPI
app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "https://your-frontend-domain.com"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# compile patterns
ZERO_WIDTH = re.compile(r'[\u200B\u200C\u200D\uFEFF]')
WATERMARK  = re.compile(r'\bCONFIDENTIAL\b', re.IGNORECASE)
WHITE_PDF  = re.compile(r'1\s+1\s+1\s+(rg|RG)')

# load OpenAI client once
API_KEY = load_api_key()
client  = OpenAI(api_key=API_KEY)

@app.post("/evaluate/")
async def evaluate(
    job_description: str = Form(...),
    resumes: List[UploadFile] = File(...)
):
    results = []

    for up in resumes:
        fname = up.filename
        ext   = os.path.splitext(fname)[1].lower()
        raw   = await up.read()
        suspicious_flags: List[str] = []

        # 1) extract text & detect tricks
        try:
            if ext == ".pdf":
                reader = PdfReader(BytesIO(raw))
                text   = "\n".join(p.extract_text() or "" for p in reader.pages)
                raw_s  = raw.decode("latin-1", errors="ignore")
                if WHITE_PDF.search(raw_s):
                    suspicious_flags.append("Hidden white text in PDF")
            elif ext == ".docx":
                doc = Document(BytesIO(raw))
                for para in doc.paragraphs:
                    for run in para.runs:
                        c = run.font.color
                        if c and c.rgb == RGBColor(0xFF,0xFF,0xFF):
                            suspicious_flags.append("Hidden white text in DOCX")
                            break
                    if "Hidden white text in DOCX" in suspicious_flags:
                        break
                text = "\n".join(p.text for p in doc.paragraphs)
            elif ext == ".txt":
                text = raw.decode("utf-8", errors="ignore")
            else:
                raise ValueError(f"Unsupported file type: {ext}")

            if ZERO_WIDTH.search(text):
                suspicious_flags.append("Hidden/invisible characters")
            if WATERMARK.search(text):
                suspicious_flags.append("Watermark 'CONFIDENTIAL' detected")

        except Exception as e:
            results.append({"filename": fname, "error": f"Extraction failed: {e}"})
            continue

        # 2) call OpenAI
        try:
            eval_data = evaluate_resume(client, "gpt-4", job_description, text)
            questions = generate_interview_questions(client, "gpt-4", job_description, text)

            summary = (
                f"{eval_data['name']} - {eval_data['match_score']}% match - "
                f"{eval_data['verdict']} [{'green flag' if eval_data['verdict']=='Strong Fit' else 'red flag'}]"
            )
            reasons = (eval_data.get("green_flags", []) + eval_data.get("red_flags", []))[:4]

            results.append({
                "filename": fname,
                "summary": summary,
                "reasons": reasons,
                "interview_questions": questions[:5],
                "suspicious_flags": suspicious_flags
            })
        except Exception as e:
            results.append({"filename": fname, "error": str(e)})

    return {"results": results}
