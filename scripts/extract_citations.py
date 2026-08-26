"""
Extrae las tablas de citas de un documento Word (.docx) con esta estructura:

    [Título arriba de la tabla: nombre del país/entidad, ej. "African Union"]
    | Question | Answer | Citation | Pincite (con hyperlink) | Comment |

Preserva la URL real del hyperlink en "Pincite", aunque el texto visible
sea la referencia bibliográfica completa (no la URL en sí).

Uso:
    pip install python-docx --break-system-packages
    python extract_citations_docx.py documento.docx salida.csv

Salida (una fila por pregunta/respuesta, con estas columnas):
    Entity, iso, Question, Answer, Citation, Pincite_Text, Source_URL, Comment

La columna "iso" queda vacía a propósito -- se llena a mano usando "Entity"
como referencia (ej. Entity="African Union" -> tú decides qué poner en iso,
ya que una organización regional puede no tener un código ISO de país).
"""

import sys
import csv
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl


def get_hyperlink_url(document, hyperlink_element):
    r_id = hyperlink_element.get(qn('r:id'))
    if r_id is None:
        return ""
    try:
        return document.part.rels[r_id].target_ref
    except KeyError:
        return ""


def extract_cell_content(document, cell):
    """Devuelve (texto_visible, url) de una celda. Si hay hyperlink,
    la url es la del hyperlink; si no, url queda vacía."""
    texts = []
    url = ""

    for paragraph in cell.paragraphs:
        p_element = paragraph._p
        found_hyperlink = False
        for hyperlink in p_element.findall(qn('w:hyperlink')):
            found_hyperlink = True
            link_text = "".join(
                node.text or "" for node in hyperlink.iter(qn('w:t'))
            )
            if link_text:
                texts.append(link_text)
            candidate_url = get_hyperlink_url(document, hyperlink)
            if candidate_url:
                url = candidate_url  # si hay varios, se queda con el último

        if not found_hyperlink and paragraph.text:
            texts.append(paragraph.text)

    return " ".join(texts).strip(), url


def iter_block_items(parent_element, document):
    """Recorre párrafos y tablas en el orden en que aparecen en el documento,
    para poder asociar el título (párrafo) que antecede a cada tabla."""
    for child in parent_element.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def main(docx_path, csv_path):
    document = Document(docx_path)
    body = document.element.body

    rows_out = []
    last_title = ""

    for block in iter_block_items(body, document):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text:
                last_title = text  # el párrafo no vacío más reciente = título de la próxima tabla

        elif isinstance(block, Table):
            # Buscar la fila real de encabezado (contiene 'Question'), en vez
            # de asumir que es la fila 0 -- algunas tablas tienen una fila
            # combinada arriba con el nombre del país/entidad.
            header_idx = find_header_row_index(block)

            if header_idx is None:
                preview = [
                    [c.text.strip() for c in row.cells]
                    for row in block.rows[:6]
                ]
                print(f"⚠️  Tabla bajo '{last_title}' no tiene fila de encabezado "
                      f"reconocible (primeras filas: {preview}) -- se omite.")
                continue

            # Nombre de la entidad: si hay una fila combinada arriba del
            # encabezado, úsala (es más confiable que el párrafo anterior,
            # que puede ser solo metadata como "Last modified: ...").
            if header_idx > 0:
                entity_row_texts = [c.text.strip() for c in block.rows[header_idx - 1].cells]
                uniq = list(dict.fromkeys(t for t in entity_row_texts if t))
                entity = uniq[0] if len(uniq) == 1 else (uniq[0] if uniq else last_title)
            else:
                entity = last_title

            header_cells = [c.text.strip() for c in block.rows[header_idx].cells]
            col_index = {name.lower(): i for i, name in enumerate(header_cells)}
            if 'questions' in col_index and 'question' not in col_index:
                col_index['question'] = col_index['questions']

            required = ['question', 'answer', 'citation', 'pincite']
            if not all(col in col_index for col in required):
                print(f"⚠️  Tabla bajo '{entity}' no tiene las columnas esperadas "
                      f"({header_cells}) -- se omite.")
                continue

            comment_idx = col_index.get('comment')

            for row in block.rows[header_idx + 1:]:  # saltar filas de título + encabezado
                cells = row.cells
                question_text, _ = extract_cell_content(document, cells[col_index['question']])
                answer_text, _ = extract_cell_content(document, cells[col_index['answer']])
                citation_text, _ = extract_cell_content(document, cells[col_index['citation']])
                pincite_text, pincite_url = extract_cell_content(document, cells[col_index['pincite']])
                comment_text = ""
                if comment_idx is not None:
                    comment_text, _ = extract_cell_content(document, cells[comment_idx])

                if not question_text and not answer_text:
                    continue  # fila vacía / de relleno

                rows_out.append([
                    entity, "", question_text, answer_text,
                    citation_text, pincite_text, pincite_url, comment_text
                ])

    header = ["Entity", "iso", "Question", "Answer", "Citation",
              "Pincite_Text", "Source_URL", "Comment"]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows_out)

    print(f"{len(rows_out)} filas extraídas -> {csv_path}")
    print("Recuerda llenar la columna 'iso' manualmente usando 'Entity' como referencia.")


def find_header_row_index(table, max_rows_to_check=6):
    """Busca, entre las primeras filas de la tabla, la que realmente
    contiene 'Question'/'Questions' como texto de celda -- así no importa
    si hay una fila de título combinada antes del encabezado real, ni si
    el documento usa singular o plural."""
    for idx, row in enumerate(table.rows[:max_rows_to_check]):
        texts = [cell.text.strip().lower() for cell in row.cells]
        if 'question' in texts or 'questions' in texts:
            return idx
    return None


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python extract_citations_docx.py documento.docx salida.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])