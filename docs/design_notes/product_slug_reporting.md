# Design Note: Use Product Slugs in Reporting

**Date:** 2025-09-29
**Status:** Active Design Principle
**Scope:** All reporting outputs (markdown, HTML, JSON)

## Problem

Reports currently reference products using only product IDs (e.g., "**Product 6664:**"), which are not human-readable and don't provide immediate context about what product is being discussed.

## Solution

**Eagerly use product slugs in all reporting outputs** to improve readability and provide immediate context.

### Examples

**Before:**
```markdown
**Product 6664:** cardiovascular-health
```

**After:**
```markdown
**Product [cardiovascular-health-formula](https://rogueherbalist.com/product/cardiovascular-health-formula/)** (ID: 6664)
```

Or more concise:
```markdown
**[cardiovascular-health-formula](https://rogueherbalist.com/product/cardiovascular-health-formula/):** cardiovascular-health
```

## Implementation

### Reports Affected
1. `classification_report.md` - Product classification analysis
2. `health_quiz_report.md` - Health quiz product recommendations
3. `health_quiz_report.html` - HTML formatted health quiz reports
4. Any other reports that reference products

### Data Requirements
- Product catalog must include `Slug` field (now available from WooCommerce export)
- Report generators must have access to product slug when formatting output
- Slug should be used to construct full product URLs where applicable

### Format Guidelines

**For classification reports:**
```markdown
**[product-slug](https://rogueherbalist.com/product/product-slug/):** category-name
```

**For recommendation reports:**
```markdown
### [Product Name](https://rogueherbalist.com/product/product-slug/)
- **Slug:** product-slug
- **ID:** 1234
- **Category:** category-name
```

**For lists/tables:**
| Product | Category | Relevance |
|---------|----------|-----------|
| [hemp-adapt-2oz](https://rogueherbalist.com/product/hemp-adapt-2oz/) | stress-mood-anxiety | 0.85 |

## Benefits

1. **Improved Readability**: Slugs are human-readable (e.g., "hemp-adapt-2oz" vs "3677")
2. **SEO-Friendly**: Product slugs match actual URL structure
3. **Clickable Links**: Can easily create working product URLs
4. **Better Context**: Immediately understand what product is being referenced
5. **Debugging**: Easier to verify products on actual website

## Migration Notes

- All new reports should use slugs by default
- Existing report generators should be updated to prefer slugs over IDs
- ID should still be included (parenthetically) for database reference
- If slug is missing, fall back to ID with warning

## Related Files

- `src/analysis_engine.py` - Report generation logic
- `src/run_assign_cat.py` - Classification reporting
- `src/run_health_quiz.py` - Health quiz reporting
- `src/product_recommendation_engine.py` - Product URL generation