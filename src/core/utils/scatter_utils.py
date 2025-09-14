# scatter plot utils
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go


def create_uof_scatter_figure(df, preguntas):
    """Crea scatter plot para Use of Force"""
    fig = px.scatter(
        df,
        y='State',
        x=preguntas[0],
        hover_data=['iso'],
        title=f'',
        labels={'State': 'Country', preguntas[0]: 'Response'}
    )

    fig.update_layout(
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis={'categoryorder': 'total ascending'},
        margin=dict(l=100, r=50, t=50, b=100),
        height=800
    )

    botones = create_scatter_dropdown_buttons(df, preguntas)

    fig.update_layout(
        updatemenus=[{
            'buttons': botones,
            'direction': 'down',
            'showactive': True,
            'x': 0.1,
            'xanchor': 'left',
            'y': 1.35,
            'yanchor': 'top'
        }]
    )

    return fig


def create_by_state_scatter_figure(df, preguntas, estados):
    """Crea scatter plot por estado para Use of Force"""
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
        # color='Question',
        title=f'Responses for {estado_inicial}',
        labels={'Response': 'Response Value', 'Question': 'Question'},
        height=600,
        hover_data=['State']
    )

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

    botones = create_state_scatter_buttons(df, preguntas, estados)

    fig.update_layout(
        updatemenus=[
            {
                'buttons': botones,
                'direction': 'down',
                'showactive': True,
                'x': 0.37,
                'xanchor': 'left',
                'y': 1.13,
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
                y=1.1,
                yref="paper",
                align="left",
                showarrow=False
            )
        ]
    )

    return fig


def create_scatter_dropdown_buttons(df, preguntas):
    """Crea botones para el dropdown del scatter plot"""
    botones = []
    for pregunta in preguntas:
        botones.append({
            'method': 'update',
            'label': pregunta,
            'args': [
                {'x': [df[pregunta]],
                 'title': f'',
                 'labels': {'State': 'País', pregunta: 'Respuesta'}}
            ]
        })
    return botones


def create_state_scatter_buttons(df_uof, preguntas_uof, estados):
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

        botones.append({
            'method': 'update',
            'label': estado,
            'args': [
                {'x': [df_melted_estado['Response']],
                 'y': [df_melted_estado['Question']],
                 'hover_data': [[estado] * len(df_melted_estado)]},
                {'title': f'Responses for {estado}'}
            ]
        })
    return botones