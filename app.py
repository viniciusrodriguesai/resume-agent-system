from __future__ import annotations
import json
import pandas as pd
import streamlit as st
from pipeline import run_pipeline
from utils.text_reader import read_text_from_upload

st.set_page_config(
    page_title="Advanced Multi-Agent Resume Analyzer",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Advanced Multi-Agent Resume and Job Analysis")
st.caption(
    "A fully local agent-based system with coordination, evidence extraction, "
    "hybrid semantic matching, review feedback, explainable scoring, and reports."
)

with st.sidebar:
    st.header("Analysis settings")
    input_mode = st.radio("Input method", ["Paste text", "Upload files"], index=0)
    strictness = st.select_slider(
        "Matching strictness",
        options=["Flexible", "Balanced", "Conservative"],
        value="Balanced",
        help="Balanced is recommended. Conservative requires stronger evidence.",
    )
    st.info("The analysis runs locally. No API key or paid AI service is required.")

resume_text = ""
job_text = ""

if input_mode == "Paste text":
    left, right = st.columns(2)
    with left:
        resume_text = st.text_area("Resume", height=330, placeholder="Paste the resume text here...")
    with right:
        job_text = st.text_area("Job description", height=330, placeholder="Paste the job description here...")
else:
    left, right = st.columns(2)
    with left:
        resume_file = st.file_uploader("Resume file", type=["pdf", "txt", "md"])
        if resume_file:
            try:
                resume_text = read_text_from_upload(resume_file, resume_file.name)
                st.success("Resume loaded.")
            except Exception as exc:
                st.error(f"Could not read the resume: {exc}")
    with right:
        job_file = st.file_uploader("Job description file", type=["pdf", "txt", "md"])
        if job_file:
            try:
                job_text = read_text_from_upload(job_file, job_file.name)
                st.success("Job description loaded.")
            except Exception as exc:
                st.error(f"Could not read the job description: {exc}")

if st.button("Run multi-agent analysis", type="primary"):
    if not resume_text.strip() or not job_text.strip():
        st.error("Provide both the resume and the job description.")
    else:
        with st.spinner("Agents are analyzing the documents..."):
            try:
                st.session_state["results"] = run_pipeline(
                    resume_text, job_text, strictness=strictness
                )
            except Exception as exc:
                st.exception(exc)

results = st.session_state.get("results")

if results:
    matching = results["matching"].data
    coordinator = results["coordinator"].data
    score = int(matching.get("overall_score", 0))
    category_scores = matching.get("category_scores", {})

    metrics = st.columns(5)
    metrics[0].metric("Overall match", f"{score}%", matching.get("level", "low").title())
    category_items = list(category_scores.items())[:3]
    for index in range(1, 4):
        if index - 1 < len(category_items):
            category, value = category_items[index - 1]
            metrics[index].metric(category, f"{value}%")
        else:
            metrics[index].metric("Category", "—")
    metrics[4].metric("Review loop", "Used" if coordinator.get("revision_performed") else "Not needed")
    st.progress(score / 100)

    tabs = st.tabs([
        "Overview", "Requirement evidence", "Resume", "Job",
        "Recommendations", "Final review", "Agent trace", "Downloads",
    ])

    with tabs[0]:
        st.subheader("Compatibility by category")
        if category_scores:
            chart = pd.DataFrame({
                "Category": list(category_scores.keys()),
                "Score": list(category_scores.values()),
            }).set_index("Category")
            st.bar_chart(chart)
        summary = st.columns(3)
        summary[0].metric("Matched", matching.get("matched_count", 0))
        summary[1].metric("Partial", matching.get("partial_count", 0))
        summary[2].metric("Missing", matching.get("missing_count", 0))
        st.write(results["matching"].summary)
        st.write(results["coordinator"].summary)

    with tabs[1]:
        rows = [{
            "Requirement": item.get("label"),
            "Priority": item.get("priority"),
            "Category": item.get("category"),
            "Status": item.get("status"),
            "Similarity": item.get("similarity"),
            "Resume evidence": item.get("evidence") or "No evidence identified",
        } for item in matching.get("matches", [])]
        frame = pd.DataFrame(rows)
        if not frame.empty:
            selected = st.multiselect(
                "Filter by status",
                ["matched", "partial", "missing"],
                default=["matched", "partial", "missing"],
            )
            st.dataframe(frame[frame["Status"].isin(selected)], use_container_width=True, hide_index=True)
        else:
            st.warning("No requirements were identified.")

    with tabs[2]:
        st.subheader("Resume Agent")
        st.write(results["resume"].summary)
        st.json({
            "name": results["resume"].data.get("name"),
            "contact": results["resume"].data.get("contact"),
            "skills": list(results["resume"].data.get("skills", {}).keys()),
            "education": results["resume"].data.get("education"),
            "experience": results["resume"].data.get("experience"),
            "projects": results["resume"].data.get("projects"),
            "warnings": results["resume"].warnings,
        })

    with tabs[3]:
        st.subheader("Job Agent")
        st.write(results["job"].summary)
        frame = pd.DataFrame(results["job"].data.get("requirements", []))
        if not frame.empty:
            columns = [c for c in ["label", "priority", "type", "category", "source_line"] if c in frame.columns]
            st.dataframe(frame[columns], use_container_width=True, hide_index=True)

    with tabs[4]:
        st.subheader("Prioritized recommendations")
        frame = pd.DataFrame(results["recommendation"].data.get("recommendations", []))
        if not frame.empty:
            st.dataframe(frame, use_container_width=True, hide_index=True)

    with tabs[5]:
        st.subheader("Review Agent")
        decision = results["review"].data.get("decision")
        message = results["review"].data.get("final_answer")
        st.success(message) if decision == "approved" else st.warning(message)
        for issue in results["review"].data.get("issues", []):
            st.write(f"- {issue}")
        st.caption("This result supports human evaluation and must not replace it.")

    with tabs[6]:
        trace = pd.DataFrame(results["coordinator"].data.get("trace", []))
        st.dataframe(trace, use_container_width=True, hide_index=True)
        st.write(f"Total workflow time: {results['coordinator'].data.get('total_elapsed_ms', 0):.2f} ms")

    with tabs[7]:
        markdown_report = results["report"].data.get("markdown_report", "")
        json_report = results["report"].data.get("json_report", json.dumps({}, indent=2))
        st.download_button(
            "Download Markdown report",
            data=markdown_report,
            file_name="resume_analysis_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.download_button(
            "Download JSON data",
            data=json_report,
            file_name="resume_analysis_data.json",
            mime="application/json",
            use_container_width=True,
        )
        st.subheader("Report preview")
        st.markdown(markdown_report)
