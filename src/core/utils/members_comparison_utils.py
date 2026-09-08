# member comparison table utils
import pandas as pd
import html as html_lib
from core.utils.sankey_utils import clean_question


def _build_citation_lookup(df_citations):
    """Returns dict (iso, question_clean, answer_clean) -> (citation, pincite, url)"""
    lookup = {}
    if df_citations is None or df_citations.empty:
        return lookup

    df = df_citations.copy()
    df['iso'] = df['iso'].astype(str)
    df['Question_clean'] = df['Question'].apply(clean_question)
    df['Answer_clean'] = df['Answer'].astype(str).str.strip().str.lower().str.rstrip('.')

    for _, row in df.iterrows():
        url = str(row.get('Source_URL', '')).strip()
        if not url or url == 'nan':
            continue
        key = (row['iso'], row['Question_clean'], row['Answer_clean'])
        lookup[key] = (
            str(row.get('Citation', '') or ''),
            str(row.get('Pincite_Text', '') or ''),
            url,
        )
    return lookup


def _render_cell(iso, question, answer, lookup):
    """Renders one table cell: a clickable <a> with a tooltip if a citation
    exists for this (country, question, answer), or plain text otherwise."""
    answer_text = '' if pd.isna(answer) else str(answer)
    if not answer_text.strip():
        return ''

    question_clean = clean_question(question)
    answer_clean = answer_text.strip().lower().rstrip('.')
    key = (str(iso), question_clean, answer_clean)

    entry = lookup.get(key)
    if not entry:
        return html_lib.escape(answer_text)

    citation, pincite, url = entry
    tooltip_parts = [p for p in (pincite, citation) if p]
    tooltip = ' — '.join(tooltip_parts) if tooltip_parts else 'View source'

    return (
        f'<a href="{html_lib.escape(url)}" target="_blank" rel="noopener" '
        f'title="{html_lib.escape(tooltip)}" class="citation-link">'
        f'{html_lib.escape(answer_text)}</a>'
    )


def _render_comparison_table(preguntas_list, eu_row, respuestas_paises, title, lookup):
    """Builds the full HTML table (header + colored cells + links)."""
    country_names = list(respuestas_paises.keys())

    header_cells = ''.join(
        f'<th>{html_lib.escape(str(c))}</th>' for c in ['Question', 'EU'] + country_names
    )

    body_rows = []
    for i, pregunta in enumerate(preguntas_list):
        respuesta_ue = eu_row[pregunta]

        row_cells = [f'<td class="question-cell">{html_lib.escape(str(pregunta))}</td>']
        row_cells.append(
            f'<td class="answer-cell eu-cell">'
            f'{_render_cell("EUN", pregunta, respuesta_ue, lookup)}</td>'
        )

        for pais in country_names:
            respuesta_pais = respuestas_paises[pais][i]
            match = str(respuesta_pais) == str(respuesta_ue)
            cell_class = 'match' if match else 'mismatch'
            row_cells.append(
                f'<td class="answer-cell {cell_class}">'
                f'{_render_cell(pais, pregunta, respuesta_pais, lookup)}</td>'
            )

        body_rows.append(f'<tr>{"".join(row_cells)}</tr>')

    return f"""
    <style>
        .comparison-table-wrapper {{ overflow-x: auto; }}
        .comparison-table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
        .comparison-table th {{
            background-color: lightblue; text-align: left; padding: 6px 10px;
            position: sticky; top: 0;
        }}
        .comparison-table td {{ padding: 6px 10px; border: 1px solid #ddd; }}
        .comparison-table .question-cell {{ background-color: lightgrey; min-width: 250px; }}
        .comparison-table .eu-cell {{ background-color: lightblue; }}
        .comparison-table .match {{ background-color: lightgreen; }}
        .comparison-table .mismatch {{ background-color: lightcoral; }}
        .comparison-table a.citation-link {{
            color: inherit; text-decoration: underline; cursor: pointer;
        }}
    </style>
    <div class="comparison-table-wrapper">
        <h3>{html_lib.escape(title)}</h3>
        <table class="comparison-table">
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{''.join(body_rows)}</tbody>
        </table>
    </div>
    """


def create_eu_comparison_table(df_issue, preguntas, df_membership, df_citations=None):
    """Crea una tabla comparativa entre respuestas de la UE y países miembros"""
    try:
        df_merged = pd.merge(
            df_issue,
            df_membership[['iso', 'membership']],
            on='iso',
            how='inner'
        ).dropna(subset=['membership'])

        eu_data = df_issue[df_issue['iso'] == 'EUN']
        if eu_data.empty:
            print("No se encontró datos para la UE")
            return ""

        eu_row = eu_data.iloc[0]

        miembros_ue = df_merged[(df_merged['membership'] == 'EU') & (df_merged['iso'] != 'EUN')]
        if miembros_ue.empty:
            print("No se encontraron países miembros de la UE")
            return ""

        respuestas_paises = {pais: [] for pais in miembros_ue['iso'].tolist()}
        for pregunta in preguntas:
            for _, pais_row in miembros_ue.iterrows():
                respuestas_paises[pais_row['iso']].append(pais_row[pregunta])

        lookup = _build_citation_lookup(df_citations)
        return _render_comparison_table(list(preguntas), eu_row, respuestas_paises, '', lookup)

    except Exception as e:
        print(f"Error creando tabla de comparación: {e}")
        import traceback
        traceback.print_exc()
        return ""


def create_eu_non_members_comparison_table(df_issue, preguntas, df_membership, df_citations=None):
    """Crea una tabla comparativa entre respuestas de la UE y países NO miembros"""
    try:
        miembros_eu = df_membership[df_membership['membership'] == 'EU']['iso'].tolist()

        eu_data = df_issue[df_issue['iso'] == 'EUN']
        if eu_data.empty:
            print("No se encontró datos para la UE")
            return ""

        eu_row = eu_data.iloc[0]

        no_miembros = df_issue[
            (~df_issue['iso'].isin(miembros_eu)) &
            (df_issue['iso'] != 'EUN')
        ]
        if no_miembros.empty:
            print("No se encontraron países no miembros de la UE")
            return ""

        respuestas_paises = {pais: [] for pais in no_miembros['iso'].tolist()}
        for pregunta in preguntas:
            for _, pais_row in no_miembros.iterrows():
                respuestas_paises[pais_row['iso']].append(pais_row[pregunta])

        lookup = _build_citation_lookup(df_citations)
        return _render_comparison_table(
            list(preguntas), eu_row, respuestas_paises, 'Comparison of EU vs NON Members', lookup
        )

    except Exception as e:
        print(f"Error creando tabla de comparación: {e}")
        import traceback
        traceback.print_exc()
        return ""