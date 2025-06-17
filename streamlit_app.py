import streamlit as st
import requests

API_URL = "http://localhost:8000/evaluate/"

def main():
    st.set_page_config(page_title="Resume Evaluator", layout="wide")
    st.title("📄 Resume Evaluator")
    st.write("Paste the job description below and upload one or more resumes (PDF, DOCX, or TXT).")

    # Job description input
    job_input = st.text_area("📝 Job Description", height=250)

    # File uploader
    uploaded = st.file_uploader(
        "📂 Upload Resumes",
        type=['pdf', 'docx', 'doc', 'txt'],
        accept_multiple_files=True
    )

    # Evaluate button
    if st.button("🔍 Evaluate Resumes"):
        if not job_input.strip():
            st.error("⚠️ Please provide the job description.")
            return
        if not uploaded:
            st.error("⚠️ Please upload at least one resume file.")
            return

        # Prepare payload
        files = [("resumes", (f.name, f.getvalue(), f.type)) for f in uploaded]
        data = {"job_description": job_input}

        # Send to backend
        with st.spinner("⏳ Evaluating, please wait..."):
            resp = requests.post(API_URL, data=data, files=files)

        if resp.status_code != 200:
            st.error(f"🚨 API error {resp.status_code}: {resp.text}")
            return

        results = resp.json().get("results", [])
        if not results:
            st.warning("No results returned from the server.")
            return

        # Display results
        for entry in results:
            st.markdown("---")
            st.subheader(entry.get("filename", "Unnamed file"))

            summary = entry.get("summary", "")
            reasons = entry.get("reasons", [])[:4]  # only first four reasons

            if summary:
                # Bold summary
                st.markdown(f"**{summary}**")

                if reasons:
                    st.markdown("**Top 4 Reasons:**")
                    for reason in reasons:
                        st.markdown(f"- {reason}")

                # Download full evaluation (summary + reasons)
                download_text = summary + "\n" + "\n".join(f"- {r}" for r in reasons)
                st.download_button(
                    label="💾 Download Full Evaluation",
                    data=download_text,
                    file_name=f"evaluation_{entry['filename']}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.error(entry.get("error", "Unknown error"))

if __name__ == "__main__":
    main()
