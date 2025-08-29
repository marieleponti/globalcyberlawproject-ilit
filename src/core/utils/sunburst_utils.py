import pandas as pd
import plotly.express as px

# def create_uofq8_sunburst_figure(df_force, df_nato):
#
#     ## clear extra spaces and capitalization differences
#     df_nato.columns = df_nato.columns.str.strip()
#     df_force.columns = df_force.columns.str.strip()
#
#     ## merge on key column
#     merged_df = pd.merge(df_force, df_nato, on='iso', how='inner')
#
#     ## filter to keep only non-union participants
#     merged_df = merged_df[merged_df["Collective (Y/N)"].isin(["N"])]
#
#     ## define answers for Question 8
#     valid_answers = ['Yes', 'No', 'Silent', 'Ambiguous']
#     ## replace 15 with the correct column index if needed
#     key_question_col = df_force.columns[15]
#
#     ## keep set of answers
#     filtered_df = merged_df[merged_df[key_question_col].isin(valid_answers)]
#
#     ## prepare data for sunburst: NATO → Question → ISO
#     # df = filtered_df[['Nato Membership', key_question_col, 'iso']].copy()
#
#     df = (
#
#         filtered_df[['Nato Membership', key_question_col, 'iso']]
#
#         .groupby(['Nato Membership', key_question_col, 'iso'])
#
#         .size()
#
#         .reset_index(name='Count')
#
#     )
#
#     ## build the sunburst -- drillable pie chart
#     fig = px.sunburst(
#         df,
#         path=['Nato Membership', key_question_col, 'iso'],  ## NATO → Question → ISO
#         values='Count',
#         branchvalues="total",
#         maxdepth=3
#     )
#
#     fig.update_traces(textinfo="label")
#     fig.update_layout(margin=dict(t=10, l=10, r=10, b=10))
#
#     return fig
#
def create_uofq8_sunburst_figure(df_force, df_nato):
    # Limpiar nombres de columnas
    df_nato.columns = df_nato.columns.str.strip()
    df_force.columns = df_force.columns.str.strip()

    # Verificar que la columna 'iso' existe en ambos dataframes
    if 'iso' not in df_force.columns or 'iso' not in df_nato.columns:
        raise ValueError("La columna 'iso' no existe en uno de los dataframes")

    # Merge de los dataframes
    merged_df = pd.merge(df_force, df_nato, on='iso', how='inner')

    # Filtrar participantes no colectivos (verificar que la columna existe)
    if 'Collective (Y/N)' not in merged_df.columns:
        raise ValueError("Columna 'Collective (Y/N)' no encontrada después del merge")

    merged_df = merged_df[merged_df["Collective (Y/N)"].isin(["N"])]

    # Definir respuestas válidas
    valid_answers = ['Yes', 'No', 'Silent', 'Ambiguous']

    # Verificar que el índice 15 existe
    if len(df_force.columns) <= 15:
        raise IndexError(f"DataFrame df_force solo tiene {len(df_force.columns)} columnas")

    key_question_col = df_force.columns[15]

    # Filtrar respuestas válidas
    filtered_df = merged_df[merged_df[key_question_col].isin(valid_answers)].copy()

    # Preparar datos para sunburst
    df_counts = (
        filtered_df[['Nato Membership', key_question_col, 'iso']]
        .groupby(['Nato Membership', key_question_col, 'iso'])
        .size()
        .reset_index(name='Count')
    )

    # Construir el gráfico sunburst
    fig = px.sunburst(
        df_counts,
        path=['Nato Membership', key_question_col, 'iso'],
        values='Count',
        branchvalues="total",
        maxdepth=3
    )

    fig.update_traces(textinfo="label+percent parent")
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10))

    return fig
