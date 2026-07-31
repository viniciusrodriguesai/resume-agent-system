from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest, AnalysisResult
from resume_ai.infrastructure.documents import DocumentReader
from resume_ai.presentation.auth import enforce_optional_oidc
from resume_ai.presentation.charts import agent_timing_chart, category_chart, status_chart
from resume_ai.settings import Settings

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / "examples"

st.set_page_config(
    page_title="Resume Match AI V5",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css() -> None:
    css_file = ROOT / "assets" / "styles.css"
    if css_file.exists():
        st.markdown(f"<style>{css_file.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Carregando os agentes e o motor local...")
def get_service(profile: str) -> ResumeAnalysisService:
    return ResumeAnalysisService(Settings.for_profile(profile))  # type: ignore[arg-type]


@st.cache_resource(show_spinner=False)
def get_reader(profile: str) -> DocumentReader:
    return DocumentReader(Settings.for_profile(profile))  # type: ignore[arg-type]


def load_example() -> None:
    st.session_state["resume_text"] = (EXAMPLES / "curriculo_exemplo.txt").read_text(encoding="utf-8")
    st.session_state["job_text"] = (EXAMPLES / "vaga_exemplo.txt").read_text(encoding="utf-8")


def score_ring(score: int, level: str) -> None:
    degrees = score * 3.6
    st.markdown(f"""
    <div class="score-panel">
      <div class="score-ring" style="background:conic-gradient(#5b5bd6 {degrees}deg,#e7e8ef 0deg)">
        <div class="score-inner"><strong>{score}%</strong><span>compatibilidade</span></div>
      </div>
      <div><span class="chip">Nível {html.escape(level)}</span><h2>Análise explicável e local</h2><p>A nota combina prioridade, evidência lexical, semântica e revisão determinística.</p></div>
    </div>
    """, unsafe_allow_html=True)


def render_result(result: AnalysisResult, service: ResumeAnalysisService) -> None:
    score_ring(result.score.overall_score, result.score.level)
    cols = st.columns(5)
    values = [
        ("Atendidos", result.score.matched),
        ("Parciais", result.score.partial),
        ("Ausentes", result.score.missing),
        ("Obrigatórios ausentes", result.score.required_missing),
        ("Tempo total", f"{result.timings_ms.get('total', 0)/1000:.2f}s"),
    ]
    for column, (label, value) in zip(cols, values):
        column.metric(label, value)

    tabs = st.tabs(["Visão geral", "Evidências", "Recomendações", "Privacidade", "Agentes", "Exportar"])
    with tabs[0]:
        col1, col2 = st.columns(2)
        col1.plotly_chart(category_chart(result), use_container_width=True)
        col2.plotly_chart(status_chart(result), use_container_width=True)
        st.info(result.review_summary)
        for explanation in result.score.explanation:
            st.markdown(f"- {explanation}")

    with tabs[1]:
        status_filter = st.multiselect("Filtrar status", ["matched", "partial", "missing"], default=["matched", "partial", "missing"])
        for match in result.matches:
            if match.status not in status_filter:
                continue
            with st.expander(f"{match.status.upper()} · {match.requirement.text} · {match.final_score:.2f}"):
                st.write(match.evidence or "Nenhuma evidência encontrada.")
                st.caption(match.explanation)
                st.dataframe(pd.DataFrame([item.model_dump() for item in match.top_candidates]), use_container_width=True, hide_index=True)

    with tabs[2]:
        for item in result.recommendations:
            st.markdown(f"**{item.priority.upper()} · {item.category}**")
            st.write(item.action)

    with tabs[3]:
        st.success(f"{result.privacy.total_removed} dado(s) pessoal(is) removido(s) antes do processamento semântico.")
        st.json(result.privacy.model_dump())
        st.caption("O histórico local guarda somente metadados, pontuação e tempos; não guarda currículo ou vaga.")

    with tabs[4]:
        st.plotly_chart(agent_timing_chart(result), use_container_width=True)
        st.dataframe(pd.DataFrame([trace.model_dump() for trace in result.traces]), use_container_width=True, hide_index=True)
        st.json(result.engine_status)

    with tabs[5]:
        st.download_button("Baixar Markdown", result.markdown_report, file_name=f"analise-{result.analysis_id}.md", mime="text/markdown")
        st.download_button("Baixar JSON", service.to_json(result), file_name=f"analise-{result.analysis_id}.json", mime="application/json")
        st.download_button("Baixar CSV", service.to_csv(result), file_name=f"analise-{result.analysis_id}.csv", mime="text/csv")


def main() -> None:
    inject_css()
    enforce_optional_oidc(Settings())
    st.markdown("""
    <div class="hero">
      <div><span class="eyebrow">V5 · LOCAL · OPEN SOURCE</span><h1>Resume Match AI</h1><p>Plataforma multiagente para comparar currículos e vagas com evidências, privacidade e explicabilidade.</p></div>
      <div class="hero-badges"><span>CPU friendly</span><span>API FastAPI</span><span>Fallback offline</span></div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("Configuração")
        profile_label = st.radio("Perfil de execução", ["⚡ Demonstração", "⚖️ Equilibrado", "🧠 Completo"], index=0)
        profile = {"⚡ Demonstração": "demo", "⚖️ Equilibrado": "balanced", "🧠 Completo": "complete"}[profile_label]
        strictness = st.select_slider("Rigor", options=["flexível", "equilibrado", "conservador"], value="equilibrado")
        st.caption("Para seu notebook, use Demonstração ao vivo. O modo Completo exige mais RAM.")
        if st.button("Carregar exemplo", use_container_width=True):
            load_example()
            st.rerun()
        if st.button("Limpar sessão", use_container_width=True):
            st.session_state.clear()
            st.cache_data.clear()
            st.rerun()

    input_mode = st.segmented_control("Forma de entrada", ["Colar textos", "Enviar arquivos"], default="Colar textos")
    resume_text = st.session_state.get("resume_text", "")
    job_text = st.session_state.get("job_text", "")

    with st.form("analysis_form"):
        if input_mode == "Colar textos":
            left, right = st.columns(2)
            resume_text = left.text_area("Currículo", value=resume_text, height=390, key="resume_text_input")
            job_text = right.text_area("Descrição da vaga", value=job_text, height=390, key="job_text_input")
        else:
            left, right = st.columns(2)
            resume_file = left.file_uploader("Currículo", type=["pdf", "docx", "txt"])
            job_file = right.file_uploader("Vaga", type=["pdf", "docx", "txt"])
            if resume_file and job_file:
                reader = get_reader(profile)
                try:
                    resume_text = reader.read_upload(resume_file.name, resume_file.getvalue())
                    job_text = reader.read_upload(job_file.name, job_file.getvalue())
                    st.success("Arquivos validados e texto extraído.")
                except Exception as exc:
                    st.error(str(exc))
        consent = st.checkbox("Entendo que o resultado apoia revisão humana e não toma decisão de contratação.")
        submitted = st.form_submit_button("Executar análise multiagente", use_container_width=True, type="primary")

    if submitted:
        if not consent:
            st.error("Confirme o aviso de uso responsável.")
        elif len(resume_text.strip()) < 10 or len(job_text.strip()) < 10:
            st.error("Informe currículo e vaga com conteúdo suficiente.")
        else:
            service = get_service(profile)
            request = AnalysisRequest(resume_text=resume_text, job_text=job_text, profile=profile, strictness=strictness)
            with st.status("Executando pipeline local...", expanded=True) as status:
                st.write("1. Removendo dados pessoais")
                st.write("2. Estruturando currículo e vaga")
                st.write("3. Recuperando evidências")
                st.write("4. Calculando pontuação e revisão")
                result = service.analyze(request)
                status.update(label="Análise concluída", state="complete", expanded=False)
            st.session_state["last_result"] = result.model_dump(mode="json")

    if "last_result" in st.session_state:
        result = AnalysisResult.model_validate(st.session_state["last_result"])
        render_result(result, get_service(result.profile))


if __name__ == "__main__":
    main()
