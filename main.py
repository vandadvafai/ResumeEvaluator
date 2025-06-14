#!/usr/bin/env python3
# main.py

import os
from io import BytesIO
from typing import List

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
from docx import Document
from openai import OpenAI

from resume_evaluator_api import load_api_key, evaluate_resume  # reuse helpers

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
                raise ValueError("Unsupported file type")
        except Exception as e:
            results.append({"filename": up.filename, "error": f"Extraction failed: {e}"})
            continue

        try:
            data = evaluate_resume(client, "gpt-4", job_description, text)
            flag = "[green flag]" if data["verdict"]=="Strong Fit" else "[red flag]"
            eval_str = f"{data['name']} - {data['match_score']}% match - {data['verdict']} {flag}"
            results.append({"filename": up.filename, "evaluation": eval_str})
        except Exception as e:
            results.append({"filename": up.filename, "error": str(e)})

    return {"results": results}
