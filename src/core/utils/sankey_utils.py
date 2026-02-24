# sankey utils
import pandas as pd
import plotly.graph_objects as go
import matplotlib.colors as mcolors
import random
import numpy as np
import re
# def create_sankey_figure(df):
#     """Crea la figura completa del Sankey de Use of Force"""
#     sankey_traces, target_columns = create_sankey_data(df)
#
#     fig = go.Figure(data=sankey_traces)
#     fig.update_layout(
#         title={
#             'text': "STATE RESPONSES ON USE OF FORCE",
#             'y': 0.95,
#             'x': 0.5,
#             'xanchor': 'center',
#             'yanchor': 'top',
#             'font': {'size': 18}
#         },
#         font={'size': 12},
#         height=700,
#         width=1200,
#         margin={'l': 50, 'r': 50, 'b': 100, 't': 100, 'pad': 10},
#         plot_bgcolor='white',
#         updatemenus=[create_sankey_dropdown_menu(target_columns)],
#     )
#     return fig

def create_sankey_figure(df_main, df_citations):

    # 1️⃣ Preparar y unir hojas
    df_long = prepare_merged_dataframe(df_main, df_citations)

    # 2️⃣ Crear Sankey con citas
    sankey_traces, target_columns = create_sankey_data(df_long)

    fig = go.Figure(data=sankey_traces)

    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Arial",
            font_color="black",
            bordercolor="#333333"
            ),
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
        updatemenus=[create_sankey_dropdown_menu(target_columns)],
    )

    return fig


def create_sankey_data(df_long):
    """Prepara datos para el Sankey con citas integradas"""

    origin_state = 'iso'
    target_columns = df_long['Question_clean'].unique()

    sankey_traces = []

    for i, target in enumerate(target_columns):

        df_filtered = df_long[df_long['Question_clean'] == target]

        df_grouped = (
            df_filtered
            .groupby([origin_state, 'Answer'])
            .agg(
                value=('iso', 'size'),
                citation=('Citation', lambda x: wrap_text('; '.join(x.unique()), 60))
            )
            .reset_index()
        )

        df_grouped.columns = ['source', 'target', 'value', 'citation']

        unique_labels = pd.unique(
            df_grouped[['source', 'target']].values.ravel('K')
        )

        mapping_dict = {k: v for v, k in enumerate(unique_labels)}

        node_config = {
            'pad': 30,
            'thickness': 15,
            'line': {'color': 'black', 'width': 0.5},
            'label': unique_labels,
            'color': '#1f77b4'
        }

        link_config = {
            'source': df_grouped['source'].map(mapping_dict),
            'target': df_grouped['target'].map(mapping_dict),
            'value': df_grouped['value'],
            'color': 'rgba(150,150,150,0.3)',
            'customdata': df_grouped['citation'],
            'hovertemplate': (
                '<b>%{source.label} → %{target.label}</b><br><br>'
                '<b>Responses:</b> %{value}<br><br>'
                '<b>Citation:</b><br>%{customdata}'
                '<extra></extra>'
            )
        }

        sankey_traces.append(
            go.Sankey(
                arrangement="perpendicular",
                node=node_config,
                link=link_config,
                visible=(i == 0)
            )
        )

    return sankey_traces, target_columns

# def create_sankey_data(df):
#     """Prepara datos para el Sankey de Use of Force"""
#     column_names = list(df.columns)
#     origin_state = 'State'
#     num_col = len(df.columns)
#     final_index = num_col + 1
#     target_columns = column_names[2:final_index]
#
#     sankey_traces = []
#
#     for i, target in enumerate(target_columns):
#         df_grouped = df.groupby([origin_state, target])['iso'].count().reset_index()
#         df_grouped.columns = ['source', 'target', 'value']
#         unique_labels = pd.unique(df_grouped[['source', 'target']].values.ravel('K'))
#         mapping_dict = {k: v for v, k in enumerate(unique_labels)}
#
#         node_config = {
#             'pad': 30,
#             'thickness': 15,
#             'line': {'color': 'black', 'width': 0.5},
#             'label': unique_labels,
#             'color': '#1f77b4'
#         }
#         link_config = {
#             'source': df_grouped['source'].map(mapping_dict),
#             'target': df_grouped['target'].map(mapping_dict),
#             'value': df_grouped['value'],
#             'color': 'rgba(150, 150, 150, 0.3)'
#         }
#         sankey_traces.append(
#             go.Sankey(
#                 arrangement="perpendicular",
#                 node=node_config,
#                 link=link_config,
#                 visible=(i == 0)
#             )
#         )
#     return sankey_traces, target_columns

