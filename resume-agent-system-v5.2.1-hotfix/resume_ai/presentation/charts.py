from __future__ import annotations

import math

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
        labels=["Correspondidos", "Parcialmente atendidos", "Ausentes"],
        values=[result.score.matched, result.score.partial, result.score.missing],
        hole=0.62,
        textinfo="label+value",
    ))
    figure.update_layout(
        title="Distribuição dos requisitos",
        height=340,
        margin=dict(l=10, r=10, t=45, b=10),
    )
    return figure


def _duration_label(duration_ms: float) -> str:
    if duration_ms >= 1000:
        return f"{duration_ms / 1000:.2f} s".replace(".", ",")
    if duration_ms >= 10:
        return f"{duration_ms:.0f} ms"
    return f"{duration_ms:.2f} ms".replace(".", ",")


def agent_timing_chart(result: AnalysisResult) -> go.Figure:
    durations = [max(trace.duration_ms, 0.01) for trace in result.traces]
    positive = [value for value in durations if value > 0]
    ratio = max(positive) / max(min(positive), 0.01) if positive else 1
    use_log = ratio > 100

    x_values = [math.log10(value + 1) for value in durations] if use_log else durations
    title = "Tempo por agente — escala visual logarítmica" if use_log else "Tempo por agente"
    xaxis_title = "Escala logarítmica; valores reais aparecem nas barras" if use_log else "Milissegundos"

    figure = go.Figure(go.Bar(
        x=x_values,
        y=[trace.agent for trace in result.traces],
        orientation="h",
        text=[_duration_label(trace.duration_ms) for trace in result.traces],
        textposition="auto",
        customdata=durations,
        hovertemplate="%{y}<br>%{customdata:.2f} ms<extra></extra>",
    ))
    figure.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        height=max(340, 45 * len(result.traces)),
        margin=dict(l=10, r=10, t=45, b=20),
    )
    if use_log:
        figure.update_xaxes(showticklabels=False)
    return figure
