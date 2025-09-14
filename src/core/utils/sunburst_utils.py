# sunburst plot utils
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px


def create_uofq8_sunburst_figure(df_force, df_nato):
    ## clear extra spaces and capitalization differences
    df_nato.columns = df_nato.columns.str.strip().str.capitalize()
    df_force.columns = df_force.columns.str.strip().str.capitalize()

    ## merge on key column
    merged_df = pd.merge(df_force, df_nato, on='Iso', how='inner')

    ## define answers for Question 8
    valid_answers = ['Yes', 'No', 'Silent', 'Ambiguous']

    ## replace 15 with the correct column index if needed
    column_index = 15
    key_question_col = df_force.columns[column_index]

    ## keep set of answers
    filtered_df = merged_df[merged_df[key_question_col].isin(valid_answers)]

    ## prepare data for sunburst: NATO → Question → ISO
    df = filtered_df[['Nato (y/n)', key_question_col, 'Iso']].copy()

    ## count each row as 1 to be aggregatable
    df['Count'] = 1

    ## build the sunburst -- drillable pie chart
    fig = px.sunburst(
        df,
        path=['Nato (y/n)', key_question_col, 'Iso'],  ## NATO → Question → ISO
        values='Count',
        branchvalues="total",
        maxdepth=3
    )

    fig.update_traces(textinfo="label")
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10))
    return fig
