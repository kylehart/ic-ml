# IC-ML Project Synopsis

## Project Overview

**Goal**: Multi-use case LLM-powered platform supporting both herbal product classification and customer health quiz recommendations with client-aware cost tracking and experimental framework.

**Business Context**: Originally built for "Get Better Care" client processing ~800 herbal products for classification at $2.43 per 1000 products. Now expanded to support customer-facing Health Quiz feature for Rogue Herbalist with personalized product recommendations.

**Current Status**: Production-ready product classification system with experimental Health Quiz architecture and comprehensive multi-client cost tracking via LiteLLM metadata integration.

## Key Achievements

**Core Infrastructure:**
- **Multi-Use Case Architecture**: Abstract framework supporting both batch classification and real-time health recommendations
- **Client-Aware Cost Tracking**: Automatic attribution of all LLM costs by client, use case, project, and environment using LiteLLM metadata
- **Experimental Framework**: Complete run management with artifact capture and reproducibility
- **Multi-Provider Integration**: 6+ models across OpenAI/Anthropic with seamless switching and cost optimization

**Product Classification (Production):**
- **Batch Processing Optimization**: 20x speed improvement (3.2s vs 84s for 10 products)
- **Cost-Effective Classification**: $0.0015 per product using GPT-4o-Mini with full taxonomy
- **Full Taxonomy Integration**: 20-category herbal taxonomy (optimized from 88KB to 36KB)
- **Modular Analysis Engine**: Human-readable markdown reports with cost breakdowns

**Health Quiz (Architectural Design):**
- **Real-time Recommendations**: LLM-powered health guidance with product matching
- **Product Recommendation Engine**: Intelligent scoring based on health categories, ingredients, and text similarity
- **Web Service API**: FastAPI-based endpoints with authentication and usage tracking
- **Multi-Client Support**: Isolated billing and configuration per client

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

### Use Case Implementations

4. **Product Classification** (`src/run_assign_cat.py`)
   - Production-ready batch processing with experimental run management
   - Complete artifact capture (inputs, config, outputs, metadata)
   - Integration with modular analysis engine and cost tracking

5. **Health Quiz** (`src/health_quiz_use_case.py`)
   - Real-time health recommendation processing
   - Structured input/output with safety features (consultation detection)
   - Integration with product recommendation engine

6. **Product Recommendation Engine** (`src/product_recommendation_engine.py`)
   - Multi-factor scoring: health categories, ingredients, text similarity
   - Category mapping system connecting health concerns to products
   - Configurable recommendation thresholds and ranking

### Supporting Infrastructure

7. **Analysis Engine** (`src/analysis_engine.py`)
   - Modular analysis components with markdown reporting
   - LiteLLM-based cost calculation using live pricing data
   - Model comparison analysis with savings calculations

8. **Web Service API** (`src/web_service.py`) - *Speculative Prototype*
   - FastAPI-based REST endpoints for both use cases
   - Client authentication and multi-tenant usage tracking
   - Background cost attribution and analytics

## Code Organization

### Source Code (`src/`)

```
src/
├── use_case_framework.py              # Abstract use case framework and registry
├── health_quiz_use_case.py            # Health quiz implementation with LLM integration
├── run_health_quiz.py                 # Health quiz experimental runner (PRODUCTION READY)
├── product_recommendation_engine.py   # Intelligent product matching system
├── web_service.py                     # FastAPI web service (speculative prototype)
├── run_assign_cat.py                  # Product classification runner with experiments
├── llm_client.py                      # LLM interface with client-aware cost tracking
├── model_config.py                    # Configuration management with client metadata
├── analysis_engine.py                 # Modular analysis with markdown reporting
├── reanalyze_assign_cat.py            # Post-classification analysis tool
└── product_processor.py              # Product data structures and batch processing
```

### Configuration (`config/`)

```
config/
└── models.yaml              # Central model configuration
    ├── default: gpt-4o-mini (cost-optimized)
    ├── models: 6+ models across 2 providers
    ├── experiments: custom configurations
    ├── use_cases: health_quiz and product_classification settings
    ├── client_tracking: automatic metadata for cost attribution
    └── api: retry and rate limiting settings
```

### Data (`data/`)

