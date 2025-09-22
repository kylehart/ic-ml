#!/usr/bin/env python3
"""
Add slug field to product catalog.
Reads the existing minimal-product-catalog.csv and adds generated slugs.
"""

import sys
import csv
import re
sys.path.append('src')

from product_recommendation_engine import ProductCatalogItem

def generate_slug_from_title(title: str) -> str:
    """Generate a URL slug from the product title using observed patterns."""
    # Start with the title
    slug = title.lower()

    # Remove common brand prefixes if present
    brand_prefixes = ['somush ', 'rogue herbalist ', 'rh ']
    for prefix in brand_prefixes:
        if slug.startswith(prefix):
            slug = slug[len(prefix):]
            break

    # Remove quotes and special characters
    slug = re.sub(r'[\'\"]+', '', slug)  # Remove quotes
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars except spaces and hyphens

    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)

    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    return slug

def add_slugs_to_catalog():
    """Add slug field to the product catalog."""
    input_file = 'data/rogue-herbalist/minimal-product-catalog.csv'
    output_file = 'data/rogue-herbalist/minimal-product-catalog-with-slugs.csv'

    print(f"Reading catalog from: {input_file}")
    print(f"Writing updated catalog to: {output_file}")

    rows_processed = 0

    with open(input_file, 'r', encoding='utf-8') as infile:
        # Read the input CSV
        reader = csv.DictReader(infile)

        # Get the original field names and add 'Slug'
        fieldnames = reader.fieldnames + ['Slug']

        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                # Generate slug from the Name field
                title = row.get('Name', '')
                if title:
                    slug = generate_slug_from_title(title)
                    row['Slug'] = slug

                    # Print progress for first few and every 50th
                    if rows_processed < 5 or rows_processed % 50 == 0:
                        print(f"  {rows_processed + 1:3d}: '{title}' -> '{slug}'")
                else:
                    row['Slug'] = ''
                    print(f"  {rows_processed + 1:3d}: Warning - no title found")

                writer.writerow(row)
                rows_processed += 1

    print(f"\nCompleted! Processed {rows_processed} products.")
    print(f"Updated catalog saved to: {output_file}")

if __name__ == "__main__":
    add_slugs_to_catalog()