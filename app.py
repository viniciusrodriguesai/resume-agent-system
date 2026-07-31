from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from resume_ai.analyzer import MultiAgentAnalyzer
from resume_ai.config import Settings
from resume_ai.documents import DocumentParser


st.set_page_config(
    page_title="Professional Multi-Agent Resume AI",
    page_icon="🧠",
    layout="wide",
)

@st.cache_resource(show_spinner="Loading local AI resources...")
def get_analyzer(full_ai: bool) -> MultiAgentAnalyzer:
    return MultiAgentAnalyzer(
        settings=Settings(),
        full_ai=full_ai,
        persist_history=True,
    )

@st.cache_resource
def get_parser() -> DocumentParser:
    return DocumentParser(Settings())


def read_upload(uploaded_file) -> tuple[str, dict]:
    return get_parser().parse_bytes(
        uploaded_file.getvalue(),
        uploaded_file.name,
    )


st.title("🧠 Professional Multi-Agent Resume AI")
st.caption(
    "Local, multilingual, explainable resume-to-job matching with privacy "
    "redaction, LangGraph orchestration, semantic retrieval, reranking, "
    "self-review, SQLite history, and evaluation support."
)

with st.sidebar:
    st.header("Execution")
    full_ai = st.toggle(
        "Full local AI",
        value=True,
        help=(
            "Uses Sentence Transformers and CrossEncoder when installed. "
            "If unavailable, the app automatically falls back to lexical similarity."
        ),
    )
    strictness = st.select_slider(
        "Matching strictness",
        options=["Flexible", "Balanced", "Conservative"],
        value="Balanced",
    )
    input_mode = st.radio(
        "Input method",
        ["Paste text", "Upload files"],
    )
    st.divider()
    st.markdown(
        "**Privacy:** direct identifiers are removed before matching. "
        "The original resume remains visible only in the current app session."
    )

resume_text = ""
job_text = ""
parser_details = {}

if input_mode == "Paste text":
    left, right = st.columns(2)
    with left:
        resume_text = st.text_area(
            "Resume",
            height=360,
            placeholder="Paste the resume text here...",
        )
    with right:
        job_text = st.text_area(
            "Job description",
            height=360,
            placeholder="Paste the job description here...",
        )
else:
    left, right = st.columns(2)
    with left:
        resume_file = st.file_uploader(
            "Resume",
            type=["pdf", "docx", "txt", "md"],
            key="resume_file",
        )
        if resume_file:
            try:
                resume_text, resume_parser = read_upload(resume_file)
                parser_details["resume"] = resume_parser
                st.success(
                    f"Resume parsed with {resume_parser.get('engine')}."
                )
            except Exception as exc:
                st.error(f"Resume parsing failed: {exc}")
    with right:
        job_file = st.file_uploader(
            "Job description",
            type=["pdf", "docx", "txt", "md"],
            key="job_file",
        )
        if job_file:
            try:
                job_text, job_parser = read_upload(job_file)
                parser_details["job"] = job_parser
                st.success(
                    f"Job parsed with {job_parser.get('engine')}."
                )
            except Exception as exc:
                st.error(f"Job parsing failed: {exc}")

run_analysis = st.button(
    "Run professional multi-agent analysis",
    type="primary",
    use_container_width=True,
)

if run_analysis:
    if not resume_text.strip() or not job_text.strip():
        st.error("Provide both the resume and the job description.")
    else:
        try:
            with st.spinner(
                "Running privacy, structuring, retrieval, reranking, scoring, "
                "review, recommendation, and reporting agents..."
            ):
                analyzer = get_analyzer(full_ai)
                result = analyzer.run(
                    resume_text,
                    job_text,
                    strictness=strictness,
                )
                result["parser_details"] = parser_details
                st.session_state["analysis_result"] = result
        except Exception as exc:
            st.exception(exc)

result = st.session_state.get("analysis_result")

