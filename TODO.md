# TODO

## Health Quiz MVP - Production Readiness

### High Priority

**Verify instruction.coach Domain with Resend**
- **Status**: Blocking production email delivery
- **Current**: Using `onboarding@resend.dev` (testing email)
- **Needed**: Verify `instruction.coach` domain in Resend Dashboard
- **Steps**:
  1. Go to [Resend Dashboard → Domains](https://resend.com/domains)
  2. Add `instruction.coach` domain
  3. Configure DNS records (SPF, DKIM, DMARC)
  4. Verify domain
  5. Update Railway variable: `RESEND_FROM_EMAIL=no-reply@instruction.coach`

**Investigate 0 Product Recommendations Bug**
- **Status**: LLM processing works, but product engine returns 0 matches
- **Symptom**: Email shows "Based on your health needs, we've selected 0 products that may help"
- **Test Case**: "Energy & Vitality" / mental clarity query
- **Expected**: Should return 5 relevant products from 787-product catalog
- **Next Steps**: Debug product recommendation engine scoring and matching logic

### Medium Priority

**Fix Email Double-Entry UX**
- **Status**: Token-based storage infrastructure exists but not used in redirect
- **Current**: User enters email in form, then again on results page
- **Solution**: Update Formbricks ending card redirect to use token URL: `/results/{token}`
- **Files**: Update `src/web_service.py` results page endpoint to support token-based lookup

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
