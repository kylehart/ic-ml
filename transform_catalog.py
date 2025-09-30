#!/usr/bin/env python3
"""
Transform WooCommerce product export to minimal-product-catalog format.
Converts internal newlines to literal ' \\n ' (with spaces).
Keeps all original columns from WooCommerce export (including Slug from WooCommerce).
"""

import csv
import re
from pathlib import Path


def clean_field(text):
    """Replace internal newlines with literal ' \\n ' (with spaces)."""
    if not text:
        return text
    # Replace actual newlines with literal ' \n '
    text = text.replace('\n', ' \\n ')
    # Clean up multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def transform_catalog(input_file, output_file):
    """Transform WooCommerce export cleaning newlines in descriptions."""

    print(f"Reading: {input_file}")

    rows_processed = 0

    with open(input_file, 'r', encoding='utf-8-sig') as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:

        reader = csv.DictReader(infile)

        # Keep all original columns from WooCommerce export
        # Expected: ID, Type, SKU, Name, Short description, Description, In stock?, and more
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            # Clean description fields
            if 'Short description' in row:
                row['Short description'] = clean_field(row['Short description'])
            if 'Description' in row:
                row['Description'] = clean_field(row['Description'])

            # Write transformed row with all original columns
            writer.writerow(row)

            rows_processed += 1

    print(f"Processed {rows_processed} products")
    print(f"Output written to: {output_file}")


if __name__ == '__main__':
    # File paths
    input_file = Path('/Users/kylehart/Documents/dev/repos/all/ic-ml/data/rogue-herbalist/wc-product-export-29-9-2025-1759193249295.csv')
    output_file = Path('/Users/kylehart/Documents/dev/repos/all/ic-ml/data/rogue-herbalist/minimal-product-catalog.csv')

    # Confirm overwrite
    if output_file.exists():
        print(f"⚠️  Will overwrite: {output_file}")

    transform_catalog(input_file, output_file)

    print("\n✅ Transformation complete!")