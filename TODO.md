# TODO

## Health Quiz MVP - Production Readiness

### High Priority

**Verify instruction.coach Domain with Resend** ✅ COMPLETED (October 2025)
- **Status**: Domain verified and production email active
- **Implementation**:
  - Domain `instruction.coach` verified in Resend Dashboard with DNS records (SPF, DKIM, DMARC)
  - Updated default email in `src/web_service.py` to `noreply@instruction.coach`
  - Updated `.env.example` to reflect production email
  - Updated all documentation (CLAUDE.md, SYNOPSIS.md) to remove testing email references
- **Production Ready**: All emails now sent from `noreply@instruction.coach`
- **Next Steps**: Update Railway environment variable if still set to testing email

**Investigate 0 Product Recommendations Bug** ✅ COMPLETED (October 2025)
- **Status**: Fixed - two bugs identified and resolved
- **Bug 1**: LLM JSON parsing failure (not using structured output)
  - LLM wrapped JSON in markdown code fences (```json...```)
  - Fixed by using `response_format={"type": "json_object"}`
- **Bug 2**: Product catalog path mismatch (underscore vs hyphen)
  - Code looked for `data/rogue_herbalist/` but directory is `data/rogue-herbalist/`
  - Fixed by translating `client_id.replace('_', '-')`
- **Result**: 0 → 5 product recommendations working
- **Files**: `src/health_quiz_use_case.py:202-246`, `src/product_recommendation_engine.py:338-340`

**Update Product Catalog with Correct WooCommerce Slugs** 📋 NEW (October 2025)
- **Status**: Current catalog has incorrect slugs generating 404 URLs
- **Issue**: Catalog Slug column doesn't match actual WooCommerce product URLs
- **Example**:
  - Catalog slug: `digestive-bitters-formula-2-oz`
  - Generated URL: `https://rogueherbalist.com/product/digestive-bitters-formula-2-oz/` ❌ 404
  - Actual WooCommerce URL: `https://rogueherbalist.com/product/digestive-bitters-formula-2oz-tincture/` ✅
- **Root Cause**: WooCommerce export may not include actual slugs, or slugs changed after export
- **Solution**: Re-export product catalog from WooCommerce or scrape actual product URLs from site
- **Impact**: All 5 product recommendation URLs may be broken
- **Priority**: High - breaks end-to-end user journey (recommendations → purchase)
- **Files**: `data/rogue-herbalist/minimal-product-catalog.csv` (Slug column needs refresh)
- **Next Steps**:
  1. Download fresh WooCommerce product export with actual slugs
  2. Or: Write scraper to match product IDs to actual URLs from live site
  3. Verify all 787 product URLs are valid before deploying to production

### Medium Priority

**Fix Email Double-Entry UX** ✅ COMPLETED (October 2025)
- **Status**: Token-based redirect fully implemented with auto-refresh
- **Implementation**:
  - New endpoint: `GET /results/{token}` with auto-loading and 3-second retry polling
  - API endpoint: `GET /api/v1/results/lookup/token/{token}` for JSON responses
  - Email HTML template includes "View results online" link with token
  - Comprehensive unit tests added (8 new test cases)
  - Fallback email lookup still available at `/results`
- **Next Steps**: Configure Formbricks form to redirect to `https://ic-ml-production.up.railway.app/results/{responseId}`
- **Files Updated**: `src/web_service.py` (lines 575-971, 1008-1038), `tests/test_web_service.py` (lines 539-706)

### Low Priority (Future Enhancements)

**Redesign Health Quiz Prompt to be More Conversational** 📋 PLANNED (Future)
- **Current**: Structured prompt with labeled sections (Health Issue:, Severity:, etc.)
- **Proposed**: Narrative format that reads more naturally to the LLM
- **Example**:
  ```
  "You're helping [firstName if available], a [age_range] person dealing with [primary_area].
  They describe it as: '[health_issue]'.
  They've tried [tried_already], but severity is still [severity]/10.
  Their lifestyle: [lifestyle]"
  ```
- **Benefits**:
  - More human context for LLM reasoning
  - Better understanding of user's situation
  - More empathetic recommendations
- **Considerations**:
  - Keep PII (email/name) out of LLM prompts (current policy)
  - Maintain backward compatibility with framework
  - A/B test to ensure quality doesn't degrade
- **Files**: `src/health_quiz_use_case.py` (lines 172-234: `get_prompt_template()` method)
- **Decision Date**: October 21, 2025 - deferred for future enhancement

**Expand Unit Test Coverage** ✅ COMPLETED (October 2025)
- **Status**: 122 passing tests covering core modules (100% pass rate)
- **Coverage**: product_recommendation_engine (28 tests), health_quiz_use_case (27), model_config (21), llm_client (20), web_service (26)
- **Future**: Add pytest-cov for coverage metrics, expand edge case testing

**Complete Admin Endpoints**
- **Status**: `/api/v1/admin/clients` lacks authentication enforcement
- **Current**: Placeholder comment "In production, this would require admin authentication"
- **Solution**: Add proper admin role checking before production use
- **Files**: `src/web_service.py` lines ~1208

**Implement Usage Statistics Database**
- **Status**: `/api/v1/usage/{client_id}` returns mock data
- **Current**: Comment "In production, this would query a usage database"
- **Solution**: Connect to PostgreSQL or similar for real usage tracking
- **Files**: `src/web_service.py` lines ~1181

## Product Classification

### Refactor Multi-assignment

**Current State**: 9/761 products (1.2%) have duplicate category assignments, mostly accidental
- 5 products: Exact duplicate rows (bugs)
- 2 products: Same category with/without subcategory (bugs)
- 2 products: Different categories (possibly intentional multi-category)

**Issue**: Prompt asks for "single MOST SPECIFIC slug" but LLM sometimes returns multiple lines per product

**Decision Needed**:
1. Explicitly ask LLM for multiple relevant categories (intentional multi-assignment)?
2. Enforce single-category per product and fix duplicate detection?

**Downstream**: WooCommerce CSV import supports multiple rows per product_id - will merge and assign all categories
