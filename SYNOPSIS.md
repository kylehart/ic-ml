# IC-ML Project Synopsis

## Project Overview

**Goal**: Multi-use case LLM-powered platform supporting herbal product classification, customer health quiz recommendations, and taxonomy/SEO content generation with client-aware cost tracking.

**Business Context**: Originally built for "Get Better Care" client processing ~800 herbal products for classification at $2.43 per 1000 products. Now expanded to support:
- Customer-facing Health Quiz feature for Rogue Herbalist with personalized product recommendations
- Taxonomy generation for e-commerce category structure and descriptions
- SEO metadata generation for categories and products

**Current Status**: Production-ready classification system, **fully deployed Health Quiz MVP** on Railway with Formbricks integration and Resend email delivery, and taxonomy/SEO generation framework with experimental runners.

## Key Achievements

**Core Infrastructure:**
- **Multi-Use Case Architecture**: Abstract framework supporting batch classification, real-time recommendations, and document generation
- **Client-Aware Cost Tracking**: Automatic attribution of all LLM costs by client, use case, project, and environment using LiteLLM metadata
- **Experimental Framework**: Complete run management with artifact capture and reproducibility
- **Multi-Provider Integration**: 6+ models across OpenAI/Anthropic with seamless switching and cost optimization

**Product Classification (Production):**
- **Batch Processing Optimization**: 20x speed improvement (3.2s vs 84s for 10 products)
- **Cost-Effective Classification**: $0.0015 per product using GPT-4o-Mini with full taxonomy
- **Full Taxonomy Integration**: 20-category herbal taxonomy (optimized from 88KB to 36KB)
- **Post-Processing Validation (October 2025)**: 100% valid slugs (from 2.8% error rate) with automatic hierarchy resolution
  - Simplified LLM task: single `best_slug` output instead of category/subcategory pairs
  - Automatic parent category detection and insertion for subcategories
  - Fuzzy matching and title-to-slug mapping for LLM hallucination correction
- **Modular Analysis Engine**: Human-readable markdown reports with cost breakdowns

**Health Quiz (Production - Deployed):**
- **Real-time Recommendations**: LLM-powered health guidance with product matching ($0.0003 per interaction)
- **Working Product URLs**: 100% tested success rate with WordPress/WooCommerce slug generation
- **HTML Report Generation**: Professional styled reports with clickable product links
- **End-to-End Testing**: Successfully tested with 5 realistic user personas
- **Rogue Herbalist Branding**: Complete green color scheme matching rogueherbalist.com design language

**Health Quiz MVP Deployment (October 2025):**
- **Railway Deployment**: Containerized FastAPI service with automatic GitHub deployments
- **Formbricks Integration**: Webhook-based form submission with verified question ID mappings for all 7 fields
- **Email-Based Results**: Email lookup page with auto-retry polling (token-based auto-loading not supported by Formbricks)
- **Resend Email Service**: HTML email delivery using `noreply@instruction.coach` (production - verified domain)
- **Results Page Polling**: Separate retry counters for different states (webhook arrival, LLM processing, network errors)
- **In-Memory Storage**: MVP uses in-memory dict with dual access (email hash + response token), upgrade path to PostgreSQL documented
- **Cost-Effective**: $0/month on free tiers (Railway $5 credit, Resend 3000 emails/month, Formbricks unlimited)
- **Branded Experience**: Consistent green branding with Google Fonts across all touchpoints

**Taxonomy & SEO Generation (September 2025):**
- **Document Generation Framework**: Abstract framework for multi-element XML document generation
- **Taxonomy Generation**: Automated category descriptions and ingredient lists with character limit enforcement
- **SEO Metadata Generation**: Separate use case generating focus keywords, meta descriptions, Open Graph tags, canonical URLs
- **Two-Pass Architecture**: Split taxonomy content from SEO to work around 16K output token limits
- **URL Validation**: HTTP HEAD requests to verify canonical URLs work
- **Idempotent Operations**: Re-running SEO generation replaces existing metadata cleanly

## Architecture Overview

### Multi-Use Case Framework

1. **Use Case Abstraction** (`src/use_case_framework.py`)
   - Abstract base classes for `UseCase`, `RealtimeUseCase`, `BatchUseCase`
   - Standardized result containers and configuration management
   - Registry system for easy use case registration and discovery

2. **LLM Client** (`src/llm_client.py`)
   - Unified interface for OpenAI and Anthropic models via LiteLLM
   - **Client-aware cost tracking** with automatic metadata tagging
   - Support for both async and sync operations
   - Built-in cost breakdown reporting for billing systems

3. **Configuration System** (`config/models.yaml` + `src/model_config.py`)
   - Centralized model definitions with client tracking metadata
   - Runtime override support for experiments
   - Cost-tier organization and multi-client settings
   - Per-use-case configuration (health_quiz, product_classification, taxonomy_generation, seo_generation)

### Use Case Implementations

4. **Product Classification** (`src/run_assign_cat.py`)
   - Production-ready batch processing with experimental run management
   - Complete artifact capture (inputs, config, outputs, metadata)
   - Integration with modular analysis engine and cost tracking

5. **Health Quiz** (`src/health_quiz_use_case.py`, `src/run_health_quiz.py`)
   - Real-time health recommendation processing
   - Structured input/output with safety features (consultation detection)
   - Integration with product recommendation engine
   - HTML and markdown report generation with Rogue Herbalist branding

6. **Product Recommendation Engine** (`src/product_recommendation_engine.py`)
   - Multi-factor scoring: health categories, ingredients, text similarity
   - Category mapping system connecting health concerns to products
   - Configurable recommendation thresholds and ranking
   - 787-product catalog with working WordPress/WooCommerce URLs

7. **Document Generation Framework** (`src/document_generation_framework.py`)
   - Abstract base classes for XML document generation use cases
   - Element-level and chunk-level processing strategies
   - Validation, merging, and reporting infrastructure
   - Shared by taxonomy and SEO generation

