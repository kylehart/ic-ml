#!/usr/bin/env python3
"""
Test script for product slug generation.
Tests algorithmic slug generation against known working URLs.
"""

import sys
sys.path.append('src')

from product_recommendation_engine import ProductCatalogItem

# Test cases with known working URLs
test_cases = [
    {
        'title': 'Hemp Adapt 2oz.',
        'expected_slug': 'hemp-adapt-2oz',
        'expected_url': 'https://rogueherbalist.com/product/hemp-adapt-2oz/',
        'product_id': '3677'
    },
    {
        'title': 'Four Mushroom Immune Complex 2oz.',
        'expected_slug': 'four-mushroom-immune-complex-2oz',
        'expected_url': 'https://rogueherbalist.com/product/four-mushroom-immune-complex-2oz/',
        'product_id': '1111'
    },
    {
        'title': 'SoMush Honey Vanilla Mushroom \'Coffee\' 3.5oz.',
        'expected_slug': 'honey-vanilla-mushroom-coffee-3oz',  # Note: your example had 3oz not 35oz
        'expected_url': 'https://rogueherbalist.com/product/honey-vanilla-mushroom-coffee-3oz/',
        'product_id': '6834'
    },
    {
        'title': 'Hemp Bitters 2oz.',
        'expected_slug': 'hemp-bitters-2oz',
        'expected_url': 'https://rogueherbalist.com/product/hemp-bitters-2oz/',
        'product_id': '3678'
    },
    {
        'title': 'Women\'s Daily Tonic 2oz.',
        'expected_slug': 'womens-daily-tonic-2oz',
        'expected_url': 'https://rogueherbalist.com/product/womens-daily-tonic-2oz/',
        'product_id': '1115'
    }
]

def test_slug_generation():
    """Test slug generation against known examples."""
    print("Testing Product Slug Generation")
    print("=" * 50)

    success_count = 0
    total_count = len(test_cases)

    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {case['title']}")

        # Create product object
        product = ProductCatalogItem(
            id=case['product_id'],
            title=case['title'],
            description="Test description"
        )

        # Generate slug
        generated_slug = product.generate_slug()
        expected_slug = case['expected_slug']

        # Test result
        is_match = generated_slug == expected_slug
        if is_match:
            success_count += 1
            print(f"  ✅ PASS: Generated '{generated_slug}'")
        else:
            print(f"  ❌ FAIL: Generated '{generated_slug}', expected '{expected_slug}'")

        # Show expected URL
        generated_url = f"https://rogueherbalist.com/product/{generated_slug}/"
        print(f"  URL: {generated_url}")

    print(f"\n" + "=" * 50)
    print(f"Results: {success_count}/{total_count} tests passed ({success_count/total_count*100:.1f}%)")

    if success_count == total_count:
        print("🎉 All tests passed! Slug generation is working correctly.")
    else:
        print("⚠️  Some tests failed. Algorithm needs refinement.")

if __name__ == "__main__":
    test_slug_generation()