def prepare_merged_dataframe(df_main, df_citations):

    # Asegurar que no haya columnas duplicadas
    df_main = df_main.loc[:, ~df_main.columns.duplicated()]

    # Columnas de preguntas (todo excepto State e ISO)
    question_columns = [
        col for col in df_main.columns
        if col not in ['State', 'iso']
    ]

    # Pasar main a formato largo
    df_long = df_main.melt(
        id_vars=['State', 'iso'],
        value_vars=question_columns,
        var_name='Question',
        value_name='Answer'
    )

    # Limpiar preguntas en ambas hojas
    df_long['Question_clean'] = df_long['Question'].apply(clean_question)
    df_citations['Question_clean'] = df_citations['Question'].apply(clean_question)

    # Normalizar texto por seguridad
    df_long['Answer'] = df_long['Answer'].str.strip().str.lower()
    df_citations['Answer'] = df_citations['Answer'].str.strip().str.lower()

    # Merge por ISO + Question + Answer
    df_long = df_long.merge(
        df_citations[['iso', 'Question_clean', 'Answer', 'Citation']],
        on=['iso', 'Question_clean', 'Answer'],
        how='left'
    )

    df_long['Citation'] = df_long['Citation'].fillna("No citation available")

    return df_long


def create_issue_demscore_sankey_figure(df_issue, df_dem):
    """Crea la figura completa del Sankey de Use of Force vs Democracy Score"""
    num_col = len(df_issue.columns)
    final_index = num_col + 1
    target_columns = list(df_issue.columns[2:final_index])
    sankey_figs = create_issue_demscore_sankey_data(df_issue, df_dem, target_columns)

    fig = go.Figure(data=sankey_figs)
    buttons = create_demscore_sankey_buttons(target_columns)

    fig.update_layout(
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

    return fig


def create_issue_demscore_sankey_data(df_issue, df_dem, target_columns):
    """Prepara datos para el Sankey de Use of Force vs Democracy Score"""
    sankey_figs = []

    for question in target_columns:
        merged_df = pd.merge(
            df_issue,
            df_dem[['iso', 'dem_score']],
            on='iso',
            how='inner'
        ).dropna()

        if merged_df.empty:
            continue

        bins = [0, 2, 4, 5, 6, 7, 8, 9, 10]
        labels = ['[0-2)', '[2-4)', '[4-5)', '[5-6)', '[6-7)', '[7-8)', '[8-9)', '[9-10]']
        merged_df['score_range'] = pd.cut(
            merged_df['dem_score'],
            bins=bins,
            right=False,
            labels=labels
        )
        merged_df.loc[merged_df['dem_score'] == 10, 'score_range'] = '[9-10]'

        countries = merged_df['iso'].unique().tolist()
        ranges = sorted(merged_df['score_range'].unique().tolist())
        responses = merged_df[question].unique().tolist()

        nodes = countries + ranges + responses
        node_indices = {node: idx for idx, node in enumerate(nodes)}

        links = []

        stage1_counts = merged_df.groupby(['iso', 'score_range']).size().reset_index(name='count')
        for _, row in stage1_counts.iterrows():
            links.append({
                'source': node_indices[row['iso']],
                'target': node_indices[row['score_range']],
                'value': row['count']
            })

        stage2_counts = merged_df.groupby(['score_range', question]).size().reset_index(name='count')
        for _, row in stage2_counts.iterrows():
            links.append({
                'source': node_indices[row['score_range']],
                'target': node_indices[row[question]],
                'value': row['count']
            })

        fig = go.Sankey(
            arrangement="perpendicular",
            node=dict(
                pad=25,
                thickness=20,
                line=dict(color='black', width=0.5),
                label=nodes,
                color=['#1f77b4'] * len(countries) +
                      ['#ff7f0e'] * len(ranges) +
                      ['#2ca02c'] * len(responses)
            ),
            link=dict(
                source=[link['source'] for link in links],
                target=[link['target'] for link in links],
                value=[link['value'] for link in links],
                color='rgba(150, 150, 150, 0.3)'
            ),
            visible=(question == target_columns[0])
        )

        sankey_figs.append(fig)

    return sankey_figs


def create_sankey_dropdown_menu(target_columns):
    """Crea el menú desplegable para los Sankeys"""
    return {
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
    }


def create_demscore_sankey_buttons(target_columns):
    """Crea los botones para el Sankey de Democracy Score"""
    buttons = []
    for i, question in enumerate(target_columns):
        visibility = [False] * len(target_columns)
        visibility[i] = True
        buttons.append(dict(
            args=[{'visible': visibility}],
            label=question,
            method="update"
        ))
    return buttons


def create_uof_art51_nato_sankey(df_force, df_nato):
    ## generates the colors randomly for each Iso
    def rgba_str(color, alpha=0.5):
        r, g, b = mcolors.to_rgb(color)
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        return f'rgba({r},{g},{b},{alpha})'

    ## clean spaces and capitalization
    df_nato.columns = df_nato.columns.str.strip().str.capitalize()
    df_force.columns = df_force.columns.str.strip().str.capitalize()

    ## map y and n from Nato (y/n) column
    df_nato["Nato (y/n)"] = df_nato["Nato (y/n)"].map({"Y": "NATO", "N": "Non-NATO"})

    ## merge the datasets
    merged_df = pd.merge(df_force, df_nato, on='Iso', how='inner')

    ## define responses hard coded column to look at
    valid_answers = ['Yes', 'No', 'Silent', 'Ambiguous']
    key_question = df_force.columns[15]

    ## nodes for each step
    countries = merged_df['Iso'].unique().tolist()
    nato_status = sorted(merged_df['Nato (y/n)'].unique().tolist())
    responses = valid_answers
    nodes = countries + nato_status + responses
    node_indices = {node: idx for idx, node in enumerate(nodes)}

    ## this brings in the color def assign a unique color to each country
    color_palette = list(mcolors.TABLEAU_COLORS.values())
    random.shuffle(color_palette)
    country_colors = {
        country: color_palette[i % len(color_palette)]
        for i, country in enumerate(countries)
    }

    ## group stages instead stage 1 and stage 2 data
    stage1 = merged_df.groupby(['Iso', 'Nato (y/n)']).size().reset_index(name='count')
    stage2 = merged_df.groupby(['Iso', 'Nato (y/n)', key_question]).size().reset_index(name='count')

    ## build links using merged columns and color def
    def build_links(highlight_country):
        links = []
        for _, row in stage1.iterrows():
            alpha = 1.0 if row['Iso'] == highlight_country else 0.15
            links.append(dict(
                source=node_indices[row['Iso']],
                target=node_indices[row['Nato (y/n)']],
                value=row['count'],
                color=rgba_str(country_colors[row['Iso']], alpha)
            ))
        for _, row in stage2.iterrows():
            if row[key_question] in valid_answers:
                alpha = 1.0 if row['Iso'] == highlight_country else 0.15
                links.append(dict(
                    source=node_indices[row['Nato (y/n)']],
                    target=node_indices[row[key_question]],
                    value=row['count'],
                    color=rgba_str(country_colors[row['Iso']], alpha)
                ))
        return links

    ## defaults to first country should be interactive
    default_country = countries[0]
    links = build_links(default_country)

    sankey_links = dict(
        source=[l['source'] for l in links],
        target=[l['target'] for l in links],
        value=[l['value'] for l in links],
        color=[l['color'] for l in links]
    )

    fig = go.Figure(data=[go.Sankey(
        # arrangement="snap",
        node=dict(
            pad=20,
            thickness=20,
            line=dict(color="blue", width=0.5),
            label=nodes,
            color="gold"
        ),
        link=sankey_links
    )])

    ## creates the dropdown menu will substitute name of country into title based on chosen selection
    buttons = []
    for country in countries:
        new_links = build_links(country)
        buttons.append(dict(
            label=country,
            method="update",
            args=[{"link": dict(
                source=[l['source'] for l in new_links],
                target=[l['target'] for l in new_links],
                value=[l['value'] for l in new_links],
                color=[l['color'] for l in new_links]
            )},
                {"title": f"Statement on Article 51 by {country}"}]
        ))
    fig.update_layout(
        title=f"Statement on Article 51 by {default_country}",
        font_size=12,
        updatemenus=[dict(
            active=0,
            buttons=buttons,
            direction="down",
            showactive=True,
            x=1.05,
            xanchor="left",
            y=1,
            yanchor="top"
        )]
    )
    return fig


def clean_question(text):
    """
    Limpia prefijos
    """
    if pd.isna(text):
        return text
    # 1️⃣ eliminar número inicial
    text = re.sub(r'^\s*\d+\s*', '', text)
    # 2️⃣ eliminar todos los bloques tipo (algo) al inicio
    text = re.sub(r'^(\s*\([^)]+\))+', '', text)
    # 3️⃣ eliminar puntuación residual al inicio
    text = re.sub(r'^\s*[\.\:\-\–]+\s*', '', text)
    text = text.strip().lower()
    # 4️⃣ capitalizar primera letra
    if text:
        text = text[0].upper() + text[1:]

    return text

import textwrap

def wrap_text(text, width=60):
    if pd.isna(text):
        return text
    return "<br>".join(textwrap.wrap(text, width=width))