8. **Taxonomy Generation** (`src/run_taxonomy_gen.py`)
   - Automated generation of category descriptions and ingredient lists
   - Chunk-based processing for large taxonomies (chunk_size=3)
   - Character limit enforcement (280 chars primary, 150 chars subcategory)
   - Natural, benefit-focused descriptions (no forced ingredient mentions)
   - Cost: ~$0.49 for 87 elements (20 primary + 67 subcategories)

9. **SEO Generation** (`src/seo_generation_framework.py`, `src/run_seo_gen.py`)
   - Separate use case for SEO metadata (focus-keyword, meta-title, meta-description, h1, og-title, og-description, keywords, canonical-url, schema-type)
   - Single-element processing (no chunking needed)
   - Strict character limit validation (focus-keyword: 40, meta-title: 60, keywords: 120, etc.)
   - URL validation with HTTP HEAD requests
   - Idempotent: re-running replaces existing `<seo>` blocks
   - XML entity encoding for unescaped ampersands

### Supporting Infrastructure

10. **Analysis Engine** (`src/analysis_engine.py`)
    - Modular analysis components with markdown reporting
    - LiteLLM-based cost calculation using live pricing data
    - Model comparison analysis with savings calculations

11. **Web Service API** (`src/web_service.py`) - *Production Deployed*
    - FastAPI-based REST endpoints for Health Quiz (Formbricks webhook, results lookup)
    - In-memory storage with email hashing for privacy and dual token access
    - Resend email integration for HTML report delivery with branded templates
    - Background task processing for non-blocking webhook responses
    - Deployed on Railway with automatic GitHub integration
    - Rogue Herbalist branded HTML templates (email, web results pages, processing pages)

## Code Organization

### Source Code (`src/`) - 15 Files, 7,414 Lines

```
src/
├── use_case_framework.py                # Abstract use case framework and registry (488 lines)
├── document_generation_framework.py     # Abstract framework for XML document generation (512 lines)
├── health_quiz_use_case.py              # Health quiz implementation with LLM integration (278 lines)
├── run_health_quiz.py                   # Health quiz experimental runner (408 lines)
├── run_taxonomy_gen.py                  # Taxonomy generation runner (474 lines)
├── seo_generation_framework.py          # SEO generation framework (634 lines)
├── run_seo_gen.py                       # SEO generation runner (407 lines)
├── product_recommendation_engine.py     # Intelligent product matching system (421 lines)
├── web_service.py                       # FastAPI web service - PRODUCTION (1,411 lines)
├── run_assign_cat.py                    # Product classification runner (715 lines)
├── llm_client.py                        # LLM interface with client-aware cost tracking (473 lines)
├── model_config.py                      # Configuration management with client metadata (241 lines)
├── analysis_engine.py                   # Modular analysis with markdown reporting (626 lines)
├── reanalyze_assign_cat.py              # Post-classification analysis tool (178 lines)
└── product_processor.py                 # Product data structures and batch processing (148 lines)
```

**Code Organization by Function:**
- **Core Infrastructure** (862 lines): `llm_client.py`, `model_config.py`, `product_processor.py`
- **Frameworks** (1,634 lines): `use_case_framework.py`, `document_generation_framework.py`, `seo_generation_framework.py`
- **Use Cases** (1,325 lines): `health_quiz_use_case.py`, `product_recommendation_engine.py`, `analysis_engine.py`
- **Runners** (2,182 lines): `run_assign_cat.py`, `run_health_quiz.py`, `run_seo_gen.py`, `run_taxonomy_gen.py`, `reanalyze_assign_cat.py`
- **Web Service** (1,411 lines): `web_service.py` (FastAPI with 15+ endpoints)

### Prompts (`prompts/`)

```
prompts/
├── README.md                    # Prompts directory documentation
├── taxonomy-gen-prompt.md       # Taxonomy generation prompt with natural description guidelines
└── seo-gen-prompt.md            # SEO generation prompt with strict character limit enforcement
```

### Configuration (`config/`)

```
config/
└── models.yaml                  # Central model configuration
    ├── default: gpt-4o-mini (cost-optimized)
    ├── models: 6+ models across 2 providers
    ├── experiments: custom configurations
    ├── use_cases:
    │   ├── health_quiz: max_recommendations, consultation_threshold, product_url_template
    │   ├── product_classification: taxonomy settings
    │   ├── taxonomy_generation: chunk_size=3, max_tokens=4000
    │   └── seo_generation: field specs, url_templates, validate_urls
    ├── client_tracking: automatic metadata for cost attribution
    └── api: retry and rate limiting settings
```

### Deployment Files (October 2025)

```
.
├── Dockerfile                       # Railway deployment container configuration
├── railway.json                     # Railway service configuration with health checks
├── requirements.txt                 # Python dependencies (FastAPI, Resend, httpx, etc.)
├── .env.example                     # Environment variables template with Resend config
├── MVP_QUICKSTART.md                # Quick deployment guide (5 steps, 2 hours)
├── FORMBRICKS_IDS_VERIFIED.md       # Formbricks question/choice ID verification report
└── docs/
    ├── railway_formbricks_deployment_guide.md  # Complete deployment guide
    └── formbricks_api_integration.md           # Formbricks Management API integration guide
```

### Data (`data/`)

```
data/rogue-herbalist/
├── taxonomy_trimmed.xml                  # Optimized taxonomy structure (60% smaller, 36KB)
├── taxonomy_first1.xml                   # Small test taxonomy (6 elements)
├── taxonomy_first2.xml                   # Larger test taxonomy
├── latest-best-taxonomy-descriptions.xml # Generated taxonomy with natural descriptions
├── latest-best-taxonomy-with-seo.xml     # Taxonomy with SEO metadata (partial - 47/87 succeeded)
├── minimal-product-catalog.csv           # Enhanced 787-product catalog with generated URL slugs
├── wc-product-export-29-9-2025-*.csv     # WooCommerce product export with real slugs
└── [various CSV examples]                # Sample data formats

data/health-quiz-samples/
└── user_personas.json                    # 5 realistic user personas for Health Quiz testing
                                          # (Sarah Chen, Marcus Rodriguez, Lisa Thompson, Robert Kim, Jennifer Walsh)
```

