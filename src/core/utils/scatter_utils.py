# scatter plot utils
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from core.utils.sankey_utils import clean_question, wrap_text


def _build_citation_lookup(df_citations):
    """Returns dict (iso, question_clean, answer_clean) -> (citation, pincite, url)"""
    lookup = {}
    if df_citations is None or df_citations.empty:
        return lookup

    df = df_citations.copy()
    df['iso'] = df['iso'].astype(str)
    df['Question_clean'] = df['Question'].apply(clean_question)
    df['Answer_clean'] = df['Answer'].astype(str).str.strip().str.lower().str.rstrip('.')

    for _, row in df.iterrows():
        url = str(row.get('Source_URL', '')).strip()
        if not url or url == 'nan':
            continue
        key = (row['iso'], row['Question_clean'], row['Answer_clean'])
        lookup[key] = (
            str(row.get('Citation', '') or ''),
            str(row.get('Pincite_Text', '') or ''),
            url,
        )
    return lookup


def _format_citation(citation):
    if citation and citation != 'No citation available':
        return f"<br><br><b>Citation:</b><br>{wrap_text(citation, 60)}"
    return ""


def _format_pincite(pincite):
    if pincite and pincite != 'No source available':
        return f"<br><br><b>Source:</b><br>{wrap_text(pincite, 60)}"
    return ""


def _customdata_for(iso, question, answer, lookup):
    """Returns [citation_display, pincite_display, url] for one point."""
    if pd.isna(answer):
        return ["", "", ""]

    question_clean = clean_question(question)
    answer_clean = str(answer).strip().lower().rstrip('.')
    key = (str(iso), question_clean, answer_clean)

    entry = lookup.get(key)
    if not entry:
        return ["", "", ""]

    citation, pincite, url = entry
    return [_format_citation(citation), _format_pincite(pincite), url]


HOVERTEMPLATE = (
    '<b>%{y}</b><br>'
    'Response: %{x}'
    '%{customdata[0]}'
    '%{customdata[1]}'
    '<extra></extra>'
)


def create_uof_scatter_figure(df, preguntas, df_citations=None):
    """Crea scatter plot para Use of Force"""
    lookup = _build_citation_lookup(df_citations)

    fig = px.scatter(
        df,
        y='State',
        x=preguntas[0],
        hover_data=['iso'],
        title=f'',
        labels={'State': 'Country', preguntas[0]: 'Response'}
    )

    customdata = [
        _customdata_for(iso, preguntas[0], answer, lookup)
        for iso, answer in zip(df['iso'], df[preguntas[0]])
    ]
    fig.update_traces(customdata=customdata, hovertemplate=HOVERTEMPLATE)

    fig.update_layout(
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis={'categoryorder': 'total ascending'},
        margin=dict(l=100, r=50, t=50, b=100),
        height=1200
    )

    botones = create_scatter_dropdown_buttons(df, preguntas, lookup)

    fig.update_layout(
        updatemenus=[{
            'buttons': botones,
            'direction': 'down',
            'showactive': True,
            'x': 0.1,
            'xanchor': 'left',
            'y': 1.15,
            'yanchor': 'top'
        }]
    )

    return fig


def create_by_state_scatter_figure(df, preguntas, estados, df_citations=None):
    """Crea scatter plot por estado para Use of Force"""
    lookup = _build_citation_lookup(df_citations)

    estado_inicial = estados[0]
    df_filtrado = df[df['State'] == estado_inicial]
    df_melted = df_filtrado.melt(
        id_vars=['State', 'iso'],
        value_vars=preguntas,
        var_name='Question',
        value_name='Response'
    )

    fig = px.scatter(
        df_melted,
        x='Response',
        y='Question',
        title=f'Responses for {estado_inicial}',
        labels={'Response': 'Response Value', 'Question': ''},
        height=1000,
        width=1500,
        hover_data=['State']
    )

    customdata = [
        _customdata_for(iso, question, answer, lookup)
        for iso, question, answer in zip(df_melted['iso'], df_melted['Question'], df_melted['Response'])
    ]
    fig.update_traces(customdata=customdata, hovertemplate=HOVERTEMPLATE)

    fig.update_layout(
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis={'categoryorder': 'total descending'},
        margin=dict(l=150, r=50, t=80, b=100),
        showlegend=False,
        transition={'duration': 500}
    )

    fig.update_traces(
        marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')),
        selector=dict(mode='markers')
    )

    botones = create_state_scatter_buttons(df, preguntas, estados, lookup)

    fig.update_layout(
        updatemenus=[
            {
                'buttons': botones,
                'direction': 'down',
                'showactive': True,
                'x': 0.37,
                'xanchor': 'left',
                'y': 1.1,
                'yanchor': 'top',
                'bgcolor': '#f8f9fa',
                'borderwidth': 1
            }
        ],
        annotations=[
            dict(
                text="Select State:",
                x=0,
                xref="paper",
                y=1.09,
                yref="paper",
                align="left",
                showarrow=False
            )
        ]
    )

    return fig


def create_scatter_dropdown_buttons(df, preguntas, lookup):
    """Crea botones para el dropdown del scatter plot"""
    botones = []
    for pregunta in preguntas:
        customdata = [
            _customdata_for(iso, pregunta, answer, lookup)
            for iso, answer in zip(df['iso'], df[pregunta])
        ]
        botones.append({
            'method': 'update',
            'label': pregunta,
            'args': [
                {
                    'x': [df[pregunta]],
                    'customdata': [customdata],
                    'title': f'',
                    'labels': {'State': 'País', pregunta: 'Respuesta'}
                }
            ]
        })
    return botones


def create_state_scatter_buttons(df_uof, preguntas_uof, estados, lookup):
    """Crea botones para el dropdown de estados"""
    botones = []
    for estado in estados:
        df_estado = df_uof[df_uof['State'] == estado]
        df_melted_estado = df_estado.melt(
            id_vars=['State', 'iso'],
            value_vars=preguntas_uof,
            var_name='Question',
            value_name='Response'
        )

        customdata = [
            _customdata_for(iso, question, answer, lookup)
            for iso, question, answer in zip(
                df_melted_estado['iso'], df_melted_estado['Question'], df_melted_estado['Response']
            )
        ]

        botones.append({
            'method': 'update',
            'label': estado,
            'args': [
                {
                    'x': [df_melted_estado['Response']],
                    'y': [df_melted_estado['Question']],
                    'customdata': [customdata],
                    'hover_data': [[estado] * len(df_melted_estado)]
                },
                {'title': f'Responses for {estado}'}
            ]
        })
    return botones