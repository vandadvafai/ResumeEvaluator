# streamlit_app.py
import streamlit as st
import requests

API_URL = "http://localhost:8000/evaluate/"

st.set_page_config(page_title="Resume Evaluator", layout="wide")

def main():
    st.markdown("<h1 style='text-align:center;'>📄 Resume Evaluator</h1>", unsafe_allow_html=True)
    st.markdown("#### Analyze resumes against job descriptions with AI-powered insights.")
    st.markdown("---")

    mode = st.radio("Choose Input Mode:", ["🧾 Simple", "⚙️ Advanced"], horizontal=True)
    job_description = ""

    if mode == "🧾 Simple":
        st.markdown("#### 📝 Paste Job Description")
        job_description = st.text_area("", height=200, placeholder="Paste the full job description here...")
    else:
        st.markdown("#### ⚙️ Fill Advanced Job Information")
        col1, col2 = st.columns(2, gap="large")
        with col1:
            title       = st.text_input("Job Title")
            visa_status = st.text_input("Visa / Residency Status")
            location    = st.text_input("Job Location")
        with col2:
            description = st.text_area("Job Description", height=120)
            salary      = st.text_input("Estimated Salary")

        st.markdown("##### 📋 Requirements & Qualifications")
        col3, col4 = st.columns(2, gap="large")
        with col3:
            requirements = st.text_area("Candidate Requirements", height=100)
        with col4:
            min_qualifications = st.text_area("Minimum Qualifications", height=100)
        adv_qualifications = st.text_area("Advanced Qualifications (Optional)", height=100)

        parts = []
        if title:            parts.append(f"Job Title: {title}")
        if location:         parts.append(f"Location: {location}")
        if visa_status:      parts.append(f"Visa / Residency Status: {visa_status}")
        if salary:           parts.append(f"Estimated Salary: {salary}")
        if description:      parts.append(f"Job Description:\n{description}")
        if requirements:     parts.append(f"Candidate Requirements:\n{requirements}")
        if min_qualifications:
                             parts.append(f"Minimum Qualifications:\n{min_qualifications}")
        if adv_qualifications:
                             parts.append(f"Advanced Qualifications:\n{adv_qualifications}")

        job_description = "\n\n".join(parts)

    st.markdown("---")
    uploaded = st.file_uploader("📂 Upload One or More Resumes", type=["pdf","docx","txt"], accept_multiple_files=True)

    if st.button("🔍 Evaluate Resumes"):
        if not job_description.strip():
            st.error("⚠️ Please provide the job description or advanced details.")
            return
        if not uploaded:
            st.error("⚠️ Please upload at least one resume.")
            return

        files = [("resumes",(f.name, f.getvalue(), f.type)) for f in uploaded]
        data  = {"job_description": job_description}

        with st.spinner("⏳ Evaluating resumes..."):
            resp = requests.post(API_URL, data=data, files=files)

        if resp.status_code != 200:
            st.error(f"🚨 API error {resp.status_code}: {resp.text}")
            return

        results = resp.json().get("results", [])
        if not results:
            st.warning("⚠️ No results returned.")
            return

        st.success("✅ Evaluation complete!")
        st.markdown("### 🔎 Results")

        for entry in results:
            st.markdown("---")
            st.markdown(f"#### 📁 {entry.get('filename','')}")

            if entry.get("error"):
                st.error(f"❌ {entry['error']}")
                continue

            for flag in entry.get("suspicious_flags", []):
                st.warning(f"⚠️ {flag}")

            st.markdown(f"**Summary:** {entry['summary']}")

            if entry.get("reasons"):
                st.markdown("**Top Reasons:**")
                for r in entry["reasons"]:
                    st.markdown(f"- {r}")

            if entry.get("interview_questions"):
                st.markdown("**Download tailored interview questions!**")

            if entry.get("interview_questions"):
                qtxt = "\n".join(entry["interview_questions"])
                st.download_button("💾 Download Interview Questions", qtxt,
                                   file_name=f"questions_{entry['filename']}.txt", mime="text/plain")

if __name__ == "__main__":
    main()