### Documentation (`docs/`)

```
docs/
├── railway_formbricks_deployment_guide.md  # Complete MVP deployment guide (Railway + Formbricks + Resend)
├── formbricks_api_integration.md            # Formbricks Management API guide with extraction script
├── taxonomy_generation_guide.md            # Taxonomy generation documentation
├── multi_client_architecture_design.md     # Multi-client platform design
├── health_quiz_user_stories.md             # Health quiz business requirements
├── implementation_guide.md                 # Original deployment and setup guide
├── wordpress_woocommerce_url_research.md   # WordPress/WooCommerce URL patterns
├── experimental_run_system.md              # Run system documentation
├── multi_provider_cost_analysis.md         # Cost comparison analysis
└── design_notes/                           # Various design notes and analysis
    ├── seo-generation-design-notes.md
    └── taxonomy-seo-split-decision.md
```

### Experimental Runs (`runs/` - git ignored)

```
# Product Classification Runs
runs/assign-cat-YYYY-MM-DD-HHMMSS/
├── inputs/          # products.json, taxonomy.xml, prompt_templates.json
├── config/          # models.yaml, run_config.json, system_info.json
├── outputs/         # classifications.csv, detailed.csv, token_usage.json
│                   # timing.json, client_cost_breakdown.json, [analysis].json, classification_report.md
└── metadata/        # run_summary.json

# Health Quiz Runs
runs/health-quiz-YYYY-MM-DD-HHMMSS/
├── inputs/          # quiz_input.json, taxonomy.xml
├── config/          # models.yaml, run_config.json, system_info.json
├── outputs/         # quiz_recommendations.json, llm_response.json, product_recommendations.json
│                   # token_usage.json, timing.json, client_cost_breakdown.json
│                   # health_quiz_report.md, health_quiz_report.html (branded), errors.log
└── metadata/        # run_summary.json

# Taxonomy Generation Runs
runs/taxonomy-gen-YYYY-MM-DD-HHMMSS/
├── inputs/          # source_taxonomy.xml, prompt_template.md
├── config/          # models.yaml, run_config.json, system_info.json
├── outputs/         # generated_taxonomy.xml, diff_report.md, validation_report.json
│                   # chunk_details.json, token_usage.json, timing.json, client_cost_breakdown.json
└── metadata/        # run_summary.json

# SEO Generation Runs
runs/seo-gen-YYYY-MM-DD-HHMMSS/
├── inputs/          # source_taxonomy.xml, prompt_template.md
├── config/          # models.yaml, run_config.json, system_info.json
├── outputs/         # taxonomy_with_seo.xml, seo_generation_report.md
│                   # validation_errors.json, url_validation_results.json
│                   # token_usage.json, timing.json, client_cost_breakdown.json
└── metadata/        # run_summary.json
```

## Key Usage Patterns

### Product Classification (Production)

```bash
# Full catalog processing with cost tracking
python src/run_assign_cat.py --input data/rogue-herbalist/minimal-product-catalog.csv

# Model comparison with automatic cost attribution
python src/run_assign_cat.py --model haiku --input products.csv
python src/run_assign_cat.py --model gpt4o_mini --input products.csv

# Single product testing
python src/run_assign_cat.py --single-product "Echinacea Immune Support"
```

### Health Quiz (Production Ready)

```bash
# Test with real user personas (5 available)
python src/run_health_quiz.py --persona "Sarah Chen"        # Digestive health - TESTED
python src/run_health_quiz.py --persona "Marcus Rodriguez"  # Joint pain
python src/run_health_quiz.py --persona "Lisa Thompson"     # Stress/sleep

# Custom health scenarios
python src/run_health_quiz.py --custom-input "Frequent headaches" --primary-area "stress_relief"

# Model cost comparison
python src/run_health_quiz.py --persona "Sarah Chen" --model gpt4o_mini  # $0.0003
python src/run_health_quiz.py --persona "Sarah Chen" --model haiku
```

### Taxonomy Generation

```bash
# Generate full taxonomy with descriptions and ingredients
python src/run_taxonomy_gen.py \
  --prompt prompts/taxonomy-gen-prompt.md \
  --source data/rogue-herbalist/taxonomy_trimmed.xml \
  --model gpt4o

# Test on small taxonomy first
python src/run_taxonomy_gen.py \
  --prompt prompts/taxonomy-gen-prompt.md \
  --source data/rogue-herbalist/taxonomy_first1.xml

# Cost: ~$0.49 for 87 elements (20 primary + 67 subcategories)
# Output: runs/taxonomy-gen-YYYY-MM-DD-HHMMSS/outputs/generated_taxonomy.xml
```

### SEO Generation

```bash
# Generate SEO metadata for taxonomy (idempotent)
python src/run_seo_gen.py \
  --source data/rogue-herbalist/latest-best-taxonomy-descriptions.xml \
  --output data/rogue-herbalist/latest-best-taxonomy-with-seo.xml

# Re-run to replace existing SEO blocks
python src/run_seo_gen.py \
  --source data/rogue-herbalist/latest-best-taxonomy-with-seo.xml \
  --output data/rogue-herbalist/latest-best-taxonomy-with-seo.xml

# Process single element for testing
# (Currently processes all elements, but validates each independently)

# Output: SEO generation report with validation errors and URL validation results
```

### Cost Tracking and Billing

```python
# Get client-aware cost breakdown (automatic in all runs)
client = LLMClient("gpt4o_mini")
cost_data = client.get_cost_breakdown_for_reporting()
# Returns: client, use_case, session_cost, models_used, detailed_costs

# Check run outputs for billing data
ls runs/*/outputs/client_cost_breakdown.json
```

### Web Service Deployment (Production)

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
#    - RESEND_FROM_EMAIL=noreply@instruction.coach (production - verified domain)
# 3. Railway auto-deploys from Dockerfile

