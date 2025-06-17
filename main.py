# main.py
#!/usr/bin/env python3

import os
from io import BytesIO
from typing import List

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
from docx import Document
from openai import OpenAI

from resume_evaluator_api import load_api_key, evaluate_resume

# Load API key and instantiate OpenAI client
API_KEY = load_api_key()
client  = OpenAI(api_key=API_KEY)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.post("/evaluate/")
async def evaluate(
    job_description: str = Form(...),
    resumes: List[UploadFile] = File(...)
):
    results = []

    for up in resumes:
        ext = os.path.splitext(up.filename)[1].lower()
        raw = await up.read()

        # Extract text
        try:
            if ext == ".pdf":
                reader = PdfReader(BytesIO(raw))
                text = "\n".join(p.extract_text() or "" for p in reader.pages)
            elif ext == ".docx":
                doc = Document(BytesIO(raw))
                text = "\n".join(p.text for p in doc.paragraphs)
            elif ext == ".txt":
                text = raw.decode("utf-8", errors="ignore")
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        except Exception as e:
            results.append({
                "filename": up.filename,
                "error": f"Could not extract text: {e}"
            })
            continue

        # Evaluate resume
        try:
            data = evaluate_resume(client, "gpt-4", job_description, text)
            # Build summary and reasons list
            flag = "[green flag]" if data.get("verdict") == "Strong Fit" else "[red flag]"
            summary = f"{data.get('name')} - {data.get('match_score')}% match - {data.get('verdict')} {flag}"
            reasons = data.get("green_flags", []) + data.get("red_flags", [])

            results.append({
                "filename": up.filename,
                "summary": summary,
                "reasons": reasons
            })
        except Exception as e:
            results.append({
                "filename": up.filename,
                "error": str(e)
            })

    return {"results": results}
