import plotly.express as px
from django.shortcuts import render
import plotly.graph_objects as go
import pandas as pd
from nat_state_vis_app import settings


# Create your views here.
def home(request):
    return render(request, 'core/home.html')


def use_of_force(request):
    return render(request, 'core/uof.html')


def sovereignty(request):
    return render(request, 'core/sovereignty.html')


def uof_sankey(request):
    # Cargar los datos
    uof_data = settings.BASE_DIR / 'data' / 'uof-aug2025.csv'
    df = pd.read_csv(uof_data)

    column_names = list(df.columns)
    origin_state = 'State'
    target_columns = column_names[2:18]  # Columnas desde Q2 hasta Q17

    sankey_traces = []

    for i, target in enumerate(target_columns):
        # Procesamiento de datos
        df_grouped = df.groupby([origin_state, target])['ISO'].count().reset_index()
        df_grouped.columns = ['source', 'target', 'value']

        # Etiquetas únicas
        unique_labels = pd.unique(df_grouped[['source', 'target']].values.ravel('K'))

        # Mapeo de índices
        mapping_dict = {k: v for v, k in enumerate(unique_labels)}

        # Configuración del nodo
        node_config = {
            'pad': 30,
            'thickness': 15,
            'line': {'color': 'black', 'width': 0.5},
            'label': unique_labels,
            'color': '#1f77b4'  # Color azul para los nodos
        }

        # Configuración del enlace
        link_config = {
            'source': df_grouped['source'].map(mapping_dict),
            'target': df_grouped['target'].map(mapping_dict),
            'value': df_grouped['value'],
            'color': 'rgba(150, 150, 150, 0.3)'  # Enlaces semi-transparentes
        }

        # Crear el trazado Sankey
        sankey_traces.append(
            go.Sankey(
                arrangement="perpendicular",
                node=node_config,
                link=link_config,
                visible=(i == 0)  # Solo el primero visible inicialmente
            )
        )

    # Configuración del layout
    fig = go.Figure(data=sankey_traces)

    fig.update_layout(
        title={
            'text': "STATE RESPONSES ON USE OF FORCE",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 18}
        },
        font={'size': 12},
        height=700,
        width=1200,
        margin={'l': 50, 'r': 50, 'b': 100, 't': 100, 'pad': 10},
        plot_bgcolor='white',
        updatemenus=[{
            'buttons': [
                {
                    'args': [{'visible': [j == i for j in range(len(target_columns))]}],
                    'label': target,
                    'method': 'update'
                } for i, target in enumerate(target_columns)
            ],
            'direction': 'down',
            'showactive': True,
            'x': 0.5,
            'xanchor': 'center',
            'y': 1.25,
            'yanchor': 'top',
            'bgcolor': 'white',
            'bordercolor': '#cccccc',
            'borderwidth': 1
        }]
    )
    # Generación del HTML con configuración responsive
    sankey_html = fig.to_html(
        full_html=False,
        config={
            'responsive': True,
            'displayModeBar': True
        },
        include_plotlyjs='cdn'
    )
    # Contenedor con estilos optimizados
    sankey_html = f"""
    <div style="
        width: 100%;
        overflow: auto;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        padding: 20px;
    ">
        {sankey_html}
    </div>
    """
    return render(request, 'core/uof_sankey.html', {'uof_sankey': sankey_html})