# KEY ENDPOINTS:
# POST /api/v1/webhook/formbricks - Receives Formbricks submissions
# GET /results - Email lookup page for users
# GET /results?e=email - Auto-lookup with email parameter
# POST /api/v1/results/lookup - API for fetching results by email
# GET /api/v1/results/lookup/token/{token} - API for fetching results by response token
# GET /health - Health check endpoint

# Railway CLI debugging
railway logs --follow
railway variables --set KEY=VALUE
```

## Critical Design Decisions

### 1. **Multi-Use Case Architecture**
- **Why**: Support batch classification, real-time recommendations, and document generation
- **Implementation**: Abstract framework with use case registry and standardized interfaces
- **Result**: Shared infrastructure with specialized use case implementations

### 2. **Client-Aware Cost Tracking via LiteLLM Metadata**
- **Why**: Enable multi-client billing without infrastructure overhead
- **Implementation**: Automatic tagging of all LLM requests with client, use_case, project, environment metadata
- **Result**: Billing-ready cost breakdowns with detailed model usage per client/use case

### 3. **Experimental Run System**
- **Why**: Reproducible research and systematic optimization
- **Pattern**: Lab notebook with complete artifact capture including cost data
- **Benefits**: No git bloat, full reproducibility, client-aware analytics

### 4. **Two-Pass Taxonomy/SEO Architecture**
- **Why**: LLMs have 16K output token limit; adding SEO metadata (9 fields) caused output to exceed limits
- **Decision**: Split into two separate use cases running sequentially
  1. Taxonomy generation: descriptions + ingredients
  2. SEO generation: metadata fields for each element
- **Benefits**:
  - No output limit issues (taxonomy uses chunking, SEO processes one element at a time)
  - Cleaner prompts (each focused on single task)
  - Idempotent SEO (can regenerate metadata without re-generating descriptions)
  - Reusable SEO framework (can apply to products, blog posts, etc.)

### 5. **Prompt Engineering for Character Limits**
- **Why**: LLMs not respecting character limits (e.g., keywords: 121-148 chars when limit is 120)
- **Decision**: NO code-based retries - fix the PROMPT instead
- **Implementation**:
  - Explicit 5-step process: draft, count, shorten, double-check, submit
  - "REJECTED" language emphasizing consequences
  - Field-specific examples showing exact character counts
  - Mandatory checklist before submission
- **Result**: Test showed keywords went from 131 chars → 78 chars with improved prompt

### 6. **Natural Description Writing**
- **Why**: Original prompt forced ingredient mentions in every description ("with echinacea and elderberry")
- **Decision**: Make ingredient mentions optional, focus on benefits
- **Implementation**:
  - Guidelines showing good vs. bad examples
  - Explanation that `<ingredients>` section already lists specific herbs
  - Natural descriptions focus on WHAT category helps with, not listing ingredients
- **Result**: Descriptions now benefit-focused and read naturally

### 7. **Post-Processing Validation Architecture (October 2025)**
- **Why**: LLMs output ~2.8% invalid slugs despite clear instructions
- **Decision**: Separate concerns - LLM for semantic understanding, code for validation
- **Implementation**:
  - LLM outputs single `best_slug` (simplified task)
  - Code determines if slug is primary/subcategory
  - Code auto-adds parent category when needed
  - Fuzzy matching + title-to-slug mapping corrects hallucinations
- **Result**: 100% valid slugs in final output with complete audit trail

### 8. **Email-Based Results Lookup (October 21, 2025)**
- **Why**: Formbricks doesn't support variable substitution in redirect URLs ({{responseId}} and @questionId both sent as literal strings)
- **Decision**: Use email lookup form instead of auto-loading token-based redirect
- **Implementation**:
  - Redirect to `/results` shows email input form
  - Users enter email → results display instantly (already cached)
  - Email also sent with HTML report for permanent reference
  - Optional `?e=email` parameter for potential future use
- **Benefits**:
  - Reliable user experience (no confusing "not found" errors)
  - Email provides permanent record of recommendations
  - No dependence on unimplemented Formbricks features
  - Simple, clear user flow

### 9. **Rogue Herbalist Brand Integration (October 21, 2025)**
- **Why**: Create consistent branded experience across all customer touchpoints
- **Decision**: Apply complete brand guidelines (colors, fonts, design language) to all HTML outputs
- **Implementation**:
  - Extracted brand colors from rogueherbalist.com (Primary Green: #206932, Dark Green: #2a9242)
  - Added Google Fonts (Roboto Condensed for headings, Arvo for body, Lato for buttons)
  - Updated all gradients from purple to green
  - Applied rounded button style (39px border-radius) across all CTAs
  - Consistent typography with uppercase headings
- **Result**: Professional branded experience in email templates, web results pages, CLI HTML reports, and processing pages

## Code Quality & Maintainability

### Codebase Metrics (Last Review: October 2025)
- **Total Python Files**: 15 files, 7,414 lines of code
- **Code Quality Score**: 8.5/10
- **Production Readiness**: 9/10
- **Dead Code**: <1% (cleaned up October 2025)
- **Test Coverage**: 122 passing unit tests (100% pass rate) covering core modules

### Architecture Strengths
- ✅ Clean separation of concerns (framework, use cases, runners)
- ✅ Modular design allows independent component testing
- ✅ Consistent patterns across all runners (RunManager pattern)
- ✅ Comprehensive cost tracking with client-aware metadata
- ✅ Type hints and Pydantic validation throughout

### Recent Cleanup (October 2025)
- ✅ Removed duplicate model configuration (gpt4o_mini)
- ✅ Removed unused imports (Form, asyncio)
- ✅ Removed unused method with latent bug (cleanup_expired)
- ✅ Fixed all high-confidence dead code issues

### Known Limitations
- **UseCaseManager Framework**: Incomplete dependency injection (intentional stub for future multi-client expansion)
- **Admin Authentication**: Admin endpoints need authentication enforcement before production use
- **Usage Statistics**: Endpoint returns mock data (needs database integration)

## Current System State

### Production Ready
- ✅ **Product Classification**: Cost-optimized pipeline with client-aware tracking
- ✅ **Multi-Provider Support**: 6+ models with automatic cost attribution
- ✅ **Experimental Framework**: Complete run management with billing data
- ✅ **Client Cost Tracking**: LiteLLM metadata integration for multi-client billing
- ✅ **Health Quiz**: Working end-to-end with real testing, HTML reports, working product URLs
- ✅ **Health Quiz MVP**: Fully deployed on Railway with Formbricks + Resend integration (October 2025)
- ✅ **Unit Test Suite**: 122 passing tests covering core modules (October 2025)
- ✅ **Brand Integration**: Complete Rogue Herbalist branding across all outputs (October 2025)

### Recently Implemented (October 21, 2025)

**Rogue Herbalist Brand Integration:**
- ✅ **Email Template Branding**: Updated HTML email templates with green gradient backgrounds, Google Fonts, branded buttons
  - Primary Green (#206932) and Dark Green (#2a9242) color scheme
  - Roboto Condensed headings (700 weight, uppercase)
  - Arvo body text for readability
  - Lato buttons (700 weight, uppercase, 39px rounded corners)
  - Product cards with green accents and badges
  - Revision button with green background and rounded style
- ✅ **Web Results Pages Branding**: Applied consistent branding to all web pages
  - `/results` email lookup page with green gradient background
  - `/results/{token}` auto-load page with branded loading states
  - Processing/loading pages with green spinner and typography
  - All buttons updated to rounded green style
  - All interactive elements (links, inputs) using green accent color
- ✅ **CLI HTML Reports Branding**: Updated CLI-generated reports
  - Health quiz HTML reports with green color scheme
  - Google Fonts for consistent typography across all formats
  - Product recommendation cards with green borders and badges
  - Quiz input sections with light green background (#e9f5ed)
- ✅ **Brand Guidelines Documentation**: Documented complete brand system in CLAUDE.md
  - Color palette: Primary Green (#206932), Dark Green (#2a9242), Dark Text (#1c390d)
  - Typography stack with Google Fonts integration
  - Button styling standards (rounded 39px, uppercase Lato)
  - Design principles extracted from rogueherbalist.com

**WooCommerce Product Catalog Updates:**
- ✅ **WooCommerce REST API Integration**: Fetched actual product slugs from live site (763 products via API)
- ✅ **Catalog Slug Corrections**: Updated 100+ product slugs that didn't match live WooCommerce URLs
  - Example: `digestive-bitters-formula-2-oz` → `digestive-bitters-formula-2oz-tincture` (404 → 200)
  - Example: `hemp-bitters-2oz` → `hemp-bitters-by-rogue-herbalist` (404 → 200)
- ✅ **Product URL Validation**: All 5 personas tested with working product purchase URLs
  - Sarah Chen (Digestive): 5 products, all URLs verified 200 OK
  - Marcus Rodriguez (Joint Pain): 5 products, all URLs verified
  - Lisa Thompson (Stress/Sleep): 5 products, highest relevance (0.77)
  - Robert Kim (Energy): 5 products, immune support focus
  - Jennifer Walsh (Women's Health): 5 products, immune support focus
- ✅ **Draft Product Filtering**: Skip products with empty slugs (47 draft/private products filtered)
- ✅ **API Response Caching**: Saved woocommerce-api-products.json (763 products) for debugging
- ✅ **Automated Slug Fetcher**: fetch_woocommerce_slugs.py with comprehensive documentation (FETCH_SLUGS_README.md)

**Framework Refactoring:**
- ✅ **Health Quiz Framework Integration**: Refactored all health quiz execution paths to use HealthQuizUseCase framework
- ✅ **Circular Import Resolution**: Created health_quiz_models.py for shared data structures (HealthQuizInput, ProductRecommendation, HealthQuizOutput)
- ✅ **LLM Structured Output**: Fixed JSON parsing by using response_format={"type": "json_object"} instead of text prompts
  - Before: LLM wrapped JSON in markdown fences (```json...```), parsing failed silently
  - After: Clean JSON responses with fallback markdown stripping for older models
- ✅ **Product Catalog Path Fix**: Corrected underscore/hyphen mismatch (rogue_herbalist → rogue-herbalist)
- ✅ **LLM Client Injection**: Manual set_dependencies() calls for direct framework instantiation
- ✅ **End-to-End Validation**: All 5 personas return 3 recommendations + 5 products with working URLs

**Formbricks Integration Refinements:**
- ✅ **Question ID Verification**: Extracted actual IDs via Management API, confirmed all 7 question IDs and choice IDs 100% correct (FORMBRICKS_IDS_VERIFIED.md)
- ✅ **Email Question Type Migration**: Replaced contactInfo (no prefill support) with openText + inputType=email for validation
  - Question ID: `d9klpkum9vi8x9vkunhu63fn` → `y4t3q9ctov2dn6qdon1kdbrq`
  - Simplified webhook parsing (no more array/nested object handling)
  - Email now supports URL prefilling for revision feature
- ✅ **Results Page Polling Fixes**: Fixed 5 critical bugs causing premature timeouts
  - Separate retry counters for different states (not_found: 10, processing: 40, network_error: 5)
  - Network errors now retry instead of giving up immediately
  - HTTP errors handled separately from network failures
  - "error" status now handled (was falling through to "unknown status")
  - Better console logging for debugging production issues
- ✅ **Formbricks @ Syntax Testing**: Tested recall syntax in redirect URLs
  - Tested: `/results?e=@y4t3q9ctov2dn6qdon1kdbrq`
  - Result: Literal string sent, not expanded to actual email
  - Conclusion: Formbricks doesn't support variable substitution in redirect URLs yet
- ✅ **Email Parameter Support**: Added `?e=email` parameter to `/results` endpoint
  - Auto-displays results if valid email provided
  - Shows processing page with auto-refresh if still processing
  - Falls back to email lookup form if invalid/unexpanded syntax
  - Comprehensive debug logging for troubleshooting
- ✅ **Final Solution**: Email lookup form at `/results` (reliable, simple UX)
  - User enters email → instant results display
  - Email also delivered with HTML report (permanent reference)
  - No dependence on unimplemented Formbricks features

**Documentation Updates:**
- ✅ **Formbricks API Integration Guide**: Complete documentation of Management API with extraction script
- ✅ **API Key Documentation**: Documented production and development Management API keys in parent directory
- ✅ **ID Verification Report**: FORMBRICKS_IDS_VERIFIED.md with complete verification tables

### Recently Implemented (October 2025)

**Health Quiz MVP Deployment:**
- ✅ **Railway Deployment**: Dockerfile, railway.json, automatic GitHub deployments
- ✅ **Formbricks Integration**: Webhook endpoint with exact question ID mapping for all 7 form fields
- ✅ **Formbricks Payload Parsing**: Array email handling, correct JSON paths, choice ID translation
- ✅ **Resend Email Service**: HTML email delivery using noreply@instruction.coach (production - verified domain)
- ✅ **Token-Based Results Lookup**: Dual access via email hash and response ID token
- ✅ **Error Handling**: Proper JSONResponse returns for 404/500 errors
- ✅ **Model Configuration**: Using aliases (gpt4o_mini) instead of full names for consistency
- ✅ **Railway CLI Integration**: Real-time log monitoring and debugging capabilities
- ✅ **End-to-End Verification**: Full flow working from form submission → LLM → email → results page
- ✅ **MVP Documentation**: Complete deployment guide and quick-start guide

**Code Quality Review:**
- ✅ **Dead Code Cleanup**: Removed unused imports, duplicate configs, buggy methods
- ✅ **Code Review**: Assessed 15 files, 7,414 lines (8.5/10 quality, 9/10 production readiness)
- ✅ **Documentation**: Identified and documented known limitations and intentional stubs
- ✅ **Unit Test Suite**: 122 passing tests covering core modules (100% pass rate)

### Recently Implemented (September 2025)
- ✅ **Document Generation Framework**: Abstract base classes for XML document generation
- ✅ **Taxonomy Generation**: Automated descriptions with natural writing, character limits, chunk processing
- ✅ **SEO Generation Framework**: Separate use case with validation, URL checking, idempotent operations
- ✅ **Improved Prompts**: Character limit enforcement and natural description guidelines

### Known Issues

**Product Classification:**
- ⚠️ **Multi-Assignment**: 1.2% of products (9/761) get duplicate category assignments - mostly bugs (exact duplicates, same category ±subcategory), refactoring plan in TODO.md

**SEO Generation:**
- ⚠️ **Character Limit Compliance**: 40/87 elements failed validation (keywords 121-148 chars); improved prompt tested successfully on single element, full regeneration pending user approval
- ⚠️ **Cost Tracking Bug**: SEO generation showing $0.00 in client_cost_breakdown.json
- ⚠️ **Missing SEO Blocks**: Elements that fail validation left without ANY SEO block (not partial)

### Implementation Pending
- 📋 **Full Taxonomy Regeneration**: Regenerate with improved natural description prompt
- 📋 **Full SEO Regeneration**: Regenerate with improved character limit enforcement prompt
- 📋 **Advanced Personalization**: Follow-up recommendations and user profiles

## Technical Dependencies

### Core Libraries
- **litellm**: Multi-provider LLM interface with built-in cost tracking and metadata support
- **fastapi**: Web framework for API endpoints (Production)
- **uvicorn**: ASGI server for FastAPI deployment
- **pydantic**: Data validation and serialization (including EmailStr for email validation)
- **python-dotenv**: Environment configuration
- **PyYAML**: Configuration file parsing
- **markdown**: HTML report generation with extensions (extra, codehilite, toc, nl2br)
- **httpx**: Async HTTP client for Resend email API
- **pandas**: Data processing for product catalogs
- **pytest**: Unit testing framework (122 passing tests)

### Multi-Client Requirements
- **Client-specific API Keys**: Separate OpenAI/Anthropic keys per client
- **Cost Attribution**: Automatic tagging via LiteLLM metadata
- **Configuration Management**: Per-client settings and use case permissions

### Deployment Infrastructure (October 2025)
- **Railway**: Containerized deployment with automatic GitHub integration
- **Formbricks**: Form builder with webhook integration
- **Resend**: Email delivery service (3000 emails/month free tier)
- **Docker**: Containerization for consistent deployment
- **ngrok**: Local webhook testing during development

## Quality Metrics & Performance

### Cost Analysis (LiteLLM Live Pricing)
- **Product Classification**: $0.0015 per product (GPT-4o-Mini)
- **Health Quiz**: $0.0003 per interaction (GPT-4o-Mini) - 5x cheaper than classification
- **Taxonomy Generation**: ~$0.49 for 87 elements (GPT-4o)
- **SEO Generation**: TBD - cost tracking bug showing $0.00
- **Claude Haiku**: $0.0024 per product with high classification quality
- **Client Attribution**: Automatic cost breakdown by client/use case/model

### Classification Quality (Product Classification)
- **Assignment Consistency**: 98.5% single assignments, 1.5% multiple assignments
- **Taxonomy Coverage**: 20 main categories, 84+ subcategories
- **Processing Speed**: ~1.2 seconds per product with batch optimization
- **Slug Validation**: 100% valid slugs post-validation (was 2.8% error rate)

### Health Quiz Quality (Real User Testing - October 2025)
- **Response Quality**: 100% confidence scores with 3 detailed evidence-based recommendations per persona
- **Product Relevance**: 5 products per persona with 0.30-0.77 relevance scores (Lisa Thompson stress/sleep highest at 0.77)
- **Processing Speed**: 5.6-9.3 seconds per complete health assessment
- **Safety Features**: Automatic consultation recommendations for severity ≥7 or concerning keywords
- **User Personas**: All 5 personas tested successfully with unique product recommendations
  - Sarah Chen (Digestive Health): Hemp Bitters, Ginger, Digestive Bitters (0.47-0.58)
  - Marcus Rodriguez (Joint Pain): InflaCalm, Ginger, Teasel Tincture (0.30-0.40)
  - Lisa Thompson (Stress/Sleep): Passionflower, Valerian, Hemp Adapt (0.54-0.77)
  - Robert Kim (Energy/Vitality): Garlic, Elderberry, Immuno Well (0.55-0.60)
  - Jennifer Walsh (Women's Health): Immuno Well, Elderberry, Garlic (0.54-0.57)
- **URL Validation**: 100% working product URLs verified via WooCommerce REST API slugs
- **Report Formats**: Both markdown (.md) and styled HTML (.html) reports with clickable purchase links
- **Cost Consistency**: $0.0003 per interaction across all personas (GPT-4o-Mini)

### Taxonomy/SEO Generation Quality
- **Taxonomy Elements Processed**: 87 (20 primary categories + 67 subcategories)
- **Taxonomy Success Rate**: 100% (all elements generated valid descriptions)
- **SEO Success Rate**: 54% (47/87 succeeded, 40 failed validation)
- **Main SEO Issue**: Keywords field exceeding 120 char limit (121-148 chars)
- **Prompt Improvement Test**: Single element went from 131 chars → 78 chars
- **Description Quality**: Improved from forced ingredient mentions to natural benefit-focused writing
- **URL Validation**: All canonical URLs tested (104 URLs, all returned HTTP 404 - categories don't exist yet)

### Client-Aware Cost Tracking
- **Automatic Attribution**: Every request tagged with client, use_case, project, environment
- **Cost Breakdown**: Session costs by model, per-call averages, total attribution
- **Reporting Format**: `client_cost_breakdown.json` with billing-ready data structure
- **Zero Infrastructure**: Uses LiteLLM's built-in metadata and cost calculation features

## Development Workflow

### Recent Work: Rogue Herbalist Brand Integration (October 21, 2025)
1. ✅ **Extracted Brand Guidelines** - Analyzed rogueherbalist.com to identify colors, fonts, and design patterns
2. ✅ **Updated Email Templates** - Applied green gradient, Google Fonts, branded buttons and product cards
3. ✅ **Updated Web Results Pages** - Consistent branding across email lookup, token-based, and processing pages
4. ✅ **Updated CLI HTML Reports** - Green color scheme in health quiz HTML reports with Google Fonts
5. ✅ **Documented Brand System** - Complete guidelines in CLAUDE.md for future reference
6. ✅ **Committed Changes** - Git commit with comprehensive branding update documentation

**Brand Elements Applied:**
- Primary Green: #206932, Dark Green: #2a9242, Dark Text: #1c390d
- Google Fonts: Roboto Condensed (headings), Arvo (body), Lato (buttons)
- Button style: 39px rounded corners, uppercase text, green background with hover state
- Typography: Uppercase headings with Roboto Condensed, clean Arvo body text
- Consistent design language across email, web, and CLI outputs

**Files Modified:**
- src/web_service.py: Email templates, web results pages, processing pages (130 lines changed)
- src/run_health_quiz.py: CLI HTML report generation (90 lines changed)

### Recent Work: Product Catalog & Framework Refactoring (October 21, 2025)
1. ✅ **Researched SKU vs Slug in WooCommerce** - Confirmed SKUs are numeric barcodes, slugs are URL strings
2. ✅ **Created WooCommerce API Fetcher** - fetch_woocommerce_slugs.py with comprehensive documentation
3. ✅ **Fetched Live Product Slugs** - 763 products via REST API with pagination (8 pages × 100 products)
4. ✅ **Updated Product Catalog** - Corrected 100+ slugs, backed up original, replaced catalog
5. ✅ **Fixed Framework Integration** - Resolved circular imports, added LLM structured output, injected dependencies
6. ✅ **Fixed Product Engine** - Added draft product filtering, corrected catalog path (underscore → hyphen)
7. ✅ **Validated All 5 Personas** - Sarah Chen, Marcus Rodriguez, Lisa Thompson, Robert Kim, Jennifer Walsh
8. ✅ **Verified Product URLs** - All recommendations return working purchase links (HTTP 200)

**Key Achievements:**
- Product URL success rate: 100% (was 0% with 404 errors)
- All 5 personas return 5 working product recommendations
- LLM recommendations improved from 1 generic → 3 detailed personalized tips
- Cost per interaction: $0.0003 (5-9 seconds processing time)

**Technical Fixes:**
- LLM JSON parsing: Added `response_format={"type": "json_object"}` with markdown fence fallback
- Circular imports: Created health_quiz_models.py for shared data structures
- Catalog loading: Fixed directory name translation (rogue_herbalist → rogue-herbalist)
- Draft filtering: Skip 47 products with empty slugs (draft/private status)

**Files Created:**
- fetch_woocommerce_slugs.py: WooCommerce REST API integration script
- FETCH_SLUGS_README.md: Complete usage documentation
- health_quiz_models.py: Shared data models (HealthQuizInput, ProductRecommendation, HealthQuizOutput)
- data/rogue-herbalist/woocommerce-api-products.json: Raw API response (763 products)

### Recent Work: Formbricks Integration Refinements (October 21, 2025)
1. ✅ **Verified Formbricks Question IDs** - Extracted actual IDs via Management API, confirmed 100% match
2. ✅ **Created ID Extraction Script** - Automated tool for pulling question/choice IDs from Formbricks API
3. ✅ **Documented API Keys** - Saved production and development Management API keys in parent directory
4. ✅ **Migrated Email Question Type** - Replaced contactInfo with openText + email validation for prefill support
5. ✅ **Fixed Results Page Polling** - Separate retry counters for different states, network error handling
6. ✅ **Tested Formbricks @ Syntax** - Confirmed recall syntax doesn't work in redirect URLs (sent as literal string)
7. ✅ **Added Email Parameter Support** - `/results?e=email` for auto-lookup with comprehensive debug logging
8. ✅ **Finalized Email Lookup Solution** - Simple, reliable UX with email input form and instant results
9. ✅ **Updated Documentation** - FORMBRICKS_IDS_VERIFIED.md, formbricks_api_integration.md, API_KEYS.md

**Key Findings:**
- All Formbricks question IDs and choice IDs were already correct in code (not the source of bugs)
- Formbricks doesn't support variable substitution in redirect URLs ({{responseId}} and @ syntax both literal)
- Email lookup form provides reliable UX without dependence on unimplemented Formbricks features
- ContactInfo question type doesn't support prefilling; openText with inputType=email does

**Debugging Tools Used:**
- Railway CLI for log streaming: `railway logs --follow`
- Formbricks Management API: `GET /api/v1/management/surveys/{surveyId}`
- Python extraction script: `extract_formbricks_ids.py`

### Recent Work: Code Quality Review (October 2025)
1. ✅ **Comprehensive Code Review**: Assessed 15 Python files, 7,414 lines of code
2. ✅ **Quality Metrics**: Scored 8.5/10 for code quality, 9/10 for production readiness
3. ✅ **Dead Code Cleanup**: Removed duplicate configs, unused imports, buggy methods
4. ✅ **Documentation**: Identified and documented known limitations and intentional stubs
5. ✅ **Architecture Analysis**: Confirmed clean separation of concerns and modular design
6. ✅ **Unit Test Suite**: 122 passing tests covering core modules (100% pass rate)

**Key Findings:**
- Codebase is production-ready with <1% dead code
- Strong architectural patterns (framework, use cases, runners)
- Areas for improvement: admin auth, usage stats database

### Recent Work: Health Quiz MVP Debugging (October 2025)
1. ✅ **Fixed Formbricks webhook payload parsing** - Corrected JSON path from `data["response"]["id"]` to `data["id"]`
2. ✅ **Added array email handling** - Extract email from Formbricks array format `["", "", "email", "", ""]`
3. ✅ **Fixed error handlers** - Changed 404/500 handlers to return `JSONResponse` instead of dict (was causing 500 errors)
4. ✅ **Fixed model configuration** - Changed model names from full names (`openai/gpt-4o-mini`) to aliases (`gpt4o_mini`)
5. ✅ **Mapped all 7 Formbricks question IDs** - Email, health issue, primary area, severity, tried already, age range, lifestyle
6. ✅ **Added choice ID mappings** - Translated Formbricks internal IDs to readable names for dropdowns
7. ✅ **Set up Railway CLI monitoring** - Linked project and service for real-time log streaming
8. ✅ **Fixed Resend email sender** - Changed from unverified testing email to production `noreply@instruction.coach`
9. ✅ **Verified end-to-end flow** - Webhook → LLM processing → Email sending → Results lookup all working
10. ✅ **Domain verification completed** - `instruction.coach` verified with Resend DNS records
11. ✅ **Token-based redirect implemented** - Eliminated email double-entry with auto-refresh results page

**Debugging Tools Used:**
- Railway CLI for log streaming: `railway logs --follow`
- Resend API for email status: `curl https://api.resend.com/emails`
- Railway variables management: `railway variables --set`