```
data/rogue-herbalist/
├── taxonomy_trimmed.xml          # Optimized taxonomy (60% smaller, 36KB)
├── taxonomy.xml.txt              # Original full taxonomy
├── minimal-product-catalog.csv   # Enhanced 787-product catalog with generated URL slugs
├── minimal-product-catalog-backup.csv  # Original catalog backup
└── [various CSV examples]        # Sample data formats

data/health-quiz-samples/
└── user_personas.json            # 5 realistic user personas for Health Quiz testing
                                  # (Sarah Chen, Marcus Rodriguez, Lisa Thompson, Robert Kim, Jennifer Walsh)
```

### Documentation (`docs/`)

```
docs/
├── multi_client_architecture_design.md    # Multi-client platform design
├── health_quiz_user_stories.md           # Health quiz business requirements
├── implementation_guide.md               # Deployment and setup guide
├── wordpress_woocommerce_url_research.md # WordPress/WooCommerce URL patterns
├── experimental_run_system.md            # Run system documentation
├── multi_provider_cost_analysis.md       # Cost comparison analysis
└── [existing design docs]                # Various technical specifications
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
python src/run_health_quiz.py --persona "Sarah Chen"     # Digestive health
python src/run_health_quiz.py --persona "Marcus Rodriguez"  # Joint pain
python src/run_health_quiz.py --persona "Lisa Thompson"     # Stress/sleep

# Custom health scenarios
python src/run_health_quiz.py --custom-input "Frequent headaches and fatigue" --primary-area "stress_relief"

# Model cost comparison
python src/run_health_quiz.py --persona "Sarah Chen" --model gpt4o_mini  # $0.0003
python src/run_health_quiz.py --persona "Sarah Chen" --model haiku       # More expensive
```

### Programmatic Health Quiz Usage

```python
# Create health quiz instance
from health_quiz_use_case import HealthQuizInput
from run_health_quiz import process_health_quiz

quiz_input = HealthQuizInput(
    health_issue_description="Digestive issues after meals",
    primary_health_area="digestive_health",
    severity_level=6
)

# Process with cost tracking
quiz_output, llm_response, product_recs, token_usage, timing_info, client_cost_data, errors = \
    process_health_quiz(quiz_input, "gpt4o_mini")

# Results include:
# - General health recommendations (3-5 points)
# - Product recommendations (up to 5 with relevance scores)
# - Educational content and lifestyle suggestions
# - Safety assessment and consultation recommendations
```

### Cost Tracking and Billing

```python
# Get client-aware cost breakdown (automatic in all runs)
client = LLMClient("gpt4o_mini")
cost_data = client.get_cost_breakdown_for_reporting()
# Returns: client, use_case, session_cost, models_used, detailed_costs

# Check run outputs for billing data
ls runs/assign-cat-*/outputs/client_cost_breakdown.json
```

## Critical Design Decisions

### 1. **Multi-Use Case Architecture**
- **Why**: Support both batch product classification and real-time health recommendations
- **Implementation**: Abstract framework with use case registry and standardized interfaces
- **Result**: Shared infrastructure with specialized use case implementations

### 2. **Client-Aware Cost Tracking via LiteLLM Metadata**
- **Why**: Enable multi-client billing without infrastructure overhead
- **Implementation**: Automatic tagging of all LLM requests with client, use_case, project, environment metadata
- **Client Tracking**: Zero-infrastructure cost attribution using LiteLLM's built-in features
- **Result**: Billing-ready cost breakdowns with detailed model usage per client/use case

### 3. **Experimental Run System**
- **Why**: Reproducible research and systematic optimization
- **Pattern**: Lab notebook with complete artifact capture including cost data
- **Benefits**: No git bloat, full reproducibility, client-aware analytics

### 4. **Health Quiz Product Recommendations**
- **Why**: Transform product classification expertise into customer-facing value
- **Implementation**: Multi-factor scoring engine with health category mapping
- **Business Model**: Direct customer health inquiry to product purchase pathway

## Current System State

### Production Ready
- ✅ **Product Classification**: Cost-optimized pipeline with client-aware tracking
- ✅ **Multi-Provider Support**: 6+ models with automatic cost attribution
- ✅ **Experimental Framework**: Complete run management with billing data
- ✅ **Client Cost Tracking**: LiteLLM metadata integration for multi-client billing