def uof_demscore_sankey(request):
    # 1. Cargar todos los datos
    uof_data = settings.BASE_DIR / 'data' / 'uof-aug2025.csv'
    dem_score_data = settings.BASE_DIR / 'data' / 'democracy-index-eiu.csv'

    # Leer datos de uso de fuerza
    df_uof = pd.read_csv(uof_data)
    column_names = list(df_uof.columns)
    target_columns = column_names[2:18]  # Columnas Q2-Q17

    # Leer y procesar datos de democracia
    df_dem = pd.read_csv(dem_score_data)
    df_dem = df_dem.rename(columns={'Year': 'year', 'Code': 'iso', 'Democracy score': 'dem_score'})
    df_uof = df_uof.rename(columns={'ISO': 'iso'})
    most_recent_year = df_dem['year'].max()
    df_dem = df_dem[df_dem['year'] == most_recent_year]

    # 2. Preparar todos los Sankeys para cada pregunta
    sankey_figs = []

    for question in target_columns:
        # Merge de datos para esta pregunta
        merged_df = pd.merge(
            df_uof,
            df_dem[['iso', 'dem_score']],
            on='iso',
            how='inner'
        ).dropna()

        if merged_df.empty:
            continue  # Saltar si no hay datos

        # Crear rangos de democracia
        bins = [0, 2, 4, 5, 6, 7, 8, 9, 10]
        labels = ['[0-2)', '[2-4)', '[4-5)', '[5-6)', '[6-7)', '[7-8)', '[8-9)', '[9-10]']
        merged_df['score_range'] = pd.cut(
            merged_df['dem_score'],
            bins=bins,
            right=False,
            labels=labels
        )
        merged_df.loc[merged_df['dem_score'] == 10, 'score_range'] = '[9-10]'

        # Preparar nodos y enlaces
        countries = merged_df['iso'].unique().tolist()
        ranges = sorted(merged_df['score_range'].unique().tolist())
        responses = merged_df[question].unique().tolist()

        nodes = countries + ranges + responses
        node_indices = {node: idx for idx, node in enumerate(nodes)}

        # Crear enlaces
        links = []

        # Etapa 1: País → Rango de democracia
        stage1_counts = merged_df.groupby(['iso', 'score_range']).size().reset_index(name='count')
        for _, row in stage1_counts.iterrows():
            links.append({
                'source': node_indices[row['iso']],
                'target': node_indices[row['score_range']],
                'value': row['count']
            })

        # Etapa 2: Rango → Respuesta
        stage2_counts = merged_df.groupby(['score_range', question]).size().reset_index(name='count')
        for _, row in stage2_counts.iterrows():
            links.append({
                'source': node_indices[row['score_range']],
                'target': node_indices[row[question]],
                'value': row['count']
            })

        # Crear figura Sankey para esta pregunta
        fig = go.Sankey(
            arrangement="perpendicular",
            node=dict(
                pad=25,
                thickness=20,
                line=dict(color='black', width=0.5),
                label=nodes,
                color=['#1f77b4'] * len(countries) +  # Azul países
                      ['#ff7f0e'] * len(ranges) +  # Naranja rangos
                      ['#2ca02c'] * len(responses)  # Verde respuestas
            ),
            link=dict(
                source=[link['source'] for link in links],
                target=[link['target'] for link in links],
                value=[link['value'] for link in links],
                color='rgba(150, 150, 150, 0.3)'
            ),
            visible=(question == target_columns[0])  # Solo primera visible
        )

        sankey_figs.append(fig)

    # 3. Crear figura final con todos los Sankeys
    fig = go.Figure(data=sankey_figs)

    # Configurar menú desplegable
    buttons = []
    for i, question in enumerate(target_columns):
        visibility = [False] * len(target_columns)
        visibility[i] = True

        buttons.append(
            dict(
                args=[{'visible': visibility},
                      # {'title': f"Country → Democracy Score → {question}"}
                      ],
                label=question,
                method="update"
            )
        )

    fig.update_layout(
        # title_text=f"Country → Democracy Score → {target_columns[0]}",
        font_size=12,
        height=800,
        width=1200,
        margin=dict(l=50, r=50, b=100, t=100, pad=20),
        plot_bgcolor='white',
        updatemenus=[{
            'buttons': buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.5,
            'xanchor': 'center',
            'y': 1.15,
            'yanchor': 'top',
            'bgcolor': 'white',
            'bordercolor': '#cccccc',
            'borderwidth': 1
        }]
    )

    # 4. Generar HTML
    sankey_html = fig.to_html(
        full_html=False,
        config={
            'responsive': True,
            'displayModeBar': True
        },
        include_plotlyjs='cdn'
    )

    # Contenedor con estilos
    sankey_html = f"""
    <div style="
        width: 100%;
        overflow: auto;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        padding: 20px;
        margin-bottom: 20px;
    ">
        {sankey_html}
    </div>
    """

    return render(request, 'core/uof_demscore_sankey.html', {
        'uof_demscore_sankey': sankey_html
    })


