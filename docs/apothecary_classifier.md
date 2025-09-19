# Apothecary Product Classifier

## Overview
A machine learning system for classifying herbal products according to a health-focused taxonomy. Uses LLMs to analyze product descriptions and match them to appropriate health categories.

## Technical Stack
- Python 3.9+
- liteLLM for LLM API abstraction
- Anthropic Claude 3 Opus (anthropic/claude-3-opus-20240229)

## Core Components

### 1. Product Data Processing
- CSV catalog reader with streaming support
- Product data model: ID, title, description, ingredients
- Handles both short and full descriptions
- UTF-8 with BOM handling for reliable text processing

### 2. Taxonomy Management
- XML-based taxonomy definition
- Hierarchical category structure
- Rich metadata including:
  - CHEBI roles
  - NPClassifier categories
  - FDA claims
  - Ingredient associations

### 3. LLM Integration
- Provider: Anthropic Claude
- Model: claude-3-opus-20240229 (see MODEL_NOTE.md)
- Token handling: Max 1000 output tokens
- Context structure:
  ```python
  messages = [
      {"role": "system", "content": "Expert classifier prompt"},
      {"role": "user", "content": "Taxonomy context"},
      {"role": "user", "content": "Product for classification"}
  ]
  ```

## Rate Limiting Considerations

### Observed Limits
- Token acceleration limits in place
- Must gradually scale up token usage
- Initial requests often succeed, subsequent ones hit limits

### Current Mitigation Strategy
1. Exponential backoff between retries:
   - Initial delay: 30 seconds
   - Doubles on each retry (30s → 60s → 120s)
2. Inter-product delays:
   - 60 second pause between products
   - Helps avoid acceleration limit issues

### Planned Improvements
1. Progressive token scaling:
   - Start with title-only classification
   - Gradually add short description
   - Finally incorporate full description
2. Batch size management:
   - Initial testing with 3 products
   - Scale up based on success rate
   - Monitor token acceleration

## Token Usage Analysis

### Per-Product Averages
- System prompt: ~100 tokens
- Taxonomy context: ~2000-3000 tokens
- Product data:
  - Title: ~10-20 tokens
  - Short description: ~100-200 tokens
  - Full description: ~500-1000 tokens
- Response: ~100-200 tokens

### Cost Considerations
- Total tokens per product: ~3000-4000
- Success rate impacts:
  - Retries increase token usage
  - Rate limits force slower processing

## Testing Approaches

### Initial Testing
1. Single product validation
   - Minimal context testing
   - Token usage baseline
   - Response format verification

### Batch Testing
1. Small batch (3 products)
   - Rate limit investigation
   - Retry logic validation
   - Token usage patterns

### Data Collection
1. Run logging:
   - Token usage metrics
   - Success/failure rates
   - Processing times
   - API response details

2. Error tracking:
   - Rate limit patterns
   - Retry effectiveness
   - Token usage thresholds

## Run Directory Structure
```
runs/
  └── YYYYMMDD_HHMMSS/
      ├── inputs/
      │   ├── product_catalog.csv
      │   └── taxonomy.xml
      ├── config/
      │   ├── config.json     # Run parameters
      │   └── prompt.txt      # Classification prompt
      ├── outputs/
      │   ├── category_assignments.csv
      │   └── stats.json      # Run statistics
      └── logs/
          ├── run.log         # Process log
          ├── api_calls.jsonl # API interactions
          └── token_usage.json
```

## Current Status
- Basic infrastructure complete
- Rate limiting challenges identified
- Testing in progress with small batches
- Token usage monitoring in place
- Next steps focused on scaling strategy