### Architectural Design Complete
- ✅ **Health Quiz Framework**: Complete use case architecture and data models
- ✅ **Product Recommendation Engine**: Intelligent matching with configurable scoring
- ✅ **Multi-Client Architecture**: Scalable framework for multiple clients and use cases
- ✅ **Web Service Design**: API specifications for real-time health quiz processing

### Implemented and Tested
- ✅ **Health Quiz Development**: Complete experimental framework with working LLM integration
- ✅ **Product Recommendation Engine**: Multi-factor scoring with 787-product catalog integration
- ✅ **WordPress/WooCommerce URL Integration**: Algorithmic slug generation with 100% success rate on tested URLs
- ✅ **Product Catalog Enhancement**: Added slug field to all 787 products with generated URLs
- ✅ **HTML Report Generation**: Professional styled reports with clickable product links
- ✅ **End-to-End Testing**: Successfully tested with real user personas generating working purchase URLs

### Implementation Pending
- 📋 **Web Service Redesign**: Unified deployment architecture with domain strategy
- 📋 **Production Integration**: E-commerce platform integration and customer journey
- 📋 **Advanced Personalization**: Follow-up recommendations and user profiles

## Technical Dependencies

### Core Libraries
- **litellm**: Multi-provider LLM interface with built-in cost tracking and metadata support
- **fastapi**: Web framework for API endpoints (speculative prototype)
- **pydantic**: Data validation and serialization
- **python-dotenv**: Environment configuration
- **PyYAML**: Configuration file parsing
- **markdown**: HTML report generation with extensions (extra, codehilite, toc, nl2br)

### Multi-Client Requirements
- **Client-specific API Keys**: Separate OpenAI/Anthropic keys per client
- **Cost Attribution**: Automatic tagging via LiteLLM metadata
- **Configuration Management**: Per-client settings and use case permissions

## Quality Metrics & Performance

### Cost Analysis (LiteLLM Live Pricing)
- **Product Classification**: $0.0015 per product (GPT-4o-Mini)
- **Health Quiz**: $0.0003 per interaction (GPT-4o-Mini) - 5x cheaper than classification
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

### Client-Aware Cost Tracking
- **Automatic Attribution**: Every request tagged with client, use_case, project, environment
- **Cost Breakdown**: Session costs by model, per-call averages, total attribution
- **Reporting Format**: `client_cost_breakdown.json` with billing-ready data structure
- **Zero Infrastructure**: Uses LiteLLM's built-in metadata and cost calculation features

## Development Workflow

### Health Quiz Development (Completed)
1. ✅ **Experimental Framework**: Complete Health Quiz runner with artifact capture
2. ✅ **Prompt Engineering**: Working LLM integration with JSON response parsing
3. ✅ **Product Recommendation Testing**: 787-product catalog with multi-factor scoring
4. ✅ **Performance Optimization**: Cost-effective at $0.0003 per interaction
5. ✅ **User Persona Testing**: 5 realistic health scenarios with end-to-end validation
6. ✅ **WordPress/WooCommerce Integration**: Proper URL generation patterns

### Next Phase: Production Deployment
1. **Web Service Integration**: Deploy Health Quiz as customer-facing service
2. **Advanced Personalization**: User profiles and follow-up recommendations
3. **E-commerce Integration**: Direct product purchase workflows

### Multi-Client Expansion
1. **Add new clients** via configuration files
2. **Implement use case variations** using abstract framework
3. **Monitor cost attribution** through automatic LiteLLM metadata
4. **Scale billing systems** using standardized cost breakdown format

## Rebuilding SYNOPSIS.md (this file)

This project can occasionally be on hold for a brief while and we want to be ready to pick it back up and quickly reload the context of all the code and documentation for new software changes, provided by you, Claude, in response to my prompting. Such a context can be degraded during compacting or must be restarted due to software crashes or inability to return the previous coding environment. Please explore what would be the ideal memory to save for this project so you don't need to completely re-read all documentation. Build an idealized SYNOPSIS.md that is right-sized for this project. It should summarize the goals and the code, but also describe the organization of the code, for further reading and analysis (avoiding scanning all code). And for future rebuilding save this prompt under the section "Rebuilding SYNOPSIS.md (this file)". The next time I say "rebuild synopsis", you shall use this prompt.