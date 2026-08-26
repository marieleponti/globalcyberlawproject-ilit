"""
Fills in the 'iso' column of the extracted citations CSV automatically,
using the State -> ISO mapping already present in the main data CSV
(e.g. sovereignty-aug2026.csv), matched against the 'Entity' column.

Usage:
    python fill_iso_from_main.py sovereignty_extracted.csv sovereignty-aug2026.csv output.csv

Any Entity that doesn't match a State exactly is left blank and printed
to the console, so you can fix those few by hand instead of everything.
"""

import sys
import csv


def normalize(name):
    """Lowercase + strip, so 'African Union' matches 'african union'
    even with stray whitespace."""
    return name.strip().lower()


def main(extracted_csv, main_csv, output_csv):
    # Build the State -> ISO lookup from the main data CSV
    with open(main_csv, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        main_rows = list(reader)

    # Main CSV columns are State, ISO, <question columns...>
    state_col = 'State' if 'State' in main_rows[0] else list(main_rows[0].keys())[0]
    iso_col = 'ISO' if 'ISO' in main_rows[0] else 'iso'

    state_to_iso = {
        normalize(row[state_col]): row[iso_col].strip()
        for row in main_rows
        if row.get(state_col) and row.get(iso_col)
    }

    print(f"{len(state_to_iso)} state->iso mappings loaded from {main_csv}")

    # Fill the extracted citations CSV
    with open(extracted_csv, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    matched = 0
    unmatched_entities = set()

    for row in rows:
        entity_key = normalize(row['Entity'])
        iso = state_to_iso.get(entity_key)
        if iso:
            row['iso'] = iso
            matched += 1
        else:
            unmatched_entities.add(row['Entity'])

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{matched} of {len(rows)} rows matched and filled automatically.")
    print(f"-> {output_csv}")

    if unmatched_entities:
        print(f"\n⚠️  {len(unmatched_entities)} entities did NOT match -- fill these by hand:")
        for e in sorted(unmatched_entities):
            print(f"  - {e}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python fill_iso_from_main.py extracted.csv main_data.csv output.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
