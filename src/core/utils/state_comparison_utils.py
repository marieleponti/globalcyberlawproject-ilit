import pandas as pd
import plotly.graph_objects as go
import ipywidgets as widgets
from IPython.display import display, clear_output

reference_nation='AU'
def create_comparison_table(df, reference_nation):
    ## the chosen columns
    question_col = df.columns[0]  ## this is the first column called questions
    nations = df.columns[1:]  ## '1st' column is nations

    # Crear el dropdown DESPUÉS de definir nations
    dropdown = widgets.Dropdown(
        options=nations,
        description="Reference:",
        style={"description_width": "initial"},
        layout=widgets.Layout(width="250px")
    )
    """
    Crea una tabla comparativa de Plotly con la nación de referencia destacada
    Retorna un objeto fig de Plotly
    """
    try:
        # Reordenar el DataFrame con la nación de referencia primero
        reordered = df[[question_col, reference_nation] +
                       [c for c in nations if c != reference_nation]]

        # Preparar datos para la tabla
        headers = reordered.columns.tolist()
        values = []

        # Transponer los datos para la tabla de Plotly
        for col in reordered.columns:
            values.append(reordered[col].tolist())

        # Crear matriz de colores basada en la comparación
        cell_colors = []

        # Para cada columna (excepto la primera que son las preguntas)
        for i, col_name in enumerate(headers):
            if col_name == question_col:
                # Columna de preguntas - gris
                cell_colors.append(['lightgrey'] * len(reordered))
            elif col_name == reference_nation:
                # Nación de referencia - azul
                cell_colors.append(['#add8e6'] * len(reordered))
            else:
                # Otras naciones - comparar con referencia
                col_colors = []
                ref_values = reordered[reference_nation].tolist()
                current_values = reordered[col_name].tolist()

                for j in range(len(reordered)):
                    if current_values[j] == ref_values[j]:
                        col_colors.append('#add8e6')  # Mismo valor que referencia
                    else:
                        col_colors.append('#ebe173')  # Valor diferente

                cell_colors.append(col_colors)

        # Transponer la matriz de colores para Plotly
        cell_colors_transposed = list(map(list, zip(*cell_colors)))

        # Crear la tabla de Plotly
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=headers,
                fill_color='#4f81bd',
                align='center',
                font=dict(size=12, color='white', weight='bold'),
                line=dict(width=1, color='#ddd'),
                height=40
            ),
            cells=dict(
                values=values,
                fill_color=cell_colors_transposed,
                align='center',
                font=dict(size=11, color='black'),
                line=dict(width=1, color='#ddd'),
                height=30
            )
        )])

        # Configurar el layout
        fig.update_layout(
            title=f'Comparación con referencia: {reference_nation}',
            height=400 + (len(reordered) * 30),
            margin=dict(l=10, r=10, t=80, b=10),
            title_x=0.5,
            title_font=dict(size=16)
        )

        return fig

    except Exception as e:
        print(f"Error creando tabla de comparación: {e}")
        import traceback
        traceback.print_exc()
        return go.Figure()


# Función para manejar la selección del dropdown
def update_table(reference_nation):
    """
    Actualiza y muestra la tabla cuando se selecciona una nación del dropdown
    """
    clear_output(wait=True)  # Limpiar output anterior
    display(dropdown)  # Mostrar el dropdown nuevamente

    # Crear y mostrar la tabla
    fig = create_comparison_table(reference_nation)
    display(fig)


    # Configurar la interactividad
    dropdown.observe(lambda change: update_table(change.new) if change.name == 'value' else None)

    # Mostrar inicialmente
    display(dropdown)
    if dropdown.value:
        update_table(dropdown.value)


# Función adicional para obtener la figura sin mostrar (útil para otros usos)
def get_comparison_table(reference_nation):
    """
    Retorna la figura de Plotly para la nación de referencia especificada
    sin mostrarla automáticamente
    """
    return create_comparison_table(reference_nation)