#!/usr/bin/env python3
"""
Verify the slug generation worked correctly.
"""

import csv

def verify_slugs():
    """Check that slugs were added correctly to the catalog."""
    input_file = 'data/rogue-herbalist/minimal-product-catalog-with-slugs.csv'

    print("Verifying slug generation in product catalog")
    print("=" * 50)

    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        # Check first 10 products
        for i, row in enumerate(reader):
            if i >= 10:
                break

            id_val = row.get('ID', '')
            name = row.get('Name', '')
            slug = row.get('Slug', '')

            print(f"{i+1:2d}. ID: {id_val:4s} | {name:40s} | {slug}")

    print("\nChecking specific test cases:")

    # Check our known test cases
    test_cases = [
        ('3677', 'Hemp Adapt 2oz.', 'hemp-adapt-2oz'),
        ('1111', 'Four Mushroom Immune Complex 2oz.', 'four-mushroom-immune-complex-2oz'),
        ('3678', 'Hemp Bitters 2oz.', 'hemp-bitters-2oz'),
    ]

    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            id_val = row.get('ID', '')
            name = row.get('Name', '')
            slug = row.get('Slug', '')

            for test_id, test_name, expected_slug in test_cases:
                if id_val == test_id:
                    status = "✅ MATCH" if slug == expected_slug else "❌ MISMATCH"
                    print(f"{status}: ID {id_val} | {name} | {slug}")
                    if slug != expected_slug:
                        print(f"    Expected: {expected_slug}")

if __name__ == "__main__":
    verify_slugs()