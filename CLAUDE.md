# IC-ML Project - Claude Code Context

## Project Overview
Multi-use case LLM platform supporting herbal product classification and health quiz recommendations with client-aware cost tracking.

**Current Status**: Production-ready classification system AND fully functional Health Quiz with working product URLs and HTML reports.

## Common Commands

### Product Classification (PRODUCTION - 100% Valid Output)
```bash
# Full catalog processing with automatic slug validation
python src/run_assign_cat.py --input data/rogue-herbalist/minimal-product-catalog.csv --taxonomy data/rogue-herbalist/latest-best-taxonomy.xml

# Single product test
python src/run_assign_cat.py --single-product "Echinacea Immune Support" --taxonomy data/rogue-herbalist/latest-best-taxonomy.xml

# Model comparison
python src/run_assign_cat.py --model gpt4o_mini --input products.csv --taxonomy data/rogue-herbalist/latest-best-taxonomy.xml
python src/run_assign_cat.py --model haiku --input products.csv --taxonomy data/rogue-herbalist/latest-best-taxonomy.xml

# Reanalyze existing run
python src/reanalyze_assign_cat.py runs/assign-cat-YYYY-MM-DD-HHMMSS

# KEY FEATURES:
# ✅ Post-processing validation ensures 100% valid slugs
# ✅ Automatic correction of common LLM hallucinations
# ✅ Raw and corrected outputs saved separately
# ✅ Full audit trail in validation_report.json
```

### Health Quiz (PRODUCTION READY)
```bash
# Test with real user personas (5 available)
python src/run_health_quiz.py --persona "Sarah Chen"        # Digestive health - TESTED
python src/run_health_quiz.py --persona "Marcus Rodriguez"  # Joint pain
python src/run_health_quiz.py --persona "Lisa Thompson"     # Stress/sleep

# Custom health scenarios
python src/run_health_quiz.py --custom-input "Frequent headaches" --primary-area "stress_relief"

# Model cost comparison ($0.0003 vs higher)
python src/run_health_quiz.py --persona "Sarah Chen" --model gpt4o_mini
python src/run_health_quiz.py --persona "Sarah Chen" --model haiku

# RECENT UPDATES - Working Features:
# ✅ Generates working product URLs: https://rogueherbalist.com/product/{slug}/
# ✅ Creates both .md and .html reports with professional styling
# ✅ 100% tested success rate on URL generation (6/6 products tested)
# ✅ Enhanced product catalog with 787 generated slugs
```

### Health Quiz MVP Deployment (NEW - October 2025)
```bash
# Local testing with web service
uvicorn src.web_service:app --reload --port 8000

# Test with ngrok for webhook testing
ngrok http 8000

# Deploy to Railway (automatic from GitHub)
# 1. Connect GitHub repo to Railway
# 2. Add environment variables:
#    - OPENAI_API_KEY (or ANTHROPIC_API_KEY)
#    - RESEND_API_KEY
#    - RESEND_FROM_EMAIL=onboarding@resend.dev (testing) or no-reply@instruction.coach (production)
# 3. Railway auto-deploys from Dockerfile

# KEY ENDPOINTS:
# POST /api/v1/webhook/formbricks - Receives Formbricks submissions
# GET /results - Email lookup page for users
# POST /api/v1/results/lookup - API for fetching results
# GET /health - Health check endpoint

# MVP ARCHITECTURE:
# ✅ Formbricks webhook → Railway endpoint → Background processing
# ✅ Email-based results lookup (24hr expiration)
# ✅ Resend email delivery with HTML reports
# ✅ In-memory storage (upgrade to PostgreSQL in Phase 2)
# ✅ Complete deployment guide: docs/railway_formbricks_deployment_guide.md
```

### Cost Tracking
```python
# Get client cost breakdown (automatic in all runs)
client = LLMClient("gpt4o_mini")
cost_data = client.get_cost_breakdown_for_reporting()

# Check billing data
ls runs/*/outputs/client_cost_breakdown.json
```

## Code Architecture

### Core Files (ACTIVE)
- `src/llm_client.py` - LLM interface with client-aware cost tracking
- `src/run_assign_cat.py` - Product classification experimental runner (PRODUCTION)
- `src/run_health_quiz.py` - Health quiz experimental runner (PRODUCTION READY)
- `src/analysis_engine.py` - Modular analysis with markdown reporting
- `config/models.yaml` - Central model config with use case settings

### Multi-Use Case Framework (WORKING)
- `src/use_case_framework.py` - Abstract base classes for multi-use case support
- `src/health_quiz_use_case.py` - Health quiz implementation with LLM integration
- `src/product_recommendation_engine.py` - 787-product catalog with intelligent scoring

