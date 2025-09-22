#!/usr/bin/env python3
"""
Test generated URLs against real Rogue Herbalist website.
"""

import sys
sys.path.append('src')
import requests
from product_recommendation_engine import ProductCatalogItem

# Test cases with titles from our catalog
test_products = [
    {'id': '3677', 'title': 'Hemp Adapt 2oz.'},
    {'id': '1111', 'title': 'Four Mushroom Immune Complex 2oz.'},
    {'id': '3678', 'title': 'Hemp Bitters 2oz.'},
    {'id': '1115', 'title': 'Women\'s Daily Tonic 2oz.'},
    {'id': '1117', 'title': 'Men\'s Daily Tonic Tincture 2oz'},
    {'id': '1119', 'title': 'Energy Tonic 2oz.'},
]

def test_url(url):
    """Test if a URL returns 200 (success) or 404 (not found)."""
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except:
        return False

def test_generated_urls():
    """Test our generated URLs against the real website."""
    print("Testing Generated URLs Against Real Website")
    print("=" * 55)

    success_count = 0
    total_count = len(test_products)

    for i, prod in enumerate(test_products, 1):
        print(f"\nTest {i}: {prod['title']}")

        # Create product and generate URL
        product = ProductCatalogItem(
            id=prod['id'],
            title=prod['title'],
            description="Test"
        )

        generated_slug = product.generate_slug()
        generated_url = f"https://rogueherbalist.com/product/{generated_slug}/"

        # Test the URL
        works = test_url(generated_url)

        if works:
            success_count += 1
            print(f"  ✅ SUCCESS: {generated_url}")
        else:
            print(f"  ❌ FAILED:  {generated_url}")

    print(f"\n" + "=" * 55)
    print(f"Results: {success_count}/{total_count} URLs work ({success_count/total_count*100:.1f}%)")

    return success_count, total_count

if __name__ == "__main__":
    test_generated_urls()