from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Literal, cast

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from resume_ai.application.analyze_resume import ResumeAnalysisService
from resume_ai.domain.models import AnalysisRequest, AnalysisResult
from resume_ai.infrastructure.documents import DocumentReader
from resume_ai.presentation.auth import enforce_optional_oidc
from resume_ai.presentation.charts import agent_timing_chart, category_chart, status_chart
from resume_ai.settings import Settings

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / "examples"
APP_VERSION = "6.0.0"

STATUS_LABELS = {
    "matched": "Correspondido",
    "partial": "Parcial",
    "missing": "Ausente",
}
STATUS_VALUES = {label: value for value, label in STATUS_LABELS.items()}
PRIORITY_LABELS = {
    "required": "Obrigatório",
    "desired": "Desejável",
    "neutral": "Neutro",
}
ENTITY_LABELS = {
    "EMAIL": "E-mail",
    "TELEFONE": "Telefone",
    "NOME_CANDIDATO": "Nome",
    "CPF": "CPF",
    "CNPJ": "CNPJ",
    "CEP": "CEP",
    "URL": "URL",
}

st.set_page_config(
    page_title="Resume Match AI V6.0.0",
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
    st.session_state["resume_text"] = (EXAMPLES / "sample_resume.txt").read_text(encoding="utf-8")
    st.session_state["job_text"] = (EXAMPLES / "vaga_exemplo.txt").read_text(encoding="utf-8")


def format_duration(duration_ms: float) -> str:
    if duration_ms >= 1000:
        return f"{duration_ms / 1000:.2f} s".replace(".", ",")
    if duration_ms >= 10:
        return f"{duration_ms:.0f} ms"
    return f"{duration_ms:.2f} ms".replace(".", ",")


def compatibility_label(score: int) -> str:
    if score >= 90:
        return "Compatibilidade excelente"
    if score >= 75:
        return "Alta compatibilidade"
    if score >= 60:
        return "Boa compatibilidade"
    if score >= 40:
        return "Compatibilidade moderada"
    return "Baixa compatibilidade"


def score_ring(score: int) -> None:
    degrees = score * 3.6
    label = compatibility_label(score)
    st.markdown(
        f"""
        <div class="score-panel">
          <div class="score-ring" style="background:conic-gradient(#5b5bd6 {degrees}deg,#e7e8ef 0deg)">
            <div class="score-inner"><strong>{score}%</strong><span>compatibilidade</span></div>
          </div>
          <div class="score-copy">
            <span class="chip">{html.escape(label)}</span>
            <h2>Análise explicável e local</h2>
            <p>A nota considera prioridade, evidência lexical, similaridade semântica e cobertura das competências exigidas.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def concise_requirement(text: str, max_chars: int = 54) -> str:
    cleaned = text.strip().rstrip(".;:")
    prefixes = (
        "experiência com ",
        "experiencia com ",
        "conhecimento de ",
        "conhecimento em ",
        "familiaridade com ",
        "domínio de ",
        "dominio de ",
        "capacidade de ",
    )
    lowered = cleaned.casefold()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            break
    if len(cleaned) > max_chars:
        return cleaned[: max_chars - 1].rstrip() + "…"
    return cleaned


def top_requirement_labels(result: AnalysisResult, status: str, *, priority: str | None = None, limit: int = 4) -> list[str]:
    candidates = [
        match
        for match in result.matches
        if match.status == status and (priority is None or match.requirement.priority == priority)
    ]
    candidates.sort(key=lambda item: item.final_score, reverse=status != "missing")
    labels: list[str] = []
    for match in candidates:
        label = concise_requirement(match.requirement.text)
        if label and label not in labels:
            labels.append(label)
        if len(labels) == limit:
            break
    return labels


def render_result_summary(result: AnalysisResult) -> None:
    score = result.score.overall_score
    desired_missing = result.score.desired_missing
    required_missing = result.score.required_missing

    if required_missing == 0:
        st.success("Todos os requisitos obrigatórios possuem alguma evidência no currículo.")
    else:
        st.warning(
            f"{required_missing} requisito(s) obrigatório(s) não possuem evidência suficiente e precisam de revisão."
        )

    if score >= 75:
        opening = "O currículo apresenta alta compatibilidade com a vaga."
    elif score >= 60:
        opening = "O currículo apresenta boa compatibilidade com a vaga."
    elif score >= 40:
        opening = "O currículo apresenta compatibilidade moderada com a vaga."
    else:
        opening = "O currículo apresenta baixa compatibilidade com a vaga."

    if desired_missing:
        detail = f"As principais oportunidades de melhoria estão em {desired_missing} requisito(s) desejável(is) ainda ausente(s)."
    elif required_missing == 0:
        detail = "Não foram identificadas lacunas obrigatórias ou desejáveis totalmente ausentes."
    else:
        detail = "Priorize primeiro os requisitos obrigatórios sem evidência."
    st.info(f"{opening} {detail}")

    strengths = top_requirement_labels(result, "matched", limit=4)
    gaps = top_requirement_labels(result, "missing", priority="desired", limit=4)
    if not gaps:
        gaps = top_requirement_labels(result, "missing", limit=4)

    left, right = st.columns(2)
    strengths_text = " · ".join(html.escape(item) for item in strengths) or "Nenhum ponto forte destacado ainda."
    gaps_text = " · ".join(html.escape(item) for item in gaps) or "Nenhuma lacuna principal identificada."
    left.markdown(
        f'<div class="insight-card strength-card"><span>Pontos fortes</span><strong>{strengths_text}</strong></div>',
        unsafe_allow_html=True,
    )
    right.markdown(
        f'<div class="insight-card gap-card"><span>Lacunas principais</span><strong>{gaps_text}</strong></div>',
        unsafe_allow_html=True,
    )


def candidate_frame(match: Any) -> pd.DataFrame:
    rows = []
    for item in match.top_candidates:
        rows.append({
            "Evidência": item.text,
            "Lexical": item.lexical_score,
            "Aproximada": item.fuzzy_score,
            "Semântica": item.semantic_score,
            "Reranker": item.reranker_score,
            "Final": item.final_score,
            "Método": item.retrieval_method,
        })
    return pd.DataFrame(rows)


def render_privacy(result: AnalysisResult) -> None:
    st.success(
        f"{result.privacy.total_removed} identificador(es) pessoal(is) foram removidos antes dos embeddings."
    )
    columns = st.columns(4)
    columns[0].metric("Identificadores removidos", result.privacy.total_removed)
    columns[1].metric("Currículo bruto armazenado", "Não" if not result.privacy.raw_document_stored else "Sim")
    columns[2].metric(
        "Texto anonimizado armazenado",
        "Não" if not result.privacy.anonymized_document_stored else "Sim",
    )
    columns[3].metric("Método", "Local")

    if result.privacy.entities:
        rows = [
            {
                "Tipo": ENTITY_LABELS.get(entity.entity_type, entity.entity_type.replace("_", " ").title()),
                "Quantidade": entity.count,
                "Ação": "Removido antes da análise",
            }
            for entity in result.privacy.entities
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum identificador pessoal foi detectado no texto enviado.")

    st.caption(
        "O histórico local guarda somente metadados, pontuação e tempos; não guarda currículo nem vaga."
    )
    with st.expander("Detalhes técnicos de privacidade"):
        st.write(f"**Método:** {result.privacy.method}")
        st.json({
            "total_removido": result.privacy.total_removed,
            "documento_bruto_armazenado": result.privacy.raw_document_stored,
            "documento_anonimizado_armazenado": result.privacy.anonymized_document_stored,
            "entidades": [
                {
                    "tipo": ENTITY_LABELS.get(entity.entity_type, entity.entity_type),
                    "quantidade": entity.count,
                }
                for entity in result.privacy.entities
            ],
        })


def render_agents(result: AnalysisResult) -> None:
    st.plotly_chart(agent_timing_chart(result), use_container_width=True)

    rows = []
    for trace in result.traces:
        rows.append({
            "Agente": trace.agent,
            "Resumo": trace.summary,
            "Tempo": format_duration(trace.duration_ms),
            "Confiança": f"{trace.confidence:.0%}",
            "Alertas": ", ".join(trace.alerts) if trace.alerts else "Nenhum",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    engine = result.engine_status
    st.subheader("Motor de análise")
    active_embeddings = bool(engine.get("embedding_enabled"))
    loaded_embeddings = bool(engine.get("embedding_loaded"))
    active_reranker = bool(engine.get("reranker_enabled"))
    loaded_reranker = bool(engine.get("reranker_loaded"))

    cols = st.columns(4)
    cols[0].metric("Embeddings", "Ativos" if active_embeddings else "Desativados")
    cols[1].metric("Modelo carregado", "Sim" if loaded_embeddings else "Fallback")
    cols[2].metric("Reranker", "Ativo" if active_reranker else "Desativado")
    cols[3].metric("Cache de trechos", engine.get("chunk_embedding_cache_entries", 0))

    st.markdown(f"**Modelo semântico:** `{engine.get('embedding_model', 'não configurado')}`")
    st.markdown(f"**Backend:** `{engine.get('embedding_backend', 'não informado')}`")
    if active_reranker:
        st.markdown(f"**Modelo de reranqueamento:** `{engine.get('reranker_model', 'não configurado')}`")
        st.caption("Carregado nesta execução." if loaded_reranker else "Ainda não carregado ou indisponível.")
    if engine.get("embedding_error"):
        st.warning(f"O modelo semântico não pôde ser usado; o fallback local foi acionado. Detalhe: {engine['embedding_error']}")
    if engine.get("reranker_error"):
        st.warning(f"O reranker não pôde ser usado. Detalhe: {engine['reranker_error']}")

    with st.expander("Detalhes técnicos avançados"):
        st.json(engine)


def render_result(result: AnalysisResult, service: ResumeAnalysisService) -> None:
    score_ring(result.score.overall_score)
    total_ms = result.timings_ms.get("total", 0.0)
    main_stage = max(
        ((name, value) for name, value in result.timings_ms.items() if name != "total"),
        key=lambda item: item[1],
        default=("não identificado", 0.0),
    )[0]
    stage_labels = {
        "privacy": "privacidade",
        "candidate": "estruturação do currículo",
        "job": "estruturação da vaga",
        "evidence": "busca de evidências",
        "scoring": "pontuação",
        "review": "revisão",
        "recommendations": "recomendações",
        "report": "relatório",
    }

    cols = st.columns(5)
    values: list[tuple[str, int | str]] = [
        ("Correspondidos", result.score.matched),
        ("Parcialmente atendidos", result.score.partial),
        ("Desejáveis ausentes", result.score.desired_missing),
        ("Obrigatórios ausentes", result.score.required_missing),
        ("Tempo de análise", format_duration(total_ms)),
    ]
    for column, (label, value) in zip(cols, values, strict=True):
        column.metric(label, value)
    st.caption(f"Principal etapa nesta execução: {stage_labels.get(main_stage, main_stage)}.")
    render_result_summary(result)

    tabs = st.tabs(["Visão geral", "Evidências", "Recomendações", "Privacidade", "Agentes", "Exportar"])
    with tabs[0]:
        col1, col2 = st.columns(2)
        col1.plotly_chart(category_chart(result), use_container_width=True)
        col2.plotly_chart(status_chart(result), use_container_width=True)
        st.info(result.review_summary)
        for explanation in result.score.explanation:
            st.markdown(f"- {explanation}")

    with tabs[1]:
        selected_labels = st.multiselect(
            "Status do filtro",
            list(STATUS_VALUES),
            default=list(STATUS_VALUES),
        )
        selected_statuses = {STATUS_VALUES[label] for label in selected_labels}
        for match in result.matches:
            if match.status not in selected_statuses:
                continue
            status_label = STATUS_LABELS[match.status]
            priority_label = PRIORITY_LABELS[match.requirement.priority]
            title = f"{status_label} · {match.requirement.text} · {match.final_score:.2f}".replace(".", ",")
            with st.expander(title):
                st.markdown(f"**Prioridade:** {priority_label}")
                st.markdown("**Melhor evidência encontrada**")
                st.info(match.evidence or "Nenhuma evidência suficiente foi localizada.")
                st.caption(match.explanation)
                frame = candidate_frame(match)
                if not frame.empty:
                    st.markdown("**Trechos candidatos**")
                    st.dataframe(
                        frame,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Lexical": st.column_config.NumberColumn(format="%.3f"),
                            "Aproximada": st.column_config.NumberColumn(format="%.3f"),
                            "Semântica": st.column_config.NumberColumn(format="%.3f"),
                            "Reranker": st.column_config.NumberColumn(format="%.3f"),
                            "Final": st.column_config.NumberColumn(format="%.3f"),
                        },
                    )

    with tabs[2]:
        for item in result.recommendations:
            st.markdown(f"**{item.priority.upper()} · {item.category}**")
            st.write(item.action)

    with tabs[3]:
        render_privacy(result)

    with tabs[4]:
        render_agents(result)

    with tabs[5]:
        left, middle, right = st.columns(3)
        left.download_button(
            "Baixar Markdown",
            result.markdown_report,
            file_name=f"analise-{result.analysis_id}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        middle.download_button(
            "Baixar JSON",
            service.to_json(result),
            file_name=f"analise-{result.analysis_id}.json",
            mime="application/json",
            use_container_width=True,
        )
        right.download_button(
            "Baixar CSV",
            service.to_csv(result),
            file_name=f"analise-{result.analysis_id}.csv",
            mime="text/csv",
            use_container_width=True,
        )


def main() -> None:
    # Resultados guardados na sessão podem ter sido gerados por uma versão
    # anterior do esquema Pydantic. Ao publicar uma atualização, descartamos
    # somente o resultado incompatível e preservamos o restante da interface.
    if st.session_state.get("_app_version") != APP_VERSION:
        st.session_state.pop("last_result", None)
        st.session_state["_app_version"] = APP_VERSION

    inject_css()
    enforce_optional_oidc(Settings())
    st.markdown(
        """
        <div class="hero">
          <div><span class="eyebrow">V6.0.0 · LOCAL · CÓDIGO ABERTO</span><h1>IA de Correspondência de Currículos</h1><p>Plataforma multiagente para comparar currículos e vagas com evidências, privacidade e explicabilidade.</p></div>
          <div class="hero-badges"><span>Otimizado para CPU</span><span>API local com FastAPI</span><span>Fallback totalmente offline</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.pop("session_cleared", False):
        st.success("Sessão limpa com sucesso.")

    with st.sidebar:
        st.header("Configuração")
        profile_label = st.radio(
            "Perfil de execução",
            ["⚡ Demonstração", "⚖️ Equilibrado", "🧠 Completo"],
            index=0,
        )
        profiles: dict[str, Literal["demo", "balanced", "complete"]] = {
            "⚡ Demonstração": "demo",
            "⚖️ Equilibrado": "balanced",
            "🧠 Completo": "complete",
        }
        profile = profiles[profile_label]
        strictness_label = st.select_slider(
            "Rigor",
            options=["Flexível", "Equilibrado", "Conservador"],
            value="Equilibrado",
        )
        strictness = cast(
            Literal["flexível", "equilibrado", "conservador"],
            strictness_label.lower(),
        )
        st.caption("Para apresentar em notebook, use Demonstração. O modo Completo exige mais memória RAM.")
        if st.button("Carregar exemplo", use_container_width=True):
            load_example()
            st.rerun()
        if st.button("Limpar sessão", use_container_width=True):
            st.session_state.clear()
            st.session_state["session_cleared"] = True
            st.cache_data.clear()
            st.rerun()

    input_mode = st.radio(
        "Forma de entrada",
        ["Colar textos", "Enviar arquivos"],
        horizontal=True,
    )
    resume_text = st.session_state.get("resume_text", "")
    job_text = st.session_state.get("job_text", "")

    with st.form("analysis_form"):
        if input_mode == "Colar textos":
            left, right = st.columns(2)
            resume_text = left.text_area(
                "Currículo",
                value=resume_text,
                height=390,
                key="resume_text_input",
                placeholder="Cole aqui o currículo...",
            )
            job_text = right.text_area(
                "Descrição da vaga",
                value=job_text,
                height=390,
                key="job_text_input",
                placeholder="Cole aqui a descrição da vaga...",
            )
        else:
            st.caption("Formatos aceitos: PDF, DOCX e TXT. Limite padrão: 10 MB por arquivo.")
            left, right = st.columns(2)
            resume_file = left.file_uploader("Arquivo do currículo", type=["pdf", "docx", "txt"])
            job_file = right.file_uploader("Arquivo da vaga", type=["pdf", "docx", "txt"])
            if resume_file and job_file:
                reader = get_reader(profile)
                try:
                    resume_text = reader.read_upload(
                        resume_file.name,
                        resume_file.getvalue(),
                        reported_type=resume_file.type,
                    )
                    job_text = reader.read_upload(
                        job_file.name,
                        job_file.getvalue(),
                        reported_type=job_file.type,
                    )
                    st.success("Arquivos validados e textos extraídos.")
                except Exception as exc:
                    st.error(str(exc))
        consent = st.checkbox(
            "Entendo que o resultado apoia revisão humana e não toma decisão de contratação."
        )
        submitted = st.form_submit_button(
            "Executar análise multiagente",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if not consent:
            st.error("Confirme o aviso de uso responsável.")
        elif len(resume_text.strip()) < 10 or len(job_text.strip()) < 10:
            st.error("Informe currículo e vaga com conteúdo suficiente.")
        else:
            service = get_service(profile)
            request = AnalysisRequest(
                resume_text=resume_text,
                job_text=job_text,
                profile=profile,
                strictness=strictness,
            )
            try:
                with st.status("Executando pipeline local...", expanded=True) as status:
                    st.write("1. Removendo dados pessoais")
                    st.write("2. Estruturando currículo e vaga")
                    st.write("3. Recuperando evidências em lote")
                    st.write("4. Calculando pontuação e revisão")
                    result = service.analyze(request)
                    status.update(label="Análise concluída", state="complete", expanded=False)
            except Exception:
                st.session_state.pop("last_result", None)
                st.error(
                    "Não foi possível concluir a análise. Verifique as entradas e tente novamente."
                )
            else:
                st.session_state["last_result"] = result.model_dump(mode="json")

    if "last_result" in st.session_state:
        try:
            result = AnalysisResult.model_validate(st.session_state["last_result"])
        except (ValidationError, TypeError, ValueError):
            st.session_state.pop("last_result", None)
            st.warning(
                "A análise anterior foi criada por uma versão incompatível e foi removida. "
                "Execute uma nova análise."
            )
        else:
            render_result(result, get_service(result.profile))


if __name__ == "__main__":
    main()