### Test Data (READY TO USE)
- `data/health-quiz-samples/user_personas.json` - 5 realistic personas for testing
- `data/rogue-herbalist/minimal-product-catalog.csv` - 787 products with generated URL slugs

### Output Files (ENHANCED)

**Health Quiz:**
- `health_quiz_report.md` - Markdown report with proper markdown links
- `health_quiz_report.html` - Professional styled HTML report
- `product_recommendations.json` - JSON with working purchase URLs
- `client_cost_breakdown.json` - Billing-ready cost attribution

**Product Classification:**
- `classifications.csv` - Final validated classifications (100% valid slugs)
- `classifications_raw.csv` - LLM output before validation
- `classification_report.md` - Analysis with distribution charts
- `validation_report.json` - Complete audit trail of corrections
- `client_cost_breakdown.json` - Billing-ready cost attribution

## Recent Achievements (September-October 2025)

### ✅ Post-Processing Slug Validation (NEW - October 2025)
- **Architecture**: Separation of concerns - LLM for semantic understanding, code for validation
- **Success Rate**: 100% valid slugs in final output (was 2.8% error rate)
- **Simplified LLM Task**: LLM outputs single `best_slug` instead of `category_slug,subcategory_slug`
- **Automatic Hierarchy Resolution**: Post-processing determines if slug is primary/subcategory and adds parent automatically
- **Auto-Correction**: Fuzzy matching + title-to-slug mapping corrects ~2% of LLM hallucinations
- **Audit Trail**: Complete record of all corrections in `validation_report.json`
- **Methods**:
  - Hierarchical mapping: subcategory → auto-add parent category
  - Title-to-slug mapping for common conversions
  - Fuzzy matching with 80% threshold
  - Invalid slugs cleared rather than guessed

### ✅ Working Product URLs
- **Algorithm**: 100% success rate on tested URLs (6/6 products work)
- **Catalog Enhancement**: Added slug field to all 787 products
- **URL Pattern**: `https://rogueherbalist.com/product/{generated-slug}/`
- **Examples**: `hemp-adapt-2oz`, `four-mushroom-immune-complex-2oz`

### ✅ HTML Report Generation
- **Package**: `markdown` with extensions (extra, codehilite, toc, nl2br)
- **Styling**: Professional CSS with responsive design
- **Links**: Clickable product purchase links in HTML output
- **Formats**: Both `.md` and `.html` generated automatically

### ✅ End-to-End Customer Journey
- Health concern input → LLM processing → Product recommendations → **Working purchase URLs**
- Complete journey from health quiz to Rogue Herbalist product pages
- Cost: $0.0003 per interaction with 5 product recommendations

## Development Guidelines

### Code Style
- **IMPORTANT**: Always use experimental run framework for LLM experiments
- **MUST**: Include client tracking metadata in all LLM calls (automatic via LLMClient)
- Use absolute paths for file operations
- Follow existing patterns in `run_health_quiz.py` for new use cases

### Validation Architecture (NEW - October 2025)
- **Principle**: LLMs for semantic understanding, code for deterministic validation
- **Pattern**: Always save raw LLM output + corrected output + validation report
- **When to use post-processing**: Whenever LLM output must match exact values (slugs, IDs, codes)
- **LLM Task Simplification**: Ask LLM for single best match, let code handle structural requirements (hierarchy, parents)
- **Example**: See `validate_and_correct_slugs()` in `run_assign_cat.py:239-507`

### Known Issues
- **Multi-Assignment**: 1.2% of products get duplicate category assignments (9/761 products)
  - 5 products: Exact duplicates (bug)
  - 2 products: Same category with/without subcategory (bug)
  - 2 products: Different categories (possibly intentional)
  - See TODO.md for refactoring plan

### Cost Management
- All LLM calls automatically tagged with client, use_case, project, environment
- Health Quiz: ~$0.0003 per interaction (5x cheaper than classification)
- Product Classification: ~$0.0015 per product
- Use `get_cost_breakdown_for_reporting()` for billing data

### Testing Workflow
1. Test with single personas first: `--persona "Sarah Chen"`
2. Compare models for cost optimization
3. Use reanalysis tools for iterative development
4. Check `runs/*/outputs/health_quiz_report.html` for styled reports with clickable links

### Updating Product Catalog
When updating the product catalog from WooCommerce:
1. Export products from WooCommerce admin (Products > All Products > Export)
2. WooCommerce export includes all necessary fields including product slugs
3. Run `python3 transform_catalog.py` to clean newlines and format for use
4. The catalog now includes real WooCommerce slugs (no generation needed)

## Configuration (CURRENT)

