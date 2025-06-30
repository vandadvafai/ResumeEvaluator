#!/usr/bin/env python3
# main.py

import os
import re
from io import BytesIO
from typing import List
from datetime import timedelta

from fastapi import (
    FastAPI, UploadFile, File, Form,
    Depends, HTTPException, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from PyPDF2 import PdfReader
from docx import Document
from docx.shared import RGBColor
from openai import OpenAI

from db import init_db, get_db
from auth import (
    UserCreate, create_access_token, verify_password,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES, hash_password
)
from models import User, SubscriptionPlan, UserSubscription
from resume_evaluator_api import (
    load_api_key, evaluate_resume,
    generate_interview_questions
)

# instantiate FastAPI
app = FastAPI()

# 1️⃣ initialize your database once on startup
@app.on_event("startup")
def on_startup():
    init_db()

# 2️⃣ lightweight health check
@app.get("/health")
async def health():
    return {"status": "ok"}

# 3️⃣ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://resumeyval.com",
        "https://www.resumeyval.com"
    ],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# compile suspicious-text patterns
ZERO_WIDTH = re.compile(r'[\u200B\u200C\u200D\uFEFF]')
WATERMARK  = re.compile(r'\bCONFIDENTIAL\b', re.IGNORECASE)
WHITE_PDF  = re.compile(r'1\s+1\s+1\s+(rg|RG)')

# load OpenAI client once
API_KEY = load_api_key()
client  = OpenAI(api_key=API_KEY)


# ─── AUTH ROUTES ──────────────────────────────────────────────────────────────

@app.post("/signup", status_code=201)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    # check existing
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(400, "Email already registered")

    # create user
    user = User(
        email     = user_in.email,
        hashed_pw = hash_password(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # assign free plan by default
    free_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name=="free").one()
    sub = UserSubscription(user_id=user.id, plan_id=free_plan.id)
    db.add(sub)
    db.commit()

    return {"msg": "User created and assigned free plan"}


@app.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_pw):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ─── EVALUATION ROUTE (protected) ─────────────────────────────────────────────

@app.post("/evaluate/")
async def evaluate(
    job_description: str = Form(...),
    resumes: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)   # <-- protection
):
    plan_name = current_user.subscription.plan.name
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

                raw_s = raw.decode("latin-1", errors="ignore")
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
            results.append({
                "filename": fname,
                "error": f"Extraction failed: {e}"
            })
            continue

        # 2) call OpenAI to evaluate & generate questions
        try:
            eval_data = evaluate_resume(client, "gpt-4", job_description, text)
            questions = generate_interview_questions(client, "gpt-4", job_description, text)

            summary = (
                f"{eval_data['name']} - {eval_data['match_score']}% match - "
                f"{eval_data['verdict']} [{'green flag' if eval_data['verdict']=='Strong Fit' else 'red flag'}]"
            )
            reasons = (eval_data.get("green_flags", []) + eval_data.get("red_flags", []))[:4]

            # enforce free-plan restrictions
            if plan_name == "free":
                reasons = reasons[:2]
                questions = []

            results.append({
                "filename": fname,
                "summary": summary,
                "reasons": reasons,
                "interview_questions": questions[:5],
                "suspicious_flags": suspicious_flags
            })

        except Exception as e:
            results.append({
                "filename": fname,
                "error": str(e)
            })

    return {"results": results}
