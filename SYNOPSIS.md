# IC-ML Project Synopsis

## Project Overview

**Goal**: Multi-use case LLM-powered platform supporting herbal product classification, customer health quiz recommendations, and taxonomy/SEO content generation with client-aware cost tracking.

**Business Context**: Originally built for "Get Better Care" client processing ~800 herbal products for classification at $2.43 per 1000 products. Now expanded to support:
- Customer-facing Health Quiz feature for Rogue Herbalist with personalized product recommendations
- Taxonomy generation for e-commerce category structure and descriptions
- SEO metadata generation for categories and products

**Current Status**: Production-ready classification system, **deployed Health Quiz MVP** on Railway with Formbricks integration and Resend email delivery, and taxonomy/SEO generation framework with experimental runners.

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
- **Post-Processing Validation (NEW - October 2025)**: 100% valid slugs (from 2.8% error rate) with automatic hierarchy resolution
  - Simplified LLM task: single `best_slug` output instead of category/subcategory pairs
  - Automatic parent category detection and insertion for subcategories
  - Fuzzy matching and title-to-slug mapping for LLM hallucination correction
- **Modular Analysis Engine**: Human-readable markdown reports with cost breakdowns

**Health Quiz (Production Ready):**
- **Real-time Recommendations**: LLM-powered health guidance with product matching ($0.0003 per interaction)
- **Working Product URLs**: 100% tested success rate with WordPress/WooCommerce slug generation
- **HTML Report Generation**: Professional styled reports with clickable product links
- **End-to-End Testing**: Successfully tested with 5 realistic user personas

**Health Quiz MVP Deployment (NEW - October 2025):**
- **Railway Deployment**: Containerized FastAPI service with automatic GitHub deployments
- **Formbricks Integration**: Webhook-based form submission handling with email-based results lookup
- **Resend Email Service**: HTML email delivery using `onboarding@resend.dev` (testing) or `no-reply@instruction.coach` (production)
- **Email-Based Results**: SHA-256 hashed email storage with 24-hour expiration for privacy
- **Auto-Retry Polling**: Results page automatically retries every 3 seconds during LLM processing
- **In-Memory Storage**: MVP uses in-memory dict, upgrade path to PostgreSQL documented
- **Cost-Effective**: $0/month on free tiers (Railway $5 credit, Resend 3000 emails/month, Formbricks unlimited)

**Taxonomy & SEO Generation (New - September 2025):**
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
   - HTML and markdown report generation

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

11. **Web Service API** (`src/web_service.py`) - *Production MVP*
    - FastAPI-based REST endpoints for Health Quiz (Formbricks webhook, results lookup)
    - In-memory storage with email hashing for privacy
    - Resend email integration for HTML report delivery
    - Background task processing for non-blocking webhook responses
    - Deployed on Railway with automatic GitHub integration

## Code Organization

### Source Code (`src/`)

```
src/
├── use_case_framework.py                # Abstract use case framework and registry
├── document_generation_framework.py     # Abstract framework for XML document generation (NEW)
├── health_quiz_use_case.py              # Health quiz implementation with LLM integration
├── run_health_quiz.py                   # Health quiz experimental runner (PRODUCTION READY)
├── run_taxonomy_gen.py                  # Taxonomy generation runner (NEW)
├── seo_generation_framework.py          # SEO generation framework (NEW)
├── run_seo_gen.py                       # SEO generation runner (NEW)
├── product_recommendation_engine.py     # Intelligent product matching system
├── web_service.py                       # FastAPI web service (PRODUCTION MVP - Railway deployed)
├── run_assign_cat.py                    # Product classification runner with experiments
├── llm_client.py                        # LLM interface with client-aware cost tracking
├── model_config.py                      # Configuration management with client metadata
├── analysis_engine.py                   # Modular analysis with markdown reporting
├── reanalyze_assign_cat.py              # Post-classification analysis tool
└── product_processor.py                 # Product data structures and batch processing
```

### Prompts (`prompts/`)

```
prompts/
├── README.md                    # Prompts directory documentation
├── taxonomy-gen-prompt.md       # Taxonomy generation prompt with natural description guidelines (NEW)
└── seo-gen-prompt.md            # SEO generation prompt with strict character limit enforcement (NEW)
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
    │   ├── taxonomy_generation: chunk_size=3, max_tokens=4000 (NEW)
    │   └── seo_generation: field specs, url_templates, validate_urls (NEW)
    ├── client_tracking: automatic metadata for cost attribution
    └── api: retry and rate limiting settings
```

### Deployment Files (NEW - October 2025)

```
.
├── Dockerfile                       # Railway deployment container configuration
├── railway.json                     # Railway service configuration with health checks
├── requirements.txt                 # Python dependencies (FastAPI, Resend, httpx, etc.)
├── .env.example                     # Environment variables template with Resend config
├── MVP_QUICKSTART.md                # Quick deployment guide (5 steps, 2 hours)
└── docs/
    └── railway_formbricks_deployment_guide.md  # Complete deployment guide (Railway + Formbricks + Resend)
```

