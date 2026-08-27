"""
Diagnoses why the citations merge fails for many rows in the Sankey.

Runs the same merge logic as prepare_merged_dataframe() in sankey_utils.py,
and reports how many (State, Question, Answer) combinations from the main
data CSV find NO matching citation -- broken down by likely cause:
  1. iso missing/empty in the citations CSV
  2. iso present, but Question_clean doesn't match anything for that iso
  3. iso + Question_clean match, but Answer doesn't match

Usage:
    python diagnose_citation_merge.py sovereignty-aug2026.csv sovereignty_citations_extracted-july2026.csv
"""

import sys
import re
import pandas as pd


def clean_question(text):
    if pd.isna(text):
        return text
    text = re.sub(r'^\s*\d+(?:\.\d+)*\s*', '', text)
    text = re.sub(r'^(\s*\([^)]+\))+', '', text)
    text = re.sub(r'^\s*[\.\:\-\–]+\s*', '', text)
    text = text.strip().lower()
    if text:
        text = text[0].upper() + text[1:]
    return text


def main(main_csv, citations_csv):
    df_main = pd.read_csv(main_csv)
    df_main = df_main.rename(columns={'ISO': 'iso'})
    df_main = df_main.loc[:, ~df_main.columns.duplicated()]

    df_citations = pd.read_csv(citations_csv)
    df_citations = df_citations.rename(columns={'ISO': 'iso'})

    question_columns = [c for c in df_main.columns if c not in ['State', 'iso']]

    df_long = df_main.melt(
        id_vars=['State', 'iso'],
        value_vars=question_columns,
        var_name='Question',
        value_name='Answer'
    )
    df_long['Question_clean'] = df_long['Question'].apply(clean_question)
    df_long['Answer'] = df_long['Answer'].astype(str).str.strip().str.lower()
    df_long['iso'] = df_long['iso'].astype(str)

    df_citations['Question_clean'] = df_citations['Question'].apply(clean_question)
    df_citations['Answer'] = df_citations['Answer'].astype(str).str.strip().str.lower()
    df_citations['iso'] = df_citations['iso'].astype(str)

    # Which isos actually have at least one citation row?
    isos_with_citations = set(
        df_citations.loc[df_citations['iso'].notna() & (df_citations['iso'].str.strip() != '') & (df_citations['iso'] != 'nan'), 'iso']
    )

    # Which (iso, question_clean) pairs exist in citations?
    iso_question_pairs = set(zip(df_citations['iso'], df_citations['Question_clean']))

    # Which (iso, question_clean, answer) triples exist in citations?
    full_triples = set(zip(df_citations['iso'], df_citations['Question_clean'], df_citations['Answer']))

    total = len(df_long)
    reason_no_iso = 0
    reason_no_question = 0
    reason_no_answer = 0
    matched = 0

    examples_no_question = []
    examples_no_answer = []

    for _, row in df_long.iterrows():
        key_iso = row['iso']
        key_q = row['Question_clean']
        key_a = row['Answer']

        if key_iso not in isos_with_citations:
            reason_no_iso += 1
        elif (key_iso, key_q) not in iso_question_pairs:
            reason_no_question += 1
            if len(examples_no_question) < 15:
                examples_no_question.append((row['State'], key_iso, row['Question']))
        elif (key_iso, key_q, key_a) not in full_triples:
            reason_no_answer += 1
            if len(examples_no_answer) < 15:
                examples_no_answer.append((row['State'], key_iso, row['Question'], row['Answer']))
        else:
            matched += 1

    print(f"Total combinaciones país+pregunta en el CSV principal: {total}\n")
    print(f"✅ Con match completo (van a tener cita/link):        {matched}")
    print(f"❌ Sin match -- iso no existe en citas:                {reason_no_iso}")
    print(f"❌ Sin match -- iso existe, pero Question no calza:    {reason_no_question}")
    print(f"❌ Sin match -- iso+Question calzan, pero Answer no:   {reason_no_answer}")

    if examples_no_question:
        print(f"\n--- Ejemplos de Question que no calza (revisar redacción/typos) ---")
        for state, iso, q in examples_no_question:
            print(f"  {state} ({iso}): \"{q}\"")

    if examples_no_answer:
        print(f"\n--- Ejemplos de Answer que no calza (mismo iso+pregunta, respuesta distinta) ---")
        for state, iso, q, a in examples_no_answer:
            print(f"  {state} ({iso}) | \"{q[:50]}\" | Answer del CSV principal: \"{a}\"")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python diagnose_citation_merge.py main_data.csv citations.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])