### Recent Work: Taxonomy & SEO Generation (September 2025)
1. ✅ **Identified 16K output token limit issue** when adding SEO to taxonomy generation
2. ✅ **Designed two-pass architecture** splitting taxonomy content from SEO metadata
3. ✅ **Implemented document generation framework** as abstract base for both use cases
4. ✅ **Built taxonomy generation** with chunk processing and character limit enforcement
5. ✅ **Built SEO generation** with field validation, URL checking, idempotent operations
6. ✅ **Tested on small taxonomy** (6 elements) - hit character limit issues
7. ✅ **Improved SEO prompt** with explicit character counting instructions
8. ✅ **Improved taxonomy prompt** to remove forced ingredient mentions
9. 🔄 **Pending**: Full regeneration with improved prompts (awaiting user approval due to cost)

### Next Phase: Production Optimization
1. **Advanced Personalization**: User profiles and follow-up recommendations
2. **E-commerce Integration**: Direct product purchase workflows
3. **Complete Taxonomy/SEO Generation**: Regenerate with improved prompts, fix cost tracking bug

### Multi-Client Expansion
1. **Add new clients** via configuration files
2. **Implement use case variations** using abstract framework
3. **Monitor cost attribution** through automatic LiteLLM metadata
4. **Scale billing systems** using standardized cost breakdown format

