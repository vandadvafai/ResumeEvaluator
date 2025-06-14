import streamlit as st
import requests

API_URL = "http://localhost:8000/evaluate/"

def main():
    st.title("Resume Evaluator Frontend")
    st.markdown("Paste the job description below and upload your resumes.")

    job_input = st.text_area("Job Description", height=200)
    uploaded = st.file_uploader(
        "Upload Resumes (PDF, DOCX, TXT)",
        type=['pdf','docx','doc','txt'],
        accept_multiple_files=True
    )

    if st.button("Evaluate"):
        if not job_input.strip():
            st.error("Please provide the job description.")
            return
        if not uploaded:
            st.error("Please upload at least one resume file.")
            return

        files = [("resumes", (f.name, f.getvalue(), f.type)) for f in uploaded]
        data = {"job_description": job_input}

        with st.spinner("Contacting backend…"):
            resp = requests.post(API_URL, data=data, files=files)

        if resp.status_code != 200:
            st.error(f"API error {resp.status_code}: {resp.text}")
            return

        for entry in resp.json().get("results", []):
            st.subheader(entry["filename"])
            if entry.get("evaluation"):
                st.text(entry["evaluation"])
                st.download_button(
                    "Download ⇩",
                    entry["evaluation"],
                    file_name=f"eval_{entry['filename']}.txt",
                    mime="text/plain"
                )
            else:
                st.error(entry.get("error", "Unknown error"))

if __name__ == "__main__":
    main()
