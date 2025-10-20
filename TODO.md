# TODO

## Refactor Multi-assignment

**Current State**: 9/761 products (1.2%) have duplicate category assignments, mostly accidental
- 5 products: Exact duplicate rows (bugs)
- 2 products: Same category with/without subcategory (bugs)
- 2 products: Different categories (possibly intentional multi-category)

**Issue**: Prompt asks for "single MOST SPECIFIC slug" but LLM sometimes returns multiple lines per product

**Decision Needed**:
1. Explicitly ask LLM for multiple relevant categories (intentional multi-assignment)?
2. Enforce single-category per product and fix duplicate detection?

**Downstream**: WooCommerce CSV import supports multiple rows per product_id - will merge and assign all categories
