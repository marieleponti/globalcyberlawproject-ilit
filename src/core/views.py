from django.shortcuts import render
import plotly.graph_objects as go
import pandas as pd
from nat_state_vis_app import settings


# Create your views here.
def home(request):
    return render(request, 'core/home.html')


def use_of_force(request):
    return render(request, 'core/uof.html')


import pandas as pd
import plotly.graph_objects as go
from django.conf import settings
from django.shortcuts import render


def sankey_uof(request):
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
            'y': 1.05,
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