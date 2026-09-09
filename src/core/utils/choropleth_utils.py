# choropleth plot utils
import pandas as pd
import plotly.express as px

def create_statements_choropleth_figure(df, year_start=2016, year_end=2027):
    """
    Builds the animated choropleth of cumulative state statements
    per country, year by year.
    """
    df = df.copy()

    value_vars = [str(y) for y in range(year_start, year_end + 1)]

    # melt into long format
    df_long = pd.melt(
        df,
        id_vars=['Country'],
        value_vars=value_vars,
        var_name='Year',
        value_name='Highlight'
    )

    # convert to numeric
    df_long['Highlight'] = pd.to_numeric(df_long['Highlight'], errors='coerce').fillna(0).astype(int)
    df_long['Year'] = df_long['Year'].astype(int)

    # aggregate values across years
    df_long = df_long.sort_values(['Country', 'Year'])
    df_long['Cumulative'] = df_long.groupby('Country')['Highlight'].cumsum()

    # build choropleth
    fig = px.choropleth(
        df_long,
        locations="Country",
        locationmode="country names",
        color="Cumulative",
        animation_frame="Year",
        color_continuous_scale="Viridis",
        projection="natural earth",
        title=f"Cumulative State Statements by Year ({year_start}–{year_end})"
    )

    # outline the countries included in the CSV
    # all countries must be included in Python, otherwise boundaries look sparse
    fig.update_traces(marker_line_color='black', marker_line_width=0.5)

    # choropleth layout
    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True
        )
    )

    return fig