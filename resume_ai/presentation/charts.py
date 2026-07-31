from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

from resume_ai.domain.models import AnalysisResult


def category_chart(result: AnalysisResult) -> go.Figure:
    categories = result.score.categories
    figure = go.Figure(go.Bar(
        x=[item.score for item in categories],
        y=[item.category for item in categories],
        orientation="h",
        text=[f"{item.score}%" for item in categories],
        textposition="auto",
    ))
    figure.update_layout(
        title="Compatibilidade por categoria",
        xaxis_title="Pontuação (%)",
        yaxis_title="",
        xaxis_range=[0, 100],
        height=max(320, 52 * len(categories)),
        margin=dict(l=10, r=10, t=45, b=20),
    )
    return figure


def status_chart(result: AnalysisResult) -> go.Figure:
    figure = go.Figure(go.Pie(
        labels=["Atendidos", "Parciais", "Ausentes"],
        values=[result.score.matched, result.score.partial, result.score.missing],
        hole=0.62,
        textinfo="label+value",
    ))
    figure.update_layout(title="Distribuição dos requisitos", height=340, margin=dict(l=10, r=10, t=45, b=10))
    return figure


def agent_timing_chart(result: AnalysisResult) -> go.Figure:
    figure = go.Figure(go.Bar(
        x=[trace.duration_ms for trace in result.traces],
        y=[trace.agent for trace in result.traces],
        orientation="h",
        text=[f"{trace.duration_ms:.0f} ms" for trace in result.traces],
        textposition="auto",
    ))
    figure.update_layout(title="Tempo por agente", xaxis_title="Milissegundos", height=max(340, 45 * len(result.traces)), margin=dict(l=10, r=10, t=45, b=20))
    return figure