def uof_scatter(request):
    # 1. Cargar todos los datos
    uof_data = settings.BASE_DIR / 'data' / 'uof-aug2025.csv'
    # Leer datos de uso de fuerza
    df = pd.read_csv(uof_data)
    column_names = list(df.columns)
    preguntas = column_names[2:18]

    fig = px.scatter(
        df,
        y='State',  # Nombre del país (ahora en eje Y)
        x=preguntas[0],  # Primera pregunta por defecto (ahora en eje X)
        hover_data=['ISO'],  # Mostrar código ISO al pasar el mouse
        title=f'',
        labels={'State': 'Country', preguntas[0]: 'Response'}
    )

    # Personalizar diseño
    fig.update_layout(
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis={'categoryorder': 'total ascending'},
        margin=dict(l=100, r=50, t=50, b=100),  # Ajustar márgenes
        height=800
    )

    # Crear botones para el dropdown
    botones = []
    for pregunta in preguntas:
        botones.append({
            'method': 'update',
            'label': pregunta,
            'args': [
                {'x': [df[pregunta]],  # Ahora actualizamos el eje X en lugar del Y
                 'title': f'',
                 'labels': {'State': 'País', pregunta: 'Respuesta'}}
            ]
        })

    # Añadir dropdown menu
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
    # Convertir figura a HTML para Django
    plot_div = fig.to_html()
    return render(request, 'core/uof_scatter.html', {'uof_scatter': plot_div})


# Scatter plot of countries and responses with countries on x axis
# def uof_scatter(request):
#     # 1. Cargar todos los datos
#     uof_data = settings.BASE_DIR / 'data' / 'uof-aug2025.csv'
#     # Leer datos de uso de fuerza
#     df = pd.read_csv(uof_data)
#     column_names = list(df.columns)
#     preguntas = column_names[2:18]
#
#     fig = px.scatter(
#         df,
#         x='State',  # Nombre del país
#         y=preguntas[0],  # Primera pregunta por defecto
#         hover_data=['ISO'],  # Mostrar código ISO al pasar el mouse
#         title=f'',
#         labels={'State': 'Country', preguntas[0]: 'Response'}
#     )
#
#     # Personalizar diseño
#     fig.update_layout(
#         hovermode='closest',
#         plot_bgcolor='rgba(0,0,0,0)',
#         xaxis={'categoryorder': 'total descending'}
#     )
#
#     # Crear botones para el dropdown
#     botones = []
#     for pregunta in preguntas:
#         botones.append({
#             'method': 'update',
#             'label': pregunta,
#             'args': [
#                 {'y': [df[pregunta]],  # Actualizar eje Y
#                  'title': f'',
#                  'labels': {'State': 'País', pregunta: 'Respuesta'}}
#             ]
#         })
#
#     # Añadir dropdown menu
#     fig.update_layout(
#         updatemenus=[{
#             'buttons': botones,
#             'direction': 'down',
#             'showactive': True,
#             'x': 0.1,
#             'xanchor': 'left',
#             'y': 1.35,
#             'yanchor': 'top'
#         }]
#     )
#     # Convertir figura a HTML para Django
#     plot_div = fig.to_html()
#     return render(request, 'core/uof_scatter.html', {'uof_scatter': plot_div})


