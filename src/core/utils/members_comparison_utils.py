# member comparison table utils
import pandas as pd
import plotly.graph_objects as go
from django.core.cache import cache
import os


def create_eu_comparison_table(df_issue, preguntas, df_membership):
    """
    Crea una tabla comparativa entre respuestas de la UE y países miembros
    Devuelve la figura de Plotly directamente
    """
    try:
        # Fusionar con información de membresía
        df_merged = pd.merge(
            df_issue,
            df_membership[['iso', 'membership']],
            on='iso',
            how='inner'
        ).dropna()

        # Obtener fila de la UE
        eu_data = df_issue[df_issue['iso'] == 'EUN']

        if eu_data.empty:
            print("No se encontró datos para la UE")
            return go.Figure()

        eu_row = eu_data.iloc[0]

        # Filtrar solo países miembros de la UE (excluyendo la fila EU)
        miembros_ue = df_merged[(df_merged['membership'] == 'EU') & (df_merged['iso'] != 'EUN')]

        if miembros_ue.empty:
            print("No se encontraron países miembros de la UE")
            return go.Figure()

        # Preparar datos para la tabla
        preguntas_list = []
        respuestas_ue = []
        respuestas_paises = {pais: [] for pais in miembros_ue['iso'].tolist()}

        # Recolectar datos
        for pregunta in preguntas:
            preguntas_list.append(pregunta)
            respuestas_ue.append(eu_row[pregunta])

            for _, pais_row in miembros_ue.iterrows():
                pais_nombre = pais_row['iso']
                respuestas_paises[pais_nombre].append(pais_row[pregunta])

        # Crear matriz de valores para la tabla
        valores = [preguntas_list, respuestas_ue]
        nombres_columnas = ['Question', 'EU']

        for pais_nombre in respuestas_paises.keys():
            valores.append(respuestas_paises[pais_nombre])
            nombres_columnas.append(pais_nombre)

        # Crear la tabla
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=nombres_columnas,
                fill_color='lightblue',
                align='left',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=valores,
                fill_color=[],
                align='left',
                font=dict(size=11),
                # org 15
                height=7
            ),
            # org 300
            columnwidth=[1200, 400]
        )])

        # Configurar colores basados en comparación con UE
        colors = []

        # INICIO: Cambia esta parte
        colors = []  # Si colors es una lista, déjala así

        # Para cada fila (pregunta)
        for i in range(len(preguntas_list)):
            fila_colores = ['lightgrey']  # Color para columna de pregunta
            fila_colores.append('lightblue')  # Celda de UE

            respuesta_ue = respuestas_ue[i]

            # Para cada país
            for pais_nombre in respuestas_paises.keys():
                respuesta_pais = respuestas_paises[pais_nombre][i]

                # Determinar color basado en similitud con respuesta UE
                if str(respuesta_pais) == str(respuesta_ue):
                    color = 'lightgreen'  # Misma respuesta
                else:
                    color = 'lightcoral'  # Respuesta diferente

                fila_colores.append(color)

            # Esto está bien si colors es una lista
            colors.append(fila_colores)

        # Transponer la matriz de colores
        colors_transposed = list(map(list, zip(*colors)))

        # Aplicar colores a la tabla
        fig.update_traces(
            cells=dict(fill_color=colors_transposed)
        )

        # Configurar layout
        fig.update_layout(
            title='',
            height=500 + (len(preguntas) * 30),
            width=1700,
            margin=dict(l=10, r=10, t=80, b=10),
            title_x=0.5
        )

        return fig

    except Exception as e:
        print(f"Error creando tabla de comparación: {e}")
        import traceback
        traceback.print_exc()
        return go.Figure()


def create_eu_non_members_comparison_table(df_issue, preguntas, df_membership):
    """
    Crea una tabla comparativa entre respuestas de la UE y países NO miembros
    """
    try:
        # Obtener la lista de países miembros EU (incluyendo EUN)
        miembros_eu = df_membership[df_membership['membership'] == 'EU']['iso'].tolist()
        print(f"Países miembros EU: {miembros_eu}")

        # Obtener fila de la UE
        eu_data = df_issue[df_issue['iso'] == 'EUN']

        if eu_data.empty:
            print("No se encontró datos para la UE")
            return go.Figure()

        eu_row = eu_data.iloc[0]

        # Filtrar países NO miembros: todos los de df_issue que NO estén en la lista de miembros
        # y que no sean la UE misma
        no_miembros = df_issue[
            (~df_issue['iso'].isin(miembros_eu)) &
            (df_issue['iso'] != 'EUN')
            ].dropna()

        print(f"Países NO miembros encontrados: {len(no_miembros)}")
        if len(no_miembros) > 0:
            print(f"ISOs de NO miembros: {no_miembros['iso'].tolist()}")

        if no_miembros.empty:
            print("No se encontraron países no miembros de la UE")
            return go.Figure()

        # Preparar datos para la tabla
        preguntas_list = []
        respuestas_ue = []
        respuestas_paises = {pais: [] for pais in no_miembros['iso'].tolist()}

        # Recolectar datos
        for pregunta in preguntas:
            preguntas_list.append(pregunta)
            respuestas_ue.append(eu_row[pregunta])

            for _, pais_row in no_miembros.iterrows():
                pais_nombre = pais_row['iso']
                respuestas_paises[pais_nombre].append(pais_row[pregunta])

        # Crear matriz de valores para la tabla
        valores = [preguntas_list, respuestas_ue]
        nombres_columnas = ['Question', 'EU']

        for pais_nombre in respuestas_paises.keys():
            valores.append(respuestas_paises[pais_nombre])
            nombres_columnas.append(pais_nombre)

        # Crear la tabla
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=nombres_columnas,
                fill_color='lightblue',
                align='left',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=valores,
                fill_color=[],
                align='left',
                font=dict(size=11),
                height=7
            ),
            columnwidth=[1200, 400]
        )])

        # Configurar colores basados en comparación con UE
        colors = []

        # Para cada fila (pregunta)
        for i in range(len(preguntas_list)):
            fila_colores = ['lightgrey']  # Color para columna de pregunta
            fila_colores.append('lightblue')  # Celda de UE

            respuesta_ue = respuestas_ue[i]

            # Para cada país
            for pais_nombre in respuestas_paises.keys():
                respuesta_pais = respuestas_paises[pais_nombre][i]

                # Determinar color basado en similitud con respuesta UE
                if str(respuesta_pais) == str(respuesta_ue):
                    color = 'lightgreen'  # Misma respuesta
                else:
                    color = 'lightcoral'  # Respuesta diferente

                fila_colores.append(color)

            colors.append(fila_colores)

        # Transponer la matriz de colores
        colors_transposed = list(map(list, zip(*colors)))

        # Aplicar colores a la tabla
        fig.update_traces(
            cells=dict(fill_color=colors_transposed)
        )

        # Configurar layout
        fig.update_layout(
            title='Comparison of EU vs NON Members',
            height=500 + (len(preguntas) * 30),
            width=1700,
            margin=dict(l=10, r=10, t=80, b=10),
            title_x=0.5
        )

        return fig

    except Exception as e:
        print(f"Error creando tabla de comparación: {e}")
        import traceback
        traceback.print_exc()
        return go.Figure()