### Data (`data/`)

```
data/rogue-herbalist/
├── taxonomy_trimmed.xml                  # Optimized taxonomy structure (60% smaller, 36KB)
├── taxonomy_first1.xml                   # Small test taxonomy (6 elements)
├── taxonomy_first2.xml                   # Larger test taxonomy
├── latest-best-taxonomy-descriptions.xml # Generated taxonomy with natural descriptions (NEW)
├── latest-best-taxonomy-with-seo.xml     # Taxonomy with SEO metadata (partial - 47/87 succeeded) (NEW)
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
├── railway_formbricks_deployment_guide.md  # Complete MVP deployment guide (Railway + Formbricks + Resend) (NEW)
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
│                   # health_quiz_report.md, health_quiz_report.html, errors.log
└── metadata/        # run_summary.json

# Taxonomy Generation Runs (NEW)
runs/taxonomy-gen-YYYY-MM-DD-HHMMSS/
├── inputs/          # source_taxonomy.xml, prompt_template.md
├── config/          # models.yaml, run_config.json, system_info.json
├── outputs/         # generated_taxonomy.xml, diff_report.md, validation_report.json
│                   # chunk_details.json, token_usage.json, timing.json, client_cost_breakdown.json
└── metadata/        # run_summary.json

# SEO Generation Runs (NEW)
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

### Taxonomy Generation (NEW)

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

### SEO Generation (NEW)

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

### 4. **Two-Pass Taxonomy/SEO Architecture** (NEW)
- **Why**: LLMs have 16K output token limit; adding SEO metadata (9 fields) caused output to exceed limits
- **Decision**: Split into two separate use cases running sequentially
  1. Taxonomy generation: descriptions + ingredients
  2. SEO generation: metadata fields for each element
- **Benefits**:
  - No output limit issues (taxonomy uses chunking, SEO processes one element at a time)
  - Cleaner prompts (each focused on single task)
  - Idempotent SEO (can regenerate metadata without re-generating descriptions)
  - Reusable SEO framework (can apply to products, blog posts, etc.)

### 5. **Prompt Engineering for Character Limits** (NEW)
- **Why**: LLMs not respecting character limits (e.g., keywords: 121-148 chars when limit is 120)
- **Decision**: NO code-based retries - fix the PROMPT instead
- **Implementation**:
  - Explicit 5-step process: draft, count, shorten, double-check, submit
  - "REJECTED" language emphasizing consequences
  - Field-specific examples showing exact character counts
  - Mandatory checklist before submission
- **Result**: Test showed keywords went from 131 chars → 78 chars with improved prompt

### 6. **Natural Description Writing** (NEW)
- **Why**: Original prompt forced ingredient mentions in every description ("with echinacea and elderberry")
- **Decision**: Make ingredient mentions optional, focus on benefits
- **Implementation**:
  - Guidelines showing good vs. bad examples
  - Explanation that `<ingredients>` section already lists specific herbs
  - Natural descriptions focus on WHAT category helps with, not listing ingredients
- **Result**: Descriptions now benefit-focused and read naturally

## Current System State

### Production Ready
- ✅ **Product Classification**: Cost-optimized pipeline with client-aware tracking
- ✅ **Multi-Provider Support**: 6+ models with automatic cost attribution
- ✅ **Experimental Framework**: Complete run management with billing data
- ✅ **Client Cost Tracking**: LiteLLM metadata integration for multi-client billing
- ✅ **Health Quiz**: Working end-to-end with real testing, HTML reports, working product URLs
- ✅ **Health Quiz MVP**: Deployed on Railway with Formbricks + Resend integration (October 2025)

### Recently Implemented (October 2025)
- ✅ **Railway Deployment**: Dockerfile, railway.json, automatic GitHub deployments
- ✅ **Formbricks Integration**: Webhook endpoint for form submissions
- ✅ **Resend Email Service**: HTML email delivery (onboarding@resend.dev for testing, no-reply@instruction.coach for production)
- ✅ **Email-Based Results Lookup**: SHA-256 hashing, 24hr expiration, auto-retry polling
- ✅ **MVP Documentation**: Complete deployment guide and quick-start guide

### Recently Implemented (September 2025)
- ✅ **Document Generation Framework**: Abstract base classes for XML document generation
- ✅ **Taxonomy Generation**: Automated descriptions with natural writing, character limits, chunk processing
- ✅ **SEO Generation Framework**: Separate use case with validation, URL checking, idempotent operations
- ✅ **Improved Prompts**: Character limit enforcement and natural description guidelines

### Known Issues
- ⚠️ **Product Classification Multi-Assignment**: 1.2% of products (9/761) get duplicate category assignments - mostly bugs (exact duplicates, same category ±subcategory), refactoring plan in TODO.md
- ⚠️ **SEO Character Limit Compliance**: 40/87 elements failed validation (keywords 121-148 chars); improved prompt tested successfully on single element, full regeneration pending user approval
- ⚠️ **Cost Tracking Bug**: SEO generation showing $0.00 in client_cost_breakdown.json
- ⚠️ **Missing SEO Blocks**: Elements that fail validation left without ANY SEO block (not partial)

### Implementation Pending
- 📋 **Full Taxonomy Regeneration**: Regenerate with improved natural description prompt
- 📋 **Full SEO Regeneration**: Regenerate with improved character limit enforcement prompt
- 📋 **Web Service Redesign**: Unified deployment architecture with domain strategy
- 📋 **Production Integration**: E-commerce platform integration and customer journey
- 📋 **Advanced Personalization**: Follow-up recommendations and user profiles

## Technical Dependencies

### Core Libraries
- **litellm**: Multi-provider LLM interface with built-in cost tracking and metadata support
- **fastapi**: Web framework for API endpoints (Production MVP)
- **uvicorn**: ASGI server for FastAPI deployment
- **pydantic**: Data validation and serialization (including EmailStr for email validation)
- **python-dotenv**: Environment configuration
- **PyYAML**: Configuration file parsing
- **markdown**: HTML report generation with extensions (extra, codehilite, toc, nl2br)
- **httpx**: Async HTTP client for Resend email API (NEW)
- **pandas**: Data processing for product catalogs

### Multi-Client Requirements
- **Client-specific API Keys**: Separate OpenAI/Anthropic keys per client
- **Cost Attribution**: Automatic tagging via LiteLLM metadata
- **Configuration Management**: Per-client settings and use case permissions

### Deployment Infrastructure (NEW - October 2025)
- **Railway**: Containerized deployment with automatic GitHub integration
- **Formbricks**: Form builder with webhook integration
- **Resend**: Email delivery service (3000 emails/month free tier)
- **Docker**: Containerization for consistent deployment
- **ngrok**: Local webhook testing during development

## Quality Metrics & Performance

### Cost Analysis (LiteLLM Live Pricing)
- **Product Classification**: $0.0015 per product (GPT-4o-Mini)
- **Health Quiz**: $0.0003 per interaction (GPT-4o-Mini) - 5x cheaper than classification
- **Taxonomy Generation**: ~$0.49 for 87 elements (GPT-4o) (NEW)
- **SEO Generation**: TBD - cost tracking bug showing $0.00 (NEW)
- **Claude Haiku**: $0.0024 per product with high classification quality
- **Client Attribution**: Automatic cost breakdown by client/use case/model

### Classification Quality (Product Classification)
- **Assignment Consistency**: 98.5% single assignments, 1.5% multiple assignments
- **Taxonomy Coverage**: 20 main categories, 84+ subcategories
- **Processing Speed**: ~1.2 seconds per product with batch optimization

### Health Quiz Quality (Real User Testing)
- **Response Quality**: 80% confidence scores with evidence-based recommendations
- **Product Relevance**: 5 products recommended with 0.47-0.58 relevance scores
- **Processing Speed**: 6-8 seconds per complete health assessment
- **Safety Features**: Automatic consultation recommendations for severity ≥7
- **User Personas**: Successfully tested with 5 realistic health scenarios
- **URL Generation**: 100% success rate on tested product URLs with algorithmic slug generation
- **Report Formats**: Both markdown (.md) and styled HTML (.html) reports with clickable links

### Taxonomy/SEO Generation Quality (NEW)
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

### Next Phase: Production Deployment
1. **Complete Taxonomy/SEO Generation**: Regenerate with improved prompts, fix cost tracking bug
2. **Web Service Integration**: Deploy Health Quiz as customer-facing service
3. **Advanced Personalization**: User profiles and follow-up recommendations
4. **E-commerce Integration**: Direct product purchase workflows

### Multi-Client Expansion
1. **Add new clients** via configuration files
2. **Implement use case variations** using abstract framework
3. **Monitor cost attribution** through automatic LiteLLM metadata
4. **Scale billing systems** using standardized cost breakdown format

## Rebuilding SYNOPSIS.md (this file)

This project can occasionally be on hold for a brief while and we want to be ready to pick it back up and quickly reload the context of all the code and documentation for new software changes, provided by you, Claude, in response to my prompting. Such a context can be degraded during compacting or must be restarted due to software crashes or inability to return the previous coding environment. Please explore what would be the ideal memory to save for this project so you don't need to completely re-read all documentation. Build an idealized SYNOPSIS.md that is right-sized for this project. It should summarize the goals and the code, but also describe the organization of the code, for further reading and analysis (avoiding scanning all code). And for future rebuilding save this prompt under the section "Rebuilding SYNOPSIS.md (this file)". The next time I say "rebuild synopsis", you shall use this prompt.
