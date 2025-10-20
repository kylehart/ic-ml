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

**Investigate 0 Product Recommendations Bug**
- **Status**: LLM processing works, but product engine returns 0 matches
- **Symptom**: Email shows "Based on your health needs, we've selected 0 products that may help"
- **Test Case**: "Energy & Vitality" / mental clarity query
- **Expected**: Should return 5 relevant products from 787-product catalog
- **Next Steps**: Debug product recommendation engine scoring and matching logic

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