def uof_by_state_scatter(request):
    # 1. Cargar todos los datos
    uof_data = settings.BASE_DIR / 'data' / 'uof-aug2025.csv'
    df_uof = pd.read_csv(uof_data)
    uof_column_names = list(df_uof.columns)
    preguntas_uof = uof_column_names[2:18]
    estados = df_uof['State'].unique()

    # Crear figura inicial con el primer estado
    estado_inicial = estados[0]
    df_filtrado = df_uof[df_uof['State'] == estado_inicial]

    # Transformar los datos para mostrar todas las preguntas
    df_melted = df_filtrado.melt(id_vars=['State', 'ISO'], value_vars=preguntas_uof,
                                 var_name='Question', value_name='Response')

    fig = px.scatter(
        df_melted,
        x='Response',
        y='Question',
        color='Question',
        title=f'Responses for {estado_inicial}',
        labels={'Response': 'Response Value', 'Question': 'Question'},
        height=600,
        hover_data=['State']  # Mostrar estado en tooltip
    )

    # Personalizar diseño
    fig.update_layout(
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis={'categoryorder': 'total descending'},
        margin=dict(l=150, r=50, t=80, b=100),  # Más margen izquierdo para preguntas largas
        showlegend=False,
        transition={'duration': 500}  # Animación suave
    )

    # Mejorar visualización de puntos
    fig.update_traces(
        marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')),
        selector=dict(mode='markers')
    )

    # Crear botones para el dropdown de estados
    botones = []
    for estado in estados:
        df_estado = df_uof[df_uof['State'] == estado]
        df_melted_estado = df_estado.melt(
            id_vars=['State', 'ISO'],
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

    # Añadir dropdown menu para estados
    fig.update_layout(
        updatemenus=[
            {
                'buttons': botones,
                'direction': 'down',
                'showactive': True,
                'x': 0.3,
                'xanchor': 'left',
                'y': 1.15,
                'yanchor': 'top',
                'bgcolor': '#f8f9fa',  # Fondo claro para el dropdown
                'borderwidth': 1
            }
        ]
    )

    # Añadir anotaciones para mejor contexto
    fig.update_layout(
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

    # Convertir figura a HTML para Django
    plot_div = fig.to_html(full_html=False, config={'responsive': True})
    return render(request, 'core/uof_by_state_scatter.html', {
        'uof_by_state_scatter': plot_div,
        'states_count': len(estados),
        'questions_count': len(preguntas_uof)
    })


def uof_sov_parallel_categories(request):
    # 1. Cargar los datos
    uof_data = settings.BASE_DIR / 'data' / 'uof-aug2025.csv'
    sovereignty_data = settings.BASE_DIR / 'data' / 'sovereignty-aug2025.csv'
    df_uof = pd.read_csv(uof_data)
    df_sov = pd.read_csv(sovereignty_data)

    # Obtener nombres de columnas
    questions_uof = list(df_uof.columns[2:18])  # Q2-Q17
    questions_sov = list(df_sov.columns[2:35])

    # 2. Crear una sola traza con la primera combinación
    fig = go.Figure()

    # Solo una traza inicial
    fig.add_trace(go.Parcats(
        dimensions=[
            {'label': 'Country', 'values': df_uof['State']},
            {'label': questions_uof[0], 'values': df_uof[questions_uof[0]]},
            {'label': questions_sov[1], 'values': df_sov[questions_sov[1]]}
        ],
        line={'color': df_uof.index, 'colorscale': 'Viridis'},
        arrangement='freeform'
    ))

    # 3. Menús desplegables optimizados
    buttons_q1 = []
    for i, q1 in enumerate(questions_uof):
        buttons_q1.append(
            dict(
                args=[{
                    'dimensions[1].label': q1,
                    'dimensions[1].values': [df_uof[q1].tolist()]
                }],
                label=q1,
                method="restyle"
            )
        )

    buttons_q2 = []
    for j, q2 in enumerate(questions_sov):
        buttons_q2.append(
            dict(
                args=[{
                    'dimensions[2].label': q2,
                    'dimensions[2].values': [df_sov[q2].tolist()]
                }],
                label=q2,
                method="restyle"
            )
        )

    # 4. Configurar layout
    fig.update_layout(
        # title='',
        font_size=12,
        height=800,
        width=1200,
        margin=dict(l=50, r=50, b=100, t=100, pad=20),
        plot_bgcolor='white',
        updatemenus=[
            {
                'buttons': buttons_q1,
                'direction': 'down',
                'showactive': True,
                'x': 0.05,
                'xanchor': 'left',
                'y': 1.25,
                'yanchor': 'top',
                'bgcolor': 'white',
                'bordercolor': '#cccccc',
                'borderwidth': 1,
                # 'title': 'Select Question 1 (Use of Force):'
            },
            {
                'buttons': buttons_q2,
                'direction': 'down',
                'showactive': True,
                'x': 0.05,
                'xanchor': 'left',
                'y': 1.15,
                'yanchor': 'top',
                'bgcolor': 'white',
                'bordercolor': '#cccccc',
                'borderwidth': 1,
                # 'title': 'Select Question 2 (Sovereignty):'
            }
        ]
    )

    # 5. Generar HTML
    plot_html = fig.to_html(
        full_html=False,
        config={'responsive': True, 'displayModeBar': True},
        include_plotlyjs='cdn'
    )

    plot_html = f"""
    <div style="
        width: 100%;
        overflow: auto;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        padding: 20px;
        margin-bottom: 20px;
    ">
        {plot_html}
    </div>
    """
    return render(request, 'core/uof_sov_parallel_categories.html', {
        'uof_sov_parallel_categories': plot_html
    })
# def uof_sov_parallel_categories(request):
#     # 1. Cargar los datos
#     uof_data = settings.BASE_DIR / 'data' / 'uof-aug2025.csv'
#     sovereignty_data = settings.BASE_DIR / 'data' / 'sovereignty-aug2025.csv'
#     df_uof = pd.read_csv(uof_data)
#     df_sov = pd.read_csv(sovereignty_data)
#
#     # Obtener nombres de columnas (preguntas)
#     uof_column_names = list(df_uof.columns)
#     sov_column_names = list(df_sov.columns)
#     questions_uof = uof_column_names[2:18]  # Columnas Q2-Q17
#     questions_sov = sov_column_names[2:35]
#
#     # 2. Preparar los datos para el diagrama
#     # Crear una copia del dataframe para no modificar el original
#     plot_df_uof = df_uof.copy()
#     plot_df_sov = df_sov.copy()
#
#     # 3. Crear la figura con categorías paralelas
#     fig = go.Figure()
#
#     # Añadir trazas para cada combinación de preguntas (inicialmente invisibles)
#     for i, q1 in enumerate(questions_uof):
#         for j, q2 in enumerate(questions_sov):
#             visible = (i == 0 and j == 1)  # Solo primera combinación visible inicialmente
#
#             # truncated_q1 = q1[:3] if len(q1) > 3 else q1
#             # truncated_q2 = q2[:3] if len(q2) > 3 else q2
#
#             fig.add_trace(go.Parcats(
#                 dimensions=[
#                     {'label': 'Country', 'values': plot_df_uof['State']},
#                     {'label': 'Question 1', 'values': plot_df_uof[q1]},
#                     {'label': 'Question 2', 'values': plot_df_sov[q2]}
#                 ],
#                 line={'color': plot_df_uof.index, 'colorscale': 'Viridis'},
#                 arrangement='freeform',
#                 visible=visible
#             ))
#
#     # 4. Crear menús desplegables para seleccionar preguntas
#     # Menú para pregunta 1
#     buttons_q1 = []
#     for i, q1 in enumerate(questions_uof):
#         buttons_q1.append(
#             dict(
#                 args=[{'dimensions[1].label': q1,
#                        'dimensions[1].values': [plot_df_uof[q1]] * len(questions_uof)}],
#                 label=q1,
#                 method="restyle"
#             )
#         )
#
#     # Menú para pregunta 2
#     buttons_q2 = []
#     for j, q2 in enumerate(questions_sov):
#         buttons_q2.append(
#             dict(
#                 args=[{'dimensions[2].label': q2,
#                        'dimensions[2].values': [plot_df_sov[q2]] * len(questions_sov)}],
#                 label=q2,
#                 method="restyle"
#             )
#         )
#
#     # 5. Configurar el layout de la figura
#     fig.update_layout(
#         title='',
#         font_size=12,
#         height=800,
#         width=1200,
#         margin=dict(l=50, r=50, b=100, t=100, pad=20),
#         plot_bgcolor='white',
#         updatemenus=[
#             {
#                 'buttons': buttons_q1,
#                 'direction': 'down',
#                 'showactive': True,
#                 'x': 0.25,
#                 'xanchor': 'center',
#                 'y': 1.25,
#                 'yanchor': 'top',
#                 'bgcolor': 'white',
#                 'bordercolor': '#cccccc',
#                 'borderwidth': 1,
#                 'title': 'Select Question 1 from issue area Use of Force:'
#             },
#             {
#                 'buttons': buttons_q2,
#                 'direction': 'down',
#                 'showactive': True,
#                 'x': 0.25,
#                 'xanchor': 'center',
#                 'y': 1.15,
#                 'yanchor': 'top',
#                 'bgcolor': 'white',
#                 'bordercolor': '#cccccc',
#                 'borderwidth': 1,
#                 'title': 'Select Question 2 from issue area Sovereignty:'
#             }
#         ]
#     )
#     # 6. Generar HTML
#     plot_html = fig.to_html(
#         full_html=False,
#         config={
#             'responsive': True,
#             'displayModeBar': True
#         },
#         include_plotlyjs='cdn'
#     )
#
#     # Contenedor con estilos
#     plot_html = f"""
#     <div style="
#         width: 100%;
#         overflow: auto;
#         background: white;
#         border-radius: 8px;
#         box-shadow: 0 2px 10px rgba(0,0,0,0.1);
#         padding: 20px;
#         margin-bottom: 20px;
#     ">
#         {plot_html}
#     </div>
#     """
#
#     return render(request, 'core/uof_sov_parallel_categories.html', {
#         'uof_sov_parallel_categories': plot_html
#     })