## Rebuilding SYNOPSIS.md (this file)

This project can occasionally be on hold for a brief while and we want to be ready to pick it back up and quickly reload the context of all the code and documentation for new software changes. Build an idealized SYNOPSIS.md that is right-sized for this project. It should summarize the goals and the code, but also describe the organization of the code, for further reading and analysis (avoiding scanning all code).

**Key Information to Include:**

1. **Recent Code Review Findings (October 2025):**
   - Codebase metrics: 15 Python files, 7,414 lines of code
   - Code quality: 8.5/10, Production readiness: 9/10
   - Dead code: <1% (cleaned up)
   - Recent cleanup: Removed duplicate model config, unused imports, unused method with bug
   - Known limitations: UseCaseManager stubs, admin auth needed, mock usage stats

2. **Architecture Overview:**
   - Core Infrastructure: llm_client.py, model_config.py, product_processor.py
   - Frameworks: use_case_framework.py, document_generation_framework.py, seo_generation_framework.py
   - Use Cases: health_quiz_use_case.py, product_recommendation_engine.py, analysis_engine.py
   - Runners: run_assign_cat.py, run_health_quiz.py, run_seo_gen.py, run_taxonomy_gen.py
   - Web Service: web_service.py (FastAPI with 15+ endpoints)

3. **Read Current Documentation:**
   - CLAUDE.md for command reference and working features
   - TODO.md for pending tasks
   - Current SYNOPSIS.md for structure

4. **Integration Requirements:**
   - Maintain the existing structure and organization
   - Add "Code Quality & Maintainability" section with metrics
   - Update "Known Issues" with code review findings
   - Update "Recent Work" with October 2025 code review and cleanup
   - Keep the "Rebuilding SYNOPSIS.md" section at the end
   - Ensure all sections are comprehensive but concise

**When prompted with "rebuild synopsis", use the above instructions to regenerate this file with updated information.**
