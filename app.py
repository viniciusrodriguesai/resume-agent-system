import pandas as pd
import streamlit as st

from pipeline import run_pipeline
from utils.text_reader import read_text_from_upload

st.set_page_config(
    page_title="Multi-Agent Resume Analyzer",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Multi-Agent Resume and Job Analysis System")
st.write(
    "A final project about agent-based programming in which specialized agents "
    "cooperate to compare a resume with a job description."
)

with st.sidebar:
    st.header("Input")
    input_mode = st.radio(
        "How would you like to provide the data?",
        ["Paste text", "Upload files"],
        index=0,
    )

resume_text = ""
job_text = ""

if input_mode == "Paste text":
    col1, col2 = st.columns(2)
    with col1:
        resume_text = st.text_area(
            "Resume",
            height=330,
            placeholder="Paste the resume text here...",
        )
    with col2:
        job_text = st.text_area(
            "Job description",
            height=330,
            placeholder="Paste the job description here...",
        )
else:
    col1, col2 = st.columns(2)
    with col1:
        resume_file = st.file_uploader(
            "Resume in PDF, TXT, or MD format",
            type=["pdf", "txt", "md"],
        )
        if resume_file:
            resume_text = read_text_from_upload(resume_file, resume_file.name)
            st.success("Resume loaded successfully.")
    with col2:
        job_file = st.file_uploader(
            "Job description in PDF, TXT, or MD format",
            type=["pdf", "txt", "md"],
        )
        if job_file:
            job_text = read_text_from_upload(job_file, job_file.name)
            st.success("Job description loaded successfully.")

if st.button("Run agents", type="primary"):
    if not resume_text.strip() or not job_text.strip():
        st.error("Provide both the resume and the job description.")
    else:
        results = run_pipeline(resume_text, job_text)

        score = results["matching"].data["score"]
        st.metric(
            "Compatibility",
            f"{score}%",
            results["matching"].data["level"].title(),
        )
        st.progress(score / 100)

        tabs = st.tabs(
            [
                "Resume",
                "Job",
                "Comparison",
                "Recommendations",
                "Final Response",
                "Agent Trace",
            ]
        )

        with tabs[0]:
            st.subheader("Resume Agent")
            st.write(results["resume"].summary)
            st.json(results["resume"].data)

        with tabs[1]:
            st.subheader("Job Agent")
            st.write(results["job"].summary)
            st.json(results["job"].data)

        with tabs[2]:
            st.subheader("Matching Agent")
            data = results["matching"].data
            comparison = pd.DataFrame(
                {
                    "Category": [
                        "Matched required skills",
                        "Missing required skills",
                        "Matched desirable skills",
                        "Missing desirable skills",
                    ],
                    "Skills": [
                        ", ".join(data["matched_required"]) or "—",
                        ", ".join(data["missing_required"]) or "—",
                        ", ".join(data["matched_desirable"]) or "—",
                        ", ".join(data["missing_desirable"]) or "—",
                    ],
                }
            )
            st.dataframe(comparison, use_container_width=True)

        with tabs[3]:
            st.subheader("Recommendation Agent")
            for item in results["recommendation"].data["recommendations"]:
                st.write("- " + item)

        with tabs[4]:
            st.subheader("Review Agent")
            st.text(results["review"].data["final_answer"])

        with tabs[5]:
            st.subheader("Execution trace")
            trace = []
            for stage, result in results.items():
                trace.append(
                    {
                        "stage": stage,
                        "agent": result.agent_name,
                        "summary": result.summary,
                    }
                )
            st.dataframe(pd.DataFrame(trace), use_container_width=True)
