"""
Replaces SharePoint URLs in Source_URL with local static paths, using the
mapping already generated in sharepoint_links_to_replace.csv.

Usage:
    python replace_sharepoint_links.py sharepoint_links_to_replace.csv \
        sovereignty_extracted-july2026.csv \
        uof_extracted.csv \
        nonintervention_extracted.csv \
        selfdefense_extracted.csv

Each target CSV is overwritten in place (a .bak backup is made first).
Only rows whose Source_URL exactly matches one of the mapped SharePoint
URLs are changed -- everything else (perma.cc, etc.) is left untouched.
"""

import sys
import csv
import shutil


def load_mapping(mapping_csv):
    url_to_path = {}
    with open(mapping_csv, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row['original_url'].strip()
            filename = row['suggested_filename'].strip()
            url_to_path[url] = f"/static/documents/{filename}"
    return url_to_path


def replace_in_file(path, url_to_path):
    shutil.copy(path, path + '.bak')

    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    replaced = 0
    for row in rows:
        url = row.get('Source_URL', '').strip()
        if url in url_to_path:
            row['Source_URL'] = url_to_path[url]
            replaced += 1

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{path}: {replaced} filas actualizadas (respaldo en {path}.bak)")


def main(mapping_csv, target_csvs):
    url_to_path = load_mapping(mapping_csv)
    print(f"{len(url_to_path)} URLs de SharePoint cargadas del mapeo.\n")

    for path in target_csvs:
        replace_in_file(path, url_to_path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python replace_sharepoint_links.py mapping.csv target1.csv [target2.csv ...]")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2:])
