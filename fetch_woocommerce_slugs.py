#!/usr/bin/env python3
"""
Fetch product slugs from WooCommerce REST API.

This script retrieves all products from the Rogue Herbalist WooCommerce store
and extracts the actual slugs to update the product catalog.

Requirements:
    pip install requests

Usage:
    python fetch_woocommerce_slugs.py

Environment Variables:
    WC_CONSUMER_KEY: WooCommerce REST API Consumer Key
    WC_CONSUMER_SECRET: WooCommerce REST API Consumer Secret

Or edit the script to hardcode credentials for one-time use.
"""

import os
import sys
import csv
import json
import requests
from typing import List, Dict, Any
from pathlib import Path


# WooCommerce API Configuration
STORE_URL = "https://rogueherbalist.com"
API_VERSION = "wc/v3"
CONSUMER_KEY = os.getenv("WC_CONSUMER_KEY", "")
CONSUMER_SECRET = os.getenv("WC_CONSUMER_SECRET", "")

# If not using environment variables, set them here for one-time use:
# CONSUMER_KEY = "ck_xxxxxxxxxxxxxxxxxxxx"
# CONSUMER_SECRET = "cs_xxxxxxxxxxxxxxxxxxxx"


def fetch_all_products(per_page: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch all products from WooCommerce API with pagination.

    Args:
        per_page: Number of products per page (max 100)

    Returns:
        List of product dictionaries with id, name, slug, sku, permalink
    """
    if not CONSUMER_KEY or not CONSUMER_SECRET:
        print("❌ Error: WooCommerce API credentials not set!")
        print("Set WC_CONSUMER_KEY and WC_CONSUMER_SECRET environment variables")
        print("Or edit this script to hardcode credentials")
        sys.exit(1)

    all_products = []
    page = 1

    # API endpoint with field filtering for efficiency
    endpoint = f"{STORE_URL}/wp-json/{API_VERSION}/products"

    # Authentication
    auth = (CONSUMER_KEY, CONSUMER_SECRET)

    print(f"🔍 Fetching products from {STORE_URL}...")

    while True:
        # Request parameters
        params = {
            "per_page": per_page,
            "page": page,
            "_fields": "id,name,slug,sku,permalink,status,stock_status"
        }

        try:
            response = requests.get(endpoint, auth=auth, params=params, timeout=30)
            response.raise_for_status()

            products = response.json()

            # Check if we got any products
            if not products:
                break

            all_products.extend(products)

            # Get total pages from headers
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            total_items = int(response.headers.get('X-WP-Total', len(products)))

            print(f"   Page {page}/{total_pages}: Fetched {len(products)} products "
                  f"(Total: {len(all_products)}/{total_items})")

            # Check if we've fetched all pages
            if page >= total_pages:
                break

            page += 1

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching page {page}: {e}")
            break

    print(f"✅ Fetched {len(all_products)} total products")
    return all_products


def update_catalog_with_slugs(products: List[Dict[str, Any]], catalog_path: Path, output_path: Path):
    """
    Update the product catalog CSV with actual WooCommerce slugs.

    Args:
        products: List of product dicts from WooCommerce API
        catalog_path: Path to current catalog CSV
        output_path: Path to save updated catalog
    """
    # Create slug lookup by product ID
    slug_lookup = {
        str(p['id']): p['slug']
        for p in products
    }

    print(f"\n📝 Updating catalog: {catalog_path}")

    # Read current catalog
    updated_rows = []
    with open(catalog_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for row in reader:
            product_id = row['ID']
            old_slug = row.get('Slug', '')

            # Update slug if we have it from API
            if product_id in slug_lookup:
                new_slug = slug_lookup[product_id]
                if old_slug != new_slug:
                    print(f"   Updated {product_id}: {old_slug} → {new_slug}")
                row['Slug'] = new_slug
            else:
                print(f"   ⚠️  Product {product_id} not found in API response")

            updated_rows.append(row)

    # Write updated catalog
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    print(f"✅ Updated catalog saved to: {output_path}")


def save_api_response(products: List[Dict[str, Any]], output_path: Path):
    """Save raw API response for debugging."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2)
    print(f"💾 Raw API response saved to: {output_path}")


def verify_slugs(products: List[Dict[str, Any]], sample_size: int = 5):
    """
    Verify that fetched slugs are correct by testing URLs.

    Args:
        products: List of product dicts
        sample_size: Number of products to verify
    """
    print(f"\n🔍 Verifying {sample_size} sample product URLs...")

    import random
    samples = random.sample(products, min(sample_size, len(products)))

    for product in samples:
        product_id = product['id']
        slug = product['slug']
        permalink = product.get('permalink', f"{STORE_URL}/product/{slug}/")

        try:
            response = requests.head(permalink, timeout=10, allow_redirects=True)
            status = "✅" if response.status_code == 200 else f"❌ {response.status_code}"
            print(f"   {status} {product_id}: {slug}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {product_id}: {slug} - Error: {e}")


def main():
    """Main execution function."""
    print("=" * 70)
    print("WooCommerce Product Slug Fetcher")
    print("=" * 70)

    # Fetch all products from API
    products = fetch_all_products(per_page=100)

    if not products:
        print("❌ No products fetched. Check API credentials and try again.")
        sys.exit(1)

    # Save raw API response
    api_response_path = Path("data/rogue-herbalist/woocommerce-api-products.json")
    api_response_path.parent.mkdir(parents=True, exist_ok=True)
    save_api_response(products, api_response_path)

    # Verify some slugs
    verify_slugs(products, sample_size=5)

    # Update catalog with correct slugs
    catalog_path = Path("data/rogue-herbalist/minimal-product-catalog.csv")
    output_path = Path("data/rogue-herbalist/minimal-product-catalog-updated-slugs.csv")

    if catalog_path.exists():
        update_catalog_with_slugs(products, catalog_path, output_path)
    else:
        print(f"⚠️  Catalog not found: {catalog_path}")
        print("   Create a new catalog from API response")

        # Create new catalog from API
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['ID', 'Name', 'Slug', 'SKU', 'Permalink', 'Status'])
            writer.writeheader()
            for p in products:
                writer.writerow({
                    'ID': p['id'],
                    'Name': p['name'],
                    'Slug': p['slug'],
                    'SKU': p.get('sku', ''),
                    'Permalink': p.get('permalink', ''),
                    'Status': p.get('status', 'publish')
                })
        print(f"✅ New catalog created: {output_path}")

    print("\n" + "=" * 70)
    print("✅ Done! Next steps:")
    print("   1. Review the updated catalog")
    print("   2. Backup current catalog if needed")
    print("   3. Replace minimal-product-catalog.csv with updated version")
    print("=" * 70)


if __name__ == "__main__":
    main()