### Models (config/models.yaml)
- **Default**: gpt-4o-mini (cost-optimized for both use cases)
- **Health Quiz**: Configured with consultation threshold, URL patterns
- **Client Tracking**: Automatic via LiteLLM metadata integration

### Use Case Settings
```yaml
health_quiz:
  default_model: "openai/gpt-4o-mini"
  max_recommendations: 5
  min_relevance_score: 0.3
  consultation_threshold: 7
  product_url_template: "https://rogueherbalist.com/product/{product_id}"
```

## Working Features (TESTED)

### Health Quiz
- ✅ Real user persona processing (Sarah Chen tested)
- ✅ LLM-powered health recommendations (3-5 evidence-based points)
- ✅ Product catalog integration (799 products from WooCommerce, 5 recommendations)
- ✅ WordPress/WooCommerce URLs using real slugs from WooCommerce
- ✅ Safety features (consultation recommendations for severity ≥7)
- ✅ Cost tracking ($0.0003 per interaction)
- ✅ Markdown and HTML report generation

### Product Classification (PRODUCTION - 100% Valid Output)
- ✅ Batch processing (10 products/batch, 20x speed improvement)
- ✅ Full taxonomy integration with 87 valid slugs
- ✅ **Post-processing validation** - 100% valid slug output
- ✅ **Auto-correction** - Fuzzy matching + title-to-slug mapping
- ✅ **Audit trail** - Complete correction log in validation_report.json
- ✅ Cost optimization ($0.0015 per product, ~$1.20 for 799 products)
- ✅ Multi-provider support (OpenAI, Anthropic)
- ✅ Analysis engine with markdown reports
- ✅ Experimental run framework with full artifact capture

## Quick Debug Commands

### Check Recent Runs
```bash
ls -la runs/  # All experimental runs
ls runs/health-quiz-*/outputs/  # Health quiz outputs
ls runs/assign-cat-*/outputs/  # Classification outputs

# Check validation reports
cat runs/assign-cat-*/outputs/validation_report.json | python3 -m json.tool
```

### Verify Classification Quality
```bash
# Compare raw vs corrected classifications
diff runs/assign-cat-YYYY-MM-DD-HHMMSS/outputs/classifications_raw.csv \
     runs/assign-cat-YYYY-MM-DD-HHMMSS/outputs/classifications.csv

# Count corrections made
cat runs/assign-cat-YYYY-MM-DD-HHMMSS/outputs/validation_report.json | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Corrections: {len(d[\"corrections\"])}')"
```

### Open Results in TextEdit
```bash
open -a textedit runs/health-quiz-YYYY-MM-DD-HHMMSS/outputs/health_quiz_report.md
open -a textedit runs/assign-cat-YYYY-MM-DD-HHMMSS/outputs/classification_report.md
open -a textedit runs/assign-cat-YYYY-MM-DD-HHMMSS/outputs/validation_report.json
```

### Test Product Catalog Loading
```python
from src.product_recommendation_engine import ProductRecommendationEngine
engine = ProductRecommendationEngine('rogue_herbalist')
print(engine.get_catalog_stats())  # Should show 787 products, all in stock
```

## Current Development State
- **Health Quiz**: PRODUCTION READY - working end-to-end with real testing
- **Product Classification**: PRODUCTION - 100% valid slug output with auto-correction
- **Taxonomy Generation**: PRODUCTION - 87-element taxonomy with SEO metadata
- **Web Service**: Architectural design complete, needs deployment redesign
- **Multi-Client**: Framework ready, tested with rogue_herbalist config

## Important Files to Monitor

**Cost & Billing:**
- `runs/*/outputs/client_cost_breakdown.json` - Billing-ready cost attribution

**Classification Quality:**
- `runs/assign-cat-*/outputs/classifications.csv` - Final validated output (100% valid)
- `runs/assign-cat-*/outputs/validation_report.json` - Auto-correction audit trail
- `runs/assign-cat-*/outputs/classification_report.md` - Analysis and distribution

**Configuration & Data:**
- `config/models.yaml` - Use case configuration
- `data/rogue-herbalist/latest-best-taxonomy.xml` - Current taxonomy (87 slugs)
- `data/health-quiz-samples/user_personas.json` - Test scenarios

## Maintaining This File

To keep CLAUDE.md current, use this prompt:

```
Sync CLAUDE.md with current codebase. Focus on:
1. Commands that actually work RIGHT NOW
2. Current file status (production ready vs in development)
3. Real test data and working examples
4. Active cost tracking patterns
```

**Remember**: This file should reflect what's ACTUALLY working, not planned features. Keep it under ~200 lines and focused on immediate coding needs.