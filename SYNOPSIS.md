# IC-ML Project Synopsis

## Project Overview

**Goal**: Cost-optimized LLM-based classification system for herbal products into health categories using multi-provider AI models with experimental run management.

**Business Context**: Processing ~800 herbal products for "Get Better Care" client, achieving 99% cost reduction (from $128 to $0.03 per catalog) through model optimization and systematic experimentation.

**Current Status**: Production-ready system with experimental run management, multi-provider support (OpenAI + Anthropic), and comprehensive cost analysis.

## Key Achievements

- **Cost Optimization**: GPT-4o-Mini ($0.03 per 800 products) vs original Opus ($128) = 99% savings
- **Multi-Provider Integration**: 6 models across OpenAI and Anthropic with seamless switching
- **Experimental Framework**: Complete run management with artifact capture and reproducibility
- **Quality Validation**: Framework for EMA regulatory data validation (planned)
- **Taxonomy Optimization**: 60% size reduction (88KB → 36KB) to eliminate rate limiting

## Architecture Overview

### Core Components

1. **LLM Client** (`src/llm_client.py`)
   - Unified interface for OpenAI and Anthropic models via litellm
   - Centralized configuration management
   - Support for both async and sync operations

2. **Product Processing** (`src/product_processor.py`)
   - Product data structures and CSV loading
   - Batch processing framework with retry logic
   - Designed for catalog-scale operations

3. **Configuration System** (`config/models.yaml` + `src/model_config.py`)
   - Centralized model definitions (6 models across 2 providers)
   - Runtime override support for experiments
   - Cost-tier organization (ultra-fast, balanced, premium)

4. **Experimental Run System** (`src/run_assign_cat.py`)
   - Complete artifact capture (inputs, config, outputs, metadata)
   - Lab notebook pattern with timestamped runs
   - Reproducible experimental framework

### Model Tiers & Costs (800 products)

| Tier | OpenAI | Anthropic | Cost |
|------|--------|-----------|------|
| **Ultra-Fast** | GPT-4o-Mini | Haiku | $0.03 / $0.05 |
| **Balanced** | GPT-4-Turbo | Sonnet | $1.80 / $0.61 |
| **Premium** | GPT-4o | Opus | $0.90 / $3.06 |

**Default**: GPT-4o-Mini (cheapest, excellent quality)

## Code Organization

### Source Code (`src/`)

```
src/
├── run_assign_cat.py          # Main executable - experimental run manager
├── llm_client.py             # LLM interface with multi-provider support
├── model_config.py           # Configuration management system
├── product_processor.py      # Product data structures and batch processing
├── classify_products.py      # Legacy classification pipeline (partial)
├── context_builder.py        # Message building for LLM API calls
└── llm_logger.py             # API logging and token usage tracking
```

### Configuration (`config/`)

```
config/
└── models.yaml              # Central model configuration
    ├── default: gpt-4o-mini (cost-optimized)
    ├── models: 6 models across 2 providers
    ├── experiments: custom configurations
    └── api: retry and rate limiting settings
```

### Data (`data/`)

```
data/rogue-herbalist/
├── taxonomy_trimmed.xml     # Optimized taxonomy (60% smaller)
└── taxonomy.xml            # Original full taxonomy
```

### Documentation (`docs/`)

```
docs/
├── experimental_run_system.md       # Run system documentation
├── multi_provider_cost_analysis.md  # Cost comparison analysis
├── cost_analysis_update.md         # Historical cost optimization
├── code_review_report.md           # Code consistency analysis
├── llm_classification_plan.md      # Original system design
├── specificity_scale_design.md     # Precision control framework
└── gold_standard_validation_framework.md  # EMA validation design
```

### Experimental Runs (`runs/` - git ignored)

```
runs/assign-cat-YYYY-MM-DD-HHMMSS/
├── inputs/          # products.json, taxonomy.xml, prompt_templates.json
├── config/          # models.yaml, run_config.json, system_info.json
├── outputs/         # classifications.csv, token_usage.json, timing.json
└── metadata/        # run_summary.json
```

## Key Usage Patterns

### Running Experiments

```bash
# Default model (GPT-4o-Mini)
python src/run_assign_cat.py --single-product "Echinacea Tincture"

# Model comparison
python src/run_assign_cat.py --model haiku --single-product "Turmeric Capsules"
python src/run_assign_cat.py --model gpt4o --input products.csv

# Batch processing
python src/run_assign_cat.py --input catalog.csv --batch-size 10
```

### Model Switching

```python
# In code
client = LLMClient("gpt4o_mini")  # Cheapest
client = LLMClient("sonnet")      # Balanced
client = LLMClient("opus")        # Premium quality
```

### Configuration Override

