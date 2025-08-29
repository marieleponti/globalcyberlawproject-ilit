# utils/sankey_utils.py
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html
from dash.dcc import Input
from dash.html import Output


def create_uof_sankey_figure(df):
    """Crea la figura completa del Sankey de Use of Force"""
    sankey_traces, target_columns = create_uof_sankey_data(df)

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
        updatemenus=[create_sankey_dropdown_menu(target_columns)]
    )

    return fig


def create_uof_sankey_data(df):
    """Prepara datos para el Sankey de Use of Force"""
    column_names = list(df.columns)
    origin_state = 'State'
    target_columns = column_names[2:18]

    sankey_traces = []

    for i, target in enumerate(target_columns):
        df_grouped = df.groupby([origin_state, target])['iso'].count().reset_index()
        df_grouped.columns = ['source', 'target', 'value']

        unique_labels = pd.unique(df_grouped[['source', 'target']].values.ravel('K'))
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
            'color': 'rgba(150, 150, 150, 0.3)'
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


def create_uof_demscore_sankey_figure(df_uof, df_dem):
    """Crea la figura completa del Sankey de Use of Force vs Democracy Score"""
    target_columns = list(df_uof.columns[2:18])
    sankey_figs = create_uof_demscore_sankey_data(df_uof, df_dem, target_columns)

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


def create_uof_demscore_sankey_data(df_uof, df_dem, target_columns):
    """Prepara datos para el Sankey de Use of Force vs Democracy Score"""
    sankey_figs = []

    for question in target_columns:
        merged_df = pd.merge(
            df_uof,
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
    ## clean extra spaces and capitalization differences
    df_nato.columns = df_nato.columns.str.strip().str.capitalize()
    df_force.columns = df_force.columns.str.strip().str.capitalize()

    ## merge on key column
    merged_df = pd.merge(df_force, df_nato, on='Iso', how='inner')

    ## define answers for Q8
    ## hardcode for the specific Q8 column
    valid_answers = ['Yes', 'No', 'Silent', 'Ambiguous']
    key_question = df_force.columns[15]

    ## node labels
    countries = merged_df['Iso'].unique().tolist()
    nato_status = sorted(merged_df['Nato (y/n)'].unique().tolist())
    responses = valid_answers

    nodes = countries + nato_status + responses
    node_indices = {node: idx for idx, node in enumerate(nodes)}

    ## prepare links
    links = []

    ## Stage 1: State → NATO
    stage1_counts = merged_df.groupby(['Iso', 'Nato (y/n)']).size().reset_index(name='count')
    for _, row in stage1_counts.iterrows():
        links.append({
            'source': node_indices[row['Iso']],
            'target': node_indices[row['Nato (y/n)']],
            'value': row['count'],
            'color': 'rgba(100, 149, 237, 0.6)'  # Cornflower blue
        })

    ## Stage 2: NATO → Response to Q8
    stage2_counts = merged_df.groupby(['Nato (y/n)', key_question]).size().reset_index(name='count')
    for _, row in stage2_counts.iterrows():
        if row[key_question] in valid_answers:
            links.append({
                'source': node_indices[row['Nato (y/n)']],
                'target': node_indices[row[key_question]],
                'value': row['count'],
                'color': 'rgba(255, 165, 0, 0.6)'  # Orange
            })

    ## Build Sankey link dict

    ##source is the starting node index of link
    ##target is the ending node index of link
    ## value is the flow size thickness of link
    ## color is the color of link
    sankey_links = dict(
        source=[link['source'] for link in links],
        target=[link['target'] for link in links],
        value=[link['value'] for link in links],
        color=[link['color'] for link in links]
    )

    colors = sankey_links['color'].copy()
    ## -----Actual Dash app portion begins after this
    ##
    ##

    # Dash App
    # app = Dash(__name__)
    #
    # ## top portion of the page
    # ## dropdown will show you which thread is highlighted
    # app.layout = html.Div([
    #     html.H2("Highlightable NATO Question 8 Sankey"),
    #     dcc.Dropdown(
    #         id='highlight-dropdown',
    #         options=[{'label': node, 'value': node} for node in nodes],
    #         placeholder="Select a node to highlight"
    #     ),
    #     dcc.Graph(id='sankey-graph')
    # ])
    #
    # ## app.callback function tells the app that it is interactive
    # ## output and input dictate the figure can be changeable and what changes it, respectively
    # @app.callback(
    #     Output('sankey-graph', 'figure'),
    #     Input('highlight-dropdown', 'value')
    # )
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            label=nodes,
            color="blue"
        ),
        link=dict(
            source=sankey_links['source'],
            target=sankey_links['target'],
            value=sankey_links['value'],
            color=colors
        )
    )])

    ## title
    fig.update_layout(title_text="NATO Countries with Answer to Question 8", font_size=14)
    return fig

    def update_sankey(selected_node):
        # Default link colors
        colors = sankey_links['color'].copy()

        ## this is the highlighting logic of the app
        ## portion that will show red for clicked option in the dropdown
        ## if -> none means that if not clicked, then no change
        ## currently only highlights from stage 1 but not fully
        if selected_node is not None:
            idx = node_indices[selected_node]
            for i, (src, tgt) in enumerate(zip(sankey_links['source'], sankey_links['target'])):
                if src == idx or tgt == idx:
                    colors[i] = 'rgba(255,0,0,0.8)'  # Highlighted red
                else:
                    colors[i] = 'rgba(200,200,200,0.2)'  # Fade others

        ## creates the sankey basically

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                label=nodes,
                color="blue"
            ),
            link=dict(
                source=sankey_links['source'],
                target=sankey_links['target'],
                value=sankey_links['value'],
                color=colors
            )
        )])

        ## title
        fig.update_layout(title_text="NATO Countries with Answer to Question 8", font_size=14)
        return fig

    # if __name__ == '__main__':
    #     app.run(debug=True, port=8051)
