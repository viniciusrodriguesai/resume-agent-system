from __future__ import annotations

import html
import json
import time
from dataclasses import replace
from pathlib import Path

import pandas as pd
import streamlit as st

from resume_v4.config import Config
from resume_v4.services.documentos import LeitorDocumentos
from resume_v4.workflow import SistemaV4


ROOT = Path(__file__).resolve().parent
EXEMPLO_CURRICULO = ROOT / "examples" / "curriculo_exemplo.txt"
EXEMPLO_VAGA = ROOT / "examples" / "vaga_exemplo.txt"

st.set_page_config(
    page_title="MatchAI — Analisador Multiagente",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def aplicar_css() -> None:
    caminho = ROOT / "assets" / "styles.css"
    if caminho.exists():
        st.markdown(
            f"<style>{caminho.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def config_por_perfil(perfil: str) -> Config:
    base = Config()
    if perfil == "⚡ Demonstração":
        return replace(
            base,
            modelo_embeddings=(
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            ),
            usar_embeddings=True,
            usar_reranker=False,
            usar_docling=False,
            usar_presidio=False,
            top_k=3,
            max_revisoes=1,
        )
    if perfil == "⚖️ Equilibrado":
        return replace(
            base,
            modelo_embeddings=(
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            ),
            usar_embeddings=True,
            usar_reranker=False,
            usar_docling=True,
            usar_presidio=False,
            top_k=4,
            max_revisoes=1,
        )
    return replace(
        base,
        usar_embeddings=True,
        usar_reranker=True,
        usar_docling=True,
        usar_presidio=True,
        top_k=5,
        max_revisoes=1,
    )


@st.cache_resource(show_spinner="Inicializando os agentes e o motor semântico...")
def carregar_sistema(perfil: str) -> SistemaV4:
    return SistemaV4(config_por_perfil(perfil))


@st.cache_resource(show_spinner=False)
def carregar_leitor(perfil: str) -> LeitorDocumentos:
    return LeitorDocumentos(config_por_perfil(perfil))


def badge(texto: str, classe: str = "neutral") -> str:
    return (
        f'<span class="badge badge-{classe}">{html.escape(str(texto))}</span>'
    )


def rotulo_status(status: str) -> tuple[str, str]:
    mapa = {
        "atendido": ("Atendido", "success"),
        "parcial": ("Parcial", "warning"),
        "ausente": ("Ausente", "danger"),
        "obrigatorio": ("Obrigatório", "danger"),
        "desejavel": ("Desejável", "brand"),
        "neutro": ("Neutro", "neutral"),
    }
    return mapa.get(str(status), (str(status).title(), "neutral"))


def card_metrica(titulo: str, valor: str, nota: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-eyebrow">{html.escape(titulo)}</div>
          <div class="kpi-value">{html.escape(str(valor))}</div>
          <div class="kpi-note">{html.escape(nota)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def cor_score(score: int) -> str:
    if score >= 82:
        return "#16835b"
    if score >= 62:
        return "#c87916"
    return "#c2414f"


def resumo_nivel(score: int) -> str:
    if score >= 82:
        return "O currículo apresenta forte aderência aos requisitos avaliados."
    if score >= 62:
        return "Há boa compatibilidade, com lacunas pontuais que merecem atenção."
    return "A vaga exige competências que ainda não possuem evidência suficiente."


def renderizar_score(score: int, nivel: str, texto_revisor: str) -> None:
    graus = max(0, min(score, 100)) * 3.6
    cor = cor_score(score)
    st.markdown(
        f"""
        <div class="score-shell">
          <div class="score-ring" style="background: conic-gradient({cor} {graus}deg, #e7eaf1 0deg);">
            <div class="score-ring-content">
              <div class="score-number">{score}%</div>
              <div class="score-caption">compatibilidade</div>
            </div>
          </div>
          <div class="score-copy">
            <div style="margin-bottom:.55rem;">{badge(nivel, 'success' if score >= 82 else 'warning' if score >= 62 else 'danger')}</div>
            <h3>{html.escape(resumo_nivel(score))}</h3>
            <p>{html.escape(texto_revisor or 'Análise concluída pelo conjunto de agentes especializados.')}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def carregar_exemplos() -> None:
    if EXEMPLO_CURRICULO.exists():
        st.session_state["curriculo_texto"] = EXEMPLO_CURRICULO.read_text(
            encoding="utf-8"
        )
    if EXEMPLO_VAGA.exists():
        st.session_state["vaga_texto"] = EXEMPLO_VAGA.read_text(
            encoding="utf-8"
        )


def limpar_tudo(liberar_modelos: bool = False) -> None:
    for chave in [
        "resultado_v4",
        "curriculo_texto",
        "vaga_texto",
        "tempo_analise_ui",
    ]:
        st.session_state.pop(chave, None)
    if liberar_modelos:
        st.cache_resource.clear()


def motor_resumido(status: dict) -> str:
    modelo = str(status.get("modelo_embeddings", "fallback"))
    if "MiniLM" in modelo or "minilm" in modelo.lower():
        return "MiniLM"
    if "bge-m3" in modelo.lower():
        return "BGE-M3"
    return "Fallback lexical"


def renderizar_nuvem_competencias(competencias: list[dict]) -> None:
    rotulos = [str(item.get("rotulo", "")) for item in competencias if item]
    if not rotulos:
        st.info("Nenhuma competência foi identificada.")
        return
    conteudo = "".join(
        f'<span class="skill-pill">{html.escape(rotulo)}</span>'
        for rotulo in rotulos[:40]
    )
    st.markdown(
        f'<div class="skill-cloud">{conteudo}</div>',
        unsafe_allow_html=True,
    )


def renderizar_cards_evidencias(resultados: list[dict], limite: int = 8) -> None:
    if not resultados:
        st.markdown(
            '<div class="empty-state">Nenhuma evidência disponível.</div>',
            unsafe_allow_html=True,
        )
        return
    for item in resultados[:limite]:
        status_texto, status_classe = rotulo_status(item.get("status", ""))
        prioridade_texto, prioridade_classe = rotulo_status(
            item.get("prioridade", "")
        )
        requisito = html.escape(str(item.get("texto", "Requisito")))
        evidencia = html.escape(
            str(item.get("evidencia") or "Nenhuma evidência localizada no currículo.")
        )
        score = float(item.get("score_final", 0.0))
        st.markdown(
            f"""
            <div class="evidence-card">
              <div class="evidence-title">
                <div>{requisito}</div>
                <div style="display:flex;gap:.35rem;flex-wrap:wrap;justify-content:flex-end;">
                  {badge(prioridade_texto, prioridade_classe)}
                  {badge(status_texto, status_classe)}
                  {badge(f'{score:.2f}', 'neutral')}
                </div>
              </div>
              <div class="evidence-quote">“{evidencia}”</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def renderizar_recomendacoes(recomendacoes: list[dict]) -> None:
    if not recomendacoes:
        st.info("Nenhuma recomendação foi gerada.")
        return
    for item in recomendacoes:
        prioridade = str(item.get("prioridade", "Baixa"))
        classe = (
            "high"
            if prioridade.lower().startswith("alta")
            else "medium"
            if prioridade.lower().startswith("m")
            else "low"
        )
        st.markdown(
            f"""
            <div class="recommendation-card {classe}">
              <div style="display:flex;gap:.45rem;align-items:center;margin-bottom:.5rem;">
                {badge(prioridade, 'danger' if classe == 'high' else 'warning' if classe == 'medium' else 'success')}
                {badge(str(item.get('categoria', 'Recomendação')), 'neutral')}
              </div>
              <div style="line-height:1.58;color:#344054;">{html.escape(str(item.get('acao', '')))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def renderizar_timeline(rastreio: list[dict]) -> None:
    if not rastreio:
        st.info("Nenhuma etapa registrada.")
        return
    for indice, item in enumerate(rastreio, start=1):
        agente = html.escape(str(item.get("agente", f"Agente {indice}")))
        resumo = html.escape(str(item.get("resumo", "Etapa concluída.")))
        tempo = item.get("tempo_ms", 0)
        confianca = item.get("confianca", 0)
        st.markdown(
            f"""
            <div class="timeline-item">
              <div class="timeline-dot">{indice}</div>
              <div class="timeline-copy">
                <strong>{agente}</strong>
                <span>{resumo} · {tempo} ms · confiança {confianca}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


aplicar_css()
st.session_state.setdefault("curriculo_texto", "")
st.session_state.setdefault("vaga_texto", "")

st.markdown(
    """
    <section class="hero">
      <div class="hero-top">
        <span class="badge badge-glass">V4.1 FRONTEND PRO</span>
        <span class="badge badge-glass">100% local</span>
        <span class="badge badge-glass">Privacidade por padrão</span>
      </div>
      <h1>MatchAI: análise inteligente entre currículo e vaga.</h1>
      <p>Um sistema multiagente explicável que transforma requisitos em evidências, identifica lacunas e gera recomendações práticas sem substituir a avaliação humana.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 🧠 MatchAI")
    st.caption("Painel de configuração da análise")

    perfil_execucao = st.selectbox(
        "Perfil de execução",
        ["⚡ Demonstração", "⚖️ Equilibrado", "🧠 Completo"],
        index=0,
        help=(
            "Demonstração usa MiniLM sem reranker pesado. Completo usa BGE-M3, "
            "reranker, Docling e Presidio."
        ),
    )
    descricoes = {
        "⚡ Demonstração": (
            "Rápido e estável para apresentação: MiniLM, 3 evidências e "
            "privacidade local leve."
        ),
        "⚖️ Equilibrado": (
            "MiniLM com leitura avançada de arquivos e até 4 evidências por requisito."
        ),
        "🧠 Completo": (
            "BGE-M3, reranker, Docling e Presidio. Mais preciso, porém mais lento."
        ),
    }
    st.markdown(
        f"""
        <div class="mode-card">
          <div class="mode-title">{html.escape(perfil_execucao)}</div>
          <div class="mode-copy">{html.escape(descricoes[perfil_execucao])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label">Entrada</div>', unsafe_allow_html=True)
    modo = st.radio(
        "Forma de entrada",
        ["✍️ Colar textos", "📎 Enviar arquivos"],
        index=0,
        label_visibility="collapsed",
    )
    rigor = st.select_slider(
        "Rigor da comparação",
        options=["Flexível", "Equilibrado", "Conservador"],
        value="Equilibrado",
    )

    st.markdown('<div class="section-label">Atalhos</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Usar exemplo", use_container_width=True):
            carregar_exemplos()
            st.rerun()
    with col_b:
        if st.button("Limpar", use_container_width=True):
            limpar_tudo()
            st.rerun()

    if st.button("Liberar modelos da memória", use_container_width=True):
        limpar_tudo(liberar_modelos=True)
        st.success("Recursos liberados.")
        st.rerun()

    configuracao_ativa = config_por_perfil(perfil_execucao)
    st.markdown('<div class="section-label">Motor ativo</div>', unsafe_allow_html=True)
    chips = [
        badge("Embeddings", "success" if configuracao_ativa.usar_embeddings else "neutral"),
        badge("Reranker", "success" if configuracao_ativa.usar_reranker else "neutral"),
        badge("Docling", "success" if configuracao_ativa.usar_docling else "neutral"),
        badge("Presidio", "success" if configuracao_ativa.usar_presidio else "neutral"),
    ]
    st.markdown(
        '<div style="display:flex;gap:.35rem;flex-wrap:wrap;">'
        + "".join(chips)
        + "</div>",
        unsafe_allow_html=True,
    )
    st.caption("Para amanhã, use ⚡ Demonstração e rigor Equilibrado.")

sistema = carregar_sistema(perfil_execucao)
leitor = carregar_leitor(perfil_execucao)

curriculo = ""
vaga = ""

st.markdown('<div class="section-label">Documentos para análise</div>', unsafe_allow_html=True)

if modo.startswith("✍️"):
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            '<div class="input-heading"><strong>👤 Currículo</strong><span>experiências, competências e projetos</span></div>',
            unsafe_allow_html=True,
        )
        curriculo = st.text_area(
            "Currículo",
            height=390,
            key="curriculo_texto",
            placeholder="Cole aqui o currículo em português ou inglês...",
            label_visibility="collapsed",
        )
        st.caption(f"{len(curriculo):,} caracteres".replace(",", "."))
    with c2:
        st.markdown(
            '<div class="input-heading"><strong>💼 Descrição da vaga</strong><span>requisitos, responsabilidades e diferenciais</span></div>',
            unsafe_allow_html=True,
        )
        vaga = st.text_area(
            "Descrição da vaga",
            height=390,
            key="vaga_texto",
            placeholder="Cole aqui a descrição da vaga em português ou inglês...",
            label_visibility="collapsed",
        )
        st.caption(f"{len(vaga):,} caracteres".replace(",", "."))
else:
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            '<div class="input-heading"><strong>👤 Currículo</strong><span>PDF, DOCX, TXT ou MD</span></div>',
            unsafe_allow_html=True,
        )
        arq_curriculo = st.file_uploader(
            "Currículo",
            type=["pdf", "docx", "txt", "md"],
            key="arq_curriculo_v41",
            label_visibility="collapsed",
        )
        if arq_curriculo:
            try:
                leitura = leitor.ler_upload(arq_curriculo, arq_curriculo.name)
                curriculo = leitura["texto"]
                st.success(f"Leitura concluída com {leitura['metodo']}.")
                with st.expander("Pré-visualizar conteúdo extraído"):
                    st.text(curriculo[:6000])
            except Exception as erro:
                st.error(f"Não foi possível ler o currículo: {erro}")
    with c2:
        st.markdown(
            '<div class="input-heading"><strong>💼 Descrição da vaga</strong><span>PDF, DOCX, TXT ou MD</span></div>',
            unsafe_allow_html=True,
        )
        arq_vaga = st.file_uploader(
            "Descrição da vaga",
            type=["pdf", "docx", "txt", "md"],
            key="arq_vaga_v41",
            label_visibility="collapsed",
        )
        if arq_vaga:
            try:
                leitura = leitor.ler_upload(arq_vaga, arq_vaga.name)
                vaga = leitura["texto"]
                st.success(f"Leitura concluída com {leitura['metodo']}.")
                with st.expander("Pré-visualizar conteúdo extraído"):
                    st.text(vaga[:6000])
            except Exception as erro:
                st.error(f"Não foi possível ler a vaga: {erro}")

executar = st.button(
    "✨ Executar análise multiagente",
    type="primary",
    use_container_width=True,
)

if executar:
    if not curriculo.strip() or not vaga.strip():
        st.error("Informe o currículo e a descrição da vaga antes de executar.")
    else:
        inicio = time.perf_counter()
        try:
            with st.status(
                "Executando o grafo multiagente...",
                expanded=True,
            ) as status_execucao:
                status_execucao.write(
                    "🔒 Preparando privacidade, estruturação, busca semântica, pontuação e revisão."
                )
                resultado_novo = sistema.analisar(curriculo, vaga, rigor=rigor)
                tempo_total = round(time.perf_counter() - inicio, 2)
                st.session_state["resultado_v4"] = resultado_novo
                st.session_state["tempo_analise_ui"] = tempo_total
                status_execucao.update(
                    label=f"Análise concluída em {tempo_total:.1f} segundos",
                    state="complete",
                    expanded=False,
                )
        except Exception as erro:
            st.exception(erro)

resultado = st.session_state.get("resultado_v4")
if not resultado:
    st.markdown(
        """
        <div class="empty-state">
          <div style="font-size:2rem;margin-bottom:.5rem;">📊</div>
          <strong>O painel de resultados aparecerá aqui.</strong><br>
          Cole os dois textos ou carregue os arquivos e execute a análise.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

pontuacao = resultado.get("pontuacao", {})
score = int(pontuacao.get("score_geral", 0))
categorias = pontuacao.get("scores_categoria", {})
contagens = pontuacao.get("contagens", {})
revisao = resultado.get("revisao", {})
status_motor = resultado.get("status_motor", {})
tempo_total = st.session_state.get("tempo_analise_ui", 0)

st.markdown('<div class="section-label">Resultado executivo</div>', unsafe_allow_html=True)
col_score, col_kpis = st.columns([1.35, 1.65], gap="large")
with col_score:
    renderizar_score(
        score,
        str(pontuacao.get("nivel", "Baixa")),
        str(revisao.get("texto_final", "")),
    )
with col_kpis:
    k1, k2 = st.columns(2)
    with k1:
        card_metrica(
            "Requisitos atendidos",
            str(contagens.get("atendido", 0)),
            "evidência forte localizada",
        )
    with k2:
        card_metrica(
            "Lacunas",
            str(contagens.get("ausente", 0)),
            "requisitos sem evidência",
        )
    k3, k4 = st.columns(2)
    with k3:
        card_metrica(
            "Motor semântico",
            motor_resumido(status_motor),
            "modelo utilizado na recuperação",
        )
    with k4:
        card_metrica(
            "Tempo total",
            f"{tempo_total:.1f}s" if tempo_total else "—",
            f"{resultado.get('revisoes', 0)} ciclo(s) de revisão",
        )

abas = st.tabs(
    [
        "📊 Dashboard",
        "🔎 Evidências",
        "👤 Perfis",
        "🧭 Recomendações",
        "🛡️ Auditoria",
        "🧩 Agentes",
        "🗂️ Histórico",
        "⬇️ Exportar",
    ]
)

with abas[0]:
    c_grafico, c_resumo = st.columns([1.35, 1], gap="large")
    with c_grafico:
        st.markdown("### Pontuação por categoria")
        if categorias:
            quadro = pd.DataFrame(
                {
                    "Categoria": list(categorias.keys()),
                    "Pontuação": list(categorias.values()),
                }
            ).set_index("Categoria")
            st.bar_chart(quadro, horizontal=True)
        else:
            st.info("Não há categorias suficientes para gerar o gráfico.")
    with c_resumo:
        st.markdown("### Diagnóstico rápido")
        resumo_itens = [
            ("Atendidos", contagens.get("atendido", 0), "success"),
            ("Parciais", contagens.get("parcial", 0), "warning"),
            ("Ausentes", contagens.get("ausente", 0), "danger"),
            ("Obrigatórios ausentes", pontuacao.get("ausentes_obrigatorios", 0), "danger"),
        ]
        for nome, valor, classe in resumo_itens:
            st.markdown(
                f"<div class='panel' style='margin-bottom:.55rem;padding:.78rem .9rem;display:flex;justify-content:space-between;align-items:center;'><strong>{html.escape(nome)}</strong>{badge(str(valor), classe)}</div>",
                unsafe_allow_html=True,
            )
        st.caption(
            f"Rigor aplicado: {pontuacao.get('rigor', 'Equilibrado')} · "
            f"revisões: {resultado.get('revisoes', 0)}"
        )

with abas[1]:
    resultados = pontuacao.get("resultados", [])
    st.markdown("### Evidências por requisito")
    f1, f2, f3 = st.columns([1.4, 1, 1])
    with f1:
        busca = st.text_input(
            "Buscar requisito ou evidência",
            placeholder="Ex.: Python, comunicação, AWS...",
        )
    with f2:
        filtro_status = st.multiselect(
            "Status",
            ["atendido", "parcial", "ausente"],
            default=["atendido", "parcial", "ausente"],
        )
    with f3:
        filtro_prioridade = st.multiselect(
            "Prioridade",
            ["obrigatorio", "desejavel", "neutro"],
            default=["obrigatorio", "desejavel", "neutro"],
        )

    filtrados = []
    termo = busca.strip().lower()
    for item in resultados:
        texto_busca = (
            f"{item.get('texto', '')} {item.get('evidencia', '')}"
        ).lower()
        if termo and termo not in texto_busca:
            continue
        if item.get("status") not in filtro_status:
            continue
        if item.get("prioridade") not in filtro_prioridade:
            continue
        filtrados.append(item)

    st.caption(f"{len(filtrados)} de {len(resultados)} requisitos exibidos")
    renderizar_cards_evidencias(filtrados, limite=10)
    with st.expander("Ver tabela completa"):
        linhas = [
            {
                "Requisito": item.get("texto"),
                "Prioridade": item.get("prioridade"),
                "Categoria": item.get("categoria"),
                "Status": item.get("status"),
                "Pontuação": item.get("score_final"),
                "Evidência": item.get("evidencia") or "Nenhuma evidência",
                "Método": f"{item.get('metodo')} / {item.get('metodo_reranker')}",
            }
            for item in filtrados
        ]
        if linhas:
            st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)

with abas[2]:
    perfil_curriculo = resultado.get("perfil_curriculo", {})
    perfil_vaga = resultado.get("perfil_vaga", {})
    esquerda, direita = st.columns(2, gap="large")
    with esquerda:
        st.markdown("### 👤 Perfil do currículo")
        st.markdown(
            f"<div class='panel'><div class='panel-title'>{html.escape(str(perfil_curriculo.get('candidato', 'Candidato anonimizado')))}</div><div class='panel-subtitle'>Competências e evidências identificadas pelos agentes</div></div>",
            unsafe_allow_html=True,
        )
        renderizar_nuvem_competencias(perfil_curriculo.get("competencias", []))
        with st.expander("Formação", expanded=True):
            for item in perfil_curriculo.get("formacao", []):
                st.write(f"• {item}")
        with st.expander("Experiência"):
            for item in perfil_curriculo.get("experiencia", []):
                st.write(f"• {item}")
        with st.expander("Projetos"):
            for item in perfil_curriculo.get("projetos", []):
                st.write(f"• {item}")
    with direita:
        st.markdown("### 💼 Perfil da vaga")
        st.markdown(
            f"<div class='panel'><div class='panel-title'>{html.escape(str(perfil_vaga.get('titulo', 'Vaga')))}</div><div class='panel-subtitle'>{len(perfil_vaga.get('requisitos', []))} requisitos estruturados</div></div>",
            unsafe_allow_html=True,
        )
        requisitos = pd.DataFrame(perfil_vaga.get("requisitos", []))
        if not requisitos.empty:
            colunas = [
                coluna
                for coluna in ["texto", "prioridade", "categoria", "tipo", "origem"]
                if coluna in requisitos.columns
            ]
            st.dataframe(
                requisitos[colunas],
                use_container_width=True,
                hide_index=True,
            )

with abas[3]:
    st.markdown("### Plano de melhoria priorizado")
    st.caption(
        "As sugestões não inventam competências: elas indicam o que estudar, comprovar ou reescrever."
    )
    renderizar_recomendacoes(resultado.get("recomendacoes", []))

with abas[4]:
    privacidade = resultado.get("privacidade", {})
    rev = resultado.get("revisao", {})
    p1, p2, p3 = st.columns(3)
    with p1:
        card_metrica(
            "Entidades removidas",
            str(len(privacidade.get("entidades", []))),
            "dados pessoais protegidos",
        )
    with p2:
        card_metrica(
            "Decisão do revisor",
            str(rev.get("decisao", "—")).title(),
            "controle de consistência",
        )
    with p3:
        card_metrica(
            "Método de privacidade",
            str(privacidade.get("metodo", "Fallback local")),
            "pré-processamento antes do matching",
        )
    st.markdown("### Revisão final")
    if rev.get("decisao") == "aprovado":
        st.success(rev.get("texto_final", "Resultado aprovado."))
    else:
        st.warning(rev.get("texto_final", "Resultado revisado."))
    for problema in rev.get("problemas", []):
        st.write(f"- {problema}")
    with st.expander("Entidades identificadas"):
        entidades = pd.DataFrame(privacidade.get("entidades", []))
        if entidades.empty:
            st.info("Nenhuma entidade pessoal foi identificada.")
        else:
            st.dataframe(entidades, use_container_width=True, hide_index=True)
    with st.expander("Currículo anonimizado utilizado pelos agentes"):
        st.code(resultado.get("curriculo_anonimizado", ""), language=None)
    st.info(
        "A pontuação é apoio à decisão. O sistema não deve substituir entrevistas, "
        "avaliação humana, contexto profissional ou adaptações de acessibilidade."
    )

with abas[5]:
    st.markdown("### Fluxo de execução")
    st.caption(
        "Cada etapa possui responsabilidade própria e compartilha estado pelo grafo."
    )
    renderizar_timeline(resultado.get("rastreio", []))

with abas[6]:
    st.markdown("### Análises recentes")
    historico = pd.DataFrame(sistema.historico.listar())
    if historico.empty:
        st.info("Nenhuma análise foi salva ainda.")
    else:
        st.dataframe(historico, use_container_width=True, hide_index=True)

with abas[7]:
    st.markdown("### Central de exportação")
    st.caption("Baixe o relatório completo ou os dados estruturados da análise.")
    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button(
            "📄 Relatório Markdown",
            resultado.get("relatorio_markdown", ""),
            "relatorio_curriculo_vaga.md",
            "text/markdown",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "🧾 Dados JSON",
            resultado.get("relatorio_json", json.dumps({}, indent=2)),
            "analise_curriculo_vaga.json",
            "application/json",
            use_container_width=True,
        )
    with d3:
        csv = pd.DataFrame(pontuacao.get("resultados", [])).to_csv(
            index=False
        ).encode("utf-8-sig")
        st.download_button(
            "📊 Evidências CSV",
            csv,
            "requisitos_evidencias.csv",
            "text/csv",
            use_container_width=True,
        )
    with st.expander("Prévia do relatório", expanded=True):
        st.markdown(resultado.get("relatorio_markdown", ""))
