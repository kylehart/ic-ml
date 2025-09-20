# WordPress WooCommerce URL Structure Research

## Overview

Research conducted to understand how WordPress and WooCommerce create product URLs based on product IDs, to ensure proper URL generation in the Health Quiz recommendation system.

## Key Findings

### WooCommerce Product URL Patterns

WooCommerce offers several permalink structure options configurable in **WordPress > Settings > Permalinks**:

#### 1. Default Product Base Pattern
- **Format**: `example.com/product/product-name/`
- **Usage**: Most common WordPress/WooCommerce setup
- **SEO**: Good for SEO with readable product names in URLs

#### 2. Plain Permalinks (ID-based)
- **Format**: `example.com/?product=123`
- **Usage**: When not using pretty permalinks
- **Benefits**: Direct product ID in URL, works with any setup

#### 3. Shop Base Pattern
- **Format**: `example.com/shop/product-name/`
- **Usage**: When shop page is used as base

#### 4. Shop Base with Category
- **Format**: `example.com/shop/category/product-name/`
- **Usage**: Hierarchical structure with categories

#### 5. Custom Patterns
- **Format**: `example.com/product/product-name-123/`
- **Usage**: Custom implementations combining name and ID

### WordPress Functions for URL Generation

#### Primary Method: `get_permalink()`
```php
$product_id = 123;
$product_url = get_permalink($product_id);
```

#### WooCommerce Product Object Method
```php
$wc_product = new WC_Product($product_id);
$product_url = $wc_product->get_permalink();
```

#### From Product Object
```php
global $product;
$product_url = get_permalink($product->get_id());
```

## Implementation Recommendations

### For External Systems (like Health Quiz)

Since external systems don't have access to WordPress functions, URL templates are necessary:

#### Recommended Primary Pattern
```yaml
product_url_template: "https://rogueherbalist.com/product/{product_id}"
```
- Follows WordPress/WooCommerce standard
- Good for SEO
- Most compatible

#### Alternative Patterns for Different Setups
```yaml
# Plain permalinks (guaranteed to work)
product_url_template: "https://rogueherbalist.com/?product={product_id}"

# Shop base
product_url_template: "https://rogueherbalist.com/shop/{product_id}"

# Custom products base
product_url_template: "https://rogueherbalist.com/products/{product_id}"
```

### Important Configuration Notes

1. **Permalink Base Uniqueness**: WordPress requires permalink bases to be unique. Don't set product base to "shop" if product category base is also "shop".

2. **SEO Considerations**: Keep URLs simple and remove unnecessary components. Product URLs should contain only essential information.

3. **Migration Compatibility**: If migrating from another platform, consider maintaining existing URL structures for SEO continuity.

## Configuration Implementation

### Current Configuration
```yaml
health_quiz:
  # WordPress/WooCommerce URL Configuration
  product_url_template: "https://rogueherbalist.com/product/{product_id}"

  # Alternative patterns commented for reference:
  # product_url_template: "https://rogueherbalist.com/?product={product_id}"  # Plain permalinks
  # product_url_template: "https://rogueherbalist.com/shop/{product_id}"     # Shop base
  # product_url_template: "https://rogueherbalist.com/products/{product_id}"  # Custom base
```

### Multi-Client Support

Different clients can use different URL patterns:

```yaml
clients:
  rogue_herbalist:
    product_url_template: "https://rogueherbalist.com/product/{product_id}"

  another_client:
    product_url_template: "https://anotherclient.com/shop/{product_id}"
```

## Testing Results

URLs generated with the current configuration:
- `https://rogueherbalist.com/product/3678` (Hemp Bitters)
- `https://rogueherbalist.com/product/9104` (Ginger Root Capsules)
- `https://rogueherbalist.com/product/9083` (Digestive Bitters Formula)

## Recommendations

1. **Use Standard Pattern**: The `/product/{product_id}` pattern is most compatible with standard WooCommerce setups.

2. **Provide Alternatives**: Keep commented alternatives in configuration for easy switching if client setup differs.

3. **Client Verification**: For production deployment, verify the actual permalink structure with the client's WordPress/WooCommerce setup.

4. **Fallback Option**: Plain permalinks (`/?product={product_id}`) work universally as a fallback option.

This research ensures the Health Quiz system generates proper URLs that work with standard WordPress/WooCommerce installations while providing flexibility for different client configurations.