if result:
    scoring = result["scoring"]
    status = result.get("engine_status", {})
    review = result.get("review", {})

    top = st.columns(6)
    top[0].metric(
        "Overall",
        f"{scoring['overall_score']}%",
        scoring["level"].title(),
    )
    top[1].metric("Matched", scoring["matched_count"])
    top[2].metric("Partial", scoring["partial_count"])
    top[3].metric("Missing", scoring["missing_count"])
    top[4].metric(
        "Graph",
        "LangGraph" if status.get("langgraph_available") else "Fallback",
    )
    top[5].metric(
        "AI engine",
        (
            "Embeddings + reranker"
            if status.get("reranker_available")
            else "Embeddings"
            if status.get("embedding_available")
            else "Lexical fallback"
        ),
    )
    st.progress(scoring["overall_score"] / 100)

    tabs = st.tabs(
        [
            "Dashboard",
            "Evidence",
            "Profiles",
            "Privacy",
            "Recommendations",
            "Review",
            "Agent graph",
            "Reports",
            "History",
        ]
    )

    with tabs[0]:
        st.subheader("Scores by requirement type")
        category_scores = scoring.get("category_scores", {})
        if category_scores:
            chart = pd.DataFrame(
                {
                    "Category": list(category_scores.keys()),
                    "Score": list(category_scores.values()),
                }
            ).set_index("Category")
            st.bar_chart(chart)

        st.subheader("System diagnostics")
        diagnostic_rows = [
            {"Component": "Embedding model", "Active": status.get("embedding_available"), "Detail": status.get("embedding_model")},
            {"Component": "CrossEncoder reranker", "Active": status.get("reranker_available"), "Detail": status.get("reranker_model")},
            {"Component": "LangGraph", "Active": status.get("langgraph_available"), "Detail": "Stateful conditional workflow"},
            {"Component": "Skill catalog", "Active": True, "Detail": f"{status.get('catalog_size', 0)} local skills"},
        ]
        st.dataframe(
            pd.DataFrame(diagnostic_rows),
            hide_index=True,
            use_container_width=True,
        )
        if status.get("embedding_error") and full_ai:
            st.warning(
                "Embedding model unavailable; lexical fallback was used. "
                f"Technical detail: {status['embedding_error']}"
            )
        if status.get("reranker_error") and full_ai:
            st.warning(
                "Reranker unavailable; first-stage retrieval was used. "
                f"Technical detail: {status['reranker_error']}"
            )

    with tabs[1]:
        rows = []
        for item in scoring.get("evidence", []):
            rows.append(
                {
                    "Requirement": item.get("label"),
                    "Type": item.get("type"),
                    "Priority": item.get("priority"),
                    "Status": item.get("status"),
                    "Score": item.get("final_score"),
                    "Best resume evidence": item.get("best_evidence") or "No evidence identified",
                    "Engine": item.get("engine"),
                }
            )
        frame = pd.DataFrame(rows)
        if not frame.empty:
            selected_statuses = st.multiselect(
                "Status filter",
                ["matched", "partial", "missing"],
                default=["matched", "partial", "missing"],
            )
            filtered = frame[frame["Status"].isin(selected_statuses)]
            st.dataframe(
                filtered,
                hide_index=True,
                use_container_width=True,
            )
            st.download_button(
                "Download evidence CSV",
                filtered.to_csv(index=False).encode("utf-8"),
                file_name="requirement_evidence.csv",
                mime="text/csv",
            )

        with st.expander("Top candidates for each requirement"):
            for item in scoring.get("evidence", []):
                st.markdown(f"### {item.get('label')}")
                candidates = pd.DataFrame(item.get("top_candidates", []))
                if not candidates.empty:
                    columns = [
                        col for col in [
                            "text", "retrieval_score", "reranker_score",
                            "final_score", "engine", "exact_alias_match",
                        ] if col in candidates.columns
                    ]
                    st.dataframe(
                        candidates[columns],
                        hide_index=True,
                        use_container_width=True,
                    )

    with tabs[2]:
        left, right = st.columns(2)
        with left:
            st.subheader("Resume profile")
            st.json(
                {
                    "skills": result["resume_profile"].get("skill_labels"),
                    "education": result["resume_profile"].get("education"),
                    "experience": result["resume_profile"].get("experience"),
                    "quantified_evidence": result["resume_profile"].get("quantified_evidence"),
                }
            )
        with right:
            st.subheader("Job profile")
            requirements = pd.DataFrame(
                result["job_profile"].get("requirements", [])
            )
            if not requirements.empty:
                columns = [
                    col for col in [
                        "label", "type", "priority", "source", "uri",
                    ] if col in requirements.columns
                ]
                st.dataframe(
                    requirements[columns],
                    hide_index=True,
                    use_container_width=True,
                )

    with tabs[3]:
        st.subheader("Privacy and fairness preprocessing")
        st.json(result.get("privacy_report", {}))
        st.caption(
            "Names, direct contact details, selected personal URLs, and selected "
            "sensitive personal lines are excluded from matching."
        )
        with st.expander("View anonymized resume used by the agents"):
            st.code(result.get("anonymized_resume_text", ""))

    with tabs[4]:
        st.subheader("Truthful, prioritized recommendations")
        recommendations = pd.DataFrame(
            result.get("recommendations", [])
        )
        if not recommendations.empty:
            st.dataframe(
                recommendations,
                hide_index=True,
                use_container_width=True,
            )

    with tabs[5]:
        decision = review.get("decision")
        if decision == "approved":
            st.success(review.get("summary"))
        else:
            st.warning(review.get("summary"))
        st.write(
            f"Revision passes performed: {result.get('revision_count', 0)}"
        )
        st.info(
            "The score is decision support only. A human should review the "
            "candidate, evidence, accommodations, and context."
        )

    with tabs[6]:
        st.subheader("Agent execution trace")
        trace = pd.DataFrame(result.get("trace", []))
        if not trace.empty:
            st.dataframe(
                trace,
                hide_index=True,
                use_container_width=True,
            )
        st.code(
            """START
  ↓
Privacy and Fairness Agent
  ↓
Resume Structurer Agent
  ↓
Job Structurer Agent
  ↓
Semantic Retriever + CrossEncoder Reranker
  ↓
Explainable Scoring Agent
  ↓
Review Agent ── revise ──┐
  │                       │
  └── approve             └── back to retrieval
          ↓
Recommendation Agent
          ↓
Report Agent
          ↓
END"""
        )

    with tabs[7]:
        markdown_report = result.get("report_markdown", "")
        json_report = result.get("report_json", json.dumps({}, indent=2))
        left, right = st.columns(2)
        with left:
            st.download_button(
                "Download Markdown report",
                markdown_report,
                file_name="resume_analysis_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with right:
            st.download_button(
                "Download JSON report",
                json_report,
                file_name="resume_analysis_report.json",
                mime="application/json",
                use_container_width=True,
            )
        st.markdown(markdown_report)

    with tabs[8]:
        analyzer = get_analyzer(full_ai)
        history = pd.DataFrame(analyzer.history.list_recent(30))
        if not history.empty:
            st.dataframe(
                history,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No saved analyses yet.")
