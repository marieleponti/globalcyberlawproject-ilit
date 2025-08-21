# utils/parallel_categories_utils.py
import plotly.graph_objects as go


def create_parallel_categories_figure(df_uof, df_sov, questions_uof, questions_sov):
    """Crea figura de categorías paralelas para UOF vs Sovereignty"""
    fig = go.Figure()

    fig.add_trace(go.Parcats(
        dimensions=[
            {'label': 'Country', 'values': df_uof['State']},
            {'label': questions_uof[0], 'values': df_uof[questions_uof[0]]},
            {'label': questions_sov[1], 'values': df_sov[questions_sov[1]]}
        ],
        line={'color': df_uof.index, 'colorscale': 'Viridis'},
        arrangement='freeform',
        hoverinfo='count+probability',
    ))

    buttons_q1 = create_parallel_categories_buttons_uof(df_uof, questions_uof)
    buttons_q2 = create_parallel_categories_buttons_sov(df_sov, questions_sov)

    fig.update_layout(
        font_size=12,
        height=800,
        width=1200,
        margin=dict(l=50, r=50, b=100, t=100, pad=20),
        plot_bgcolor='white',
        updatemenus=[
            create_parallel_categories_menu(buttons_q1, 0.05, 1.25),
            create_parallel_categories_menu(buttons_q2, 0.05, 1.15)
        ]
    )

    return fig


def create_parallel_categories_buttons_uof(df_uof, questions_uof):
    """Crea botones para las preguntas UOF"""
    buttons = []
    for i, q1 in enumerate(questions_uof):
        buttons.append(
            dict(
                args=[{
                    'dimensions[1].label': q1,
                    'dimensions[1].values': [df_uof[q1].tolist()]
                }],
                label=q1,
                method="restyle"
            )
        )
    return buttons


def create_parallel_categories_buttons_sov(df_sov, questions_sov):
    """Crea botones para las preguntas Sovereignty"""
    buttons = []
    for j, q2 in enumerate(questions_sov):
        buttons.append(
            dict(
                args=[{
                    'dimensions[2].label': q2,
                    'dimensions[2].values': [df_sov[q2].tolist()]
                }],
                label=q2,
                method="restyle"
            )
        )
    return buttons


def create_parallel_categories_menu(buttons, x_position, y_position):
    """Crea menú para categorías paralelas"""
    return {
        'buttons': buttons,
        'direction': 'down',
        'showactive': True,
        'x': x_position,
        'xanchor': 'left',
        'y': y_position,
        'yanchor': 'top',
        'bgcolor': 'white',
        'bordercolor': '#cccccc',
        'borderwidth': 1,
    }