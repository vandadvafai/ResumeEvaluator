# Resume Evaluator

A simple toolchain that lets you evaluate candidate resumes against a job description using OpenAI’s API. It includes:

* **`resume_evaluator_api.py`**: CLI script with reusable functions to extract text and call OpenAI.
* **`main.py`**: FastAPI backend exposing an `/evaluate/` endpoint.
* **`streamlit_app.py`**: Streamlit frontend UI to paste a job description and upload resumes.

---

## 🚀 Features

* Supports **TXT**, **PDF**, and **DOCX** resumes.
* Calculates match score, identifies green/red flags, and outputs a one-line verdict.
* Can be used via CLI or web UI.

---

## 📋 Prerequisites

* Python 3.8+
* OpenAI API key

---

## 🛠 Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/your-org/ResumeEvaluator.git
   cd resume-evaluator
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root:

   ```ini
   OPENAI_API_KEY=your_openai_api_key_here
   ```

---

## ⚙️ Configuration

No additional configuration needed. The `.env` file is auto-loaded to set your OpenAI key.

---

## 💻 Running the Backend

Start the FastAPI server (default port 8000):

```bash
uvicorn main:app --reload --port 8000
```

The API endpoint will be available at `http://localhost:8000/evaluate/`.

---

## 🌐 Running the Frontend

In a separate terminal, launch the Streamlit app:

```bash
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser.

---

## 📝 Usage

1. **Paste** your full job description into the text area.
2. **Upload** one or more resumes (`.txt`, `.pdf`, `.docx`).
3. **Click** Evaluate.
4. **View** one-line verdicts and download individual evaluations.

---

## 🗂️ File Structure

```
Resume_Evaluator/
├── .env                 # contains OPENAI_API_KEY
├── requirements.txt     # Python dependencies
├── resume_evaluator_api.py  # core evaluator CLI
├── main.py              # FastAPI backend
├── streamlit_app.py     # Streamlit frontend
└── README.md            # this file
```

---

## 📄 License

MIT © Group 6/ IE University
