# sunburst plot utils
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px


def create_uofq8_sunburst_figure(df_force, df_nato):

    merged_df = pd.merge(df_force, df_nato, on='iso', how='inner')
    valid_answers = ['Yes', 'No', 'Silent', 'Ambiguous']
    ## replace 15 with the correct column index if needed
    key_question_col = df_force.columns[15]

    filtered_df = merged_df[merged_df[key_question_col].isin(valid_answers)]

    df = filtered_df[['NATO (Y/N)', key_question_col, 'iso']].copy()

    fig = go.Figure(go.Sunburst(
        ids=[df['NATO (Y/N)'], df[key_question_col], df['iso']],
        labels=[df['NATO (Y/N)'], df[key_question_col], df['iso']],
        parents=[df['NATO (Y/N)'], df[key_question_col], df['iso']],
    ))
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    return fig