```bash
# Environment override
MODEL_CONFIG_OVERRIDE=experiment:temperature_test python src/run_assign_cat.py
```

## Critical Design Decisions

### 1. **Multi-Provider Strategy**
- **Why**: Cost optimization and API reliability
- **Implementation**: Unified interface via litellm
- **Result**: 106x cost range ($0.03 to $3.06)

### 2. **Experimental Run System**
- **Why**: Reproducible research and systematic optimization
- **Pattern**: Lab notebook with complete artifact capture
- **Benefits**: No git bloat, full reproducibility, analysis-ready outputs

### 3. **Taxonomy Optimization**
- **Problem**: Rate limiting on 88KB taxonomy
- **Solution**: Removed ingredients, kept subcategories (36KB)
- **Result**: Eliminated rate limiting, maintained classification quality

### 4. **Centralized Configuration**
- **Problem**: Model inconsistencies across codebase
- **Solution**: Single YAML file with override support
- **Benefits**: Easy model switching, experiment reproducibility

## Current System State

### Production Ready Features
- ✅ **Cost-optimized pipeline**: $0.03 per 800 products
- ✅ **Multi-provider support**: 6 models across OpenAI/Anthropic
- ✅ **Experimental framework**: Complete run management
- ✅ **Configuration system**: Centralized with override support
- ✅ **Quality testing**: Individual model validation

### Planned Enhancements
- 🔄 **Batch processing**: Additional 70%+ cost savings
- 🔄 **EMA validation**: Gold standard quality measurement using regulatory data (documented but not implemented)
- 🔄 **Specificity scale**: 1-10 precision control for classification (documented but not implemented)
- 🔄 **Full catalog processing**: 800-product production run

## Technical Dependencies

### Core Libraries
- **litellm**: Multi-provider LLM interface
- **python-dotenv**: Environment configuration
- **PyYAML**: Configuration file parsing

### API Requirements
- **OpenAI API**: GPT models (default provider)
- **Anthropic API**: Claude models (backup/quality)

### File Dependencies
- `config/models.yaml`: Model definitions
- `data/rogue-herbalist/taxonomy_trimmed.xml`: Classification taxonomy
- `.env`: API keys (git ignored)

## Quality Metrics

### Cost Comparison (Per Request)
- **GPT-4o-Mini**: $0.000036 (cheapest)
- **Claude Haiku**: $0.000064
- **Claude Sonnet**: $0.000765
- **Claude Opus**: $0.003825 (most expensive)

### Classification Accuracy Example
**Test Product**: Turmeric Curcumin Anti-Inflammatory
- **OpenAI Models**: Correctly classified as `pain-inflammation`
- **Claude Haiku**: Incorrectly classified as `stress-mood-anxiety`
- **Finding**: OpenAI models showed better accuracy for tested cases

## Troubleshooting Guide

### Common Issues
1. **Rate Limiting**: Use trimmed taxonomy, reduce batch size
2. **API Quota**: Check API key billing status
3. **Model Errors**: Verify model names in `config/models.yaml`
4. **Configuration**: Check `.env` file for API keys

### Debug Commands
```bash
# Test model switching
python src/run_assign_cat.py --model gpt4o_mini --single-product "Test Product"

# Verify configuration
python -c "from model_config import get_model_config; print(get_model_config().model)"

# Check run outputs
ls -la runs/assign-cat-*/outputs/
```

## Development Workflow

### Making Changes
1. **Update configuration**: Modify `config/models.yaml`
2. **Test changes**: Use single-product tests first
3. **Run experiments**: Generate timestamped runs for comparison
4. **Document results**: Update cost analysis or add findings to docs

### Adding Models
1. Add to `config/models.yaml` under `models:` section
2. Test with `python src/run_assign_cat.py --model new_model --single-product "Test Product"`
3. Update cost analysis documentation

### Extending Use Cases
1. Create new main script (e.g., `src/run_sentiment.py`)
2. Follow experimental run pattern with same directory structure
3. Update this synopsis with new use case

## Rebuilding SYNOPSIS.md (this file)

This project can occasionally be on hold for a brief while and we want to be ready to pick it back up and quickly reload the context of all the code and documentation for new software changes, provided by you, Claude, in response to my prompting. such a context can be degraded during compacting or must be restarted due to software crashed or inability to return the previous coding environment. Please explore what would be the ideal memory to save for this project so you don't need to completely re-read all documentation. build an idealized SYNOPSIS.md that is right-sized for this project. it should summarize the goals and the code, but also describe the organization of the code, for further reading and analysis (avoiding scanning all code). And for future rebuilding save this prompt under the section "Rebuilding SYNOPSIS.md (this file)". The next time I say "rebuild synopsis, you shall use this prompt".