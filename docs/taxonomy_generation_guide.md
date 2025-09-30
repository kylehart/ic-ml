# Taxonomy Generation Use Case

## Overview

The taxonomy generation use case enables LLM-powered refinement and expansion of XML taxonomies. This is part of the broader **Document Generation Framework** that supports taxonomies, quizzes, protocols, and enrollment forms.

## Architecture

### Core Components

1. **use_case_framework.py** - Added `DocumentGenerationUseCase` base class
2. **document_generation_framework.py** - Shared infrastructure:
   - `DocumentValidator` - XML/JSON validation with taxonomy-specific checks
   - `DocumentDiffer` - Structural diff generation and reporting
   - `DocumentGenerationRunner` - Base experimental runner
3. **run_taxonomy_gen.py** - Taxonomy-specific implementation with retry logic

### Processing Pattern

```
Source Document + Instructions → LLM → Generated Document
                                  ↓
                            Validation Loop
                                  ↓
                         Diff + Cost Tracking
```

## Usage

### Basic Command

```bash
python src/run_taxonomy_gen.py \
  --source data/rogue-herbalist/taxonomy_trimmed.xml \
  --instructions "Add a new category for Sleep Support with subcategories" \
  --model gpt4o
```

### Using Custom Prompt Template

You can provide a custom prompt template that will be prepended to the taxonomy. This is useful for specialized generation strategies:

```bash
python src/run_taxonomy_gen.py \
  --source data/rogue-herbalist/taxonomy_trimmed.xml \
  --instructions "Expand immune support with detailed subcategories" \
  --prompt prompts/taxonomy-gen-prompt.md \
  --model gpt4o
```

The prompt template file (like `prompts/taxonomy-gen-prompt.md`) should contain your specialized instructions for how the LLM should approach taxonomy generation. The source taxonomy will be appended after your prompt template.

### Using Instructions File

```bash
# Create instructions file
cat > instructions.txt <<EOF
Add a new primary category for "Women's Health" with:
- Appropriate sub-title and description
- Meta information with relevant chebi-roles
- At least 3 subcategories covering hormonal balance, pregnancy support, and menopause
EOF

# Run generation
python src/run_taxonomy_gen.py \
  --source data/rogue-herbalist/taxonomy_trimmed.xml \
  --instructions @instructions.txt \
  --model gpt4o
```

### With Context Data

```bash
# Provide context about product catalog
python src/run_taxonomy_gen.py \
  --source taxonomy.xml \
  --instructions @instructions.txt \
  --context-file catalog_stats.json
```

## Output Structure

Each run creates a timestamped directory: `runs/taxonomy-gen-YYYY-MM-DD-HHMMSS/`

```
taxonomy-gen-2025-09-30-123950/
├── inputs/
│   ├── source_taxonomy.xml           # Original taxonomy
│   ├── instructions.txt              # Generation instructions
│   ├── prompt_template.md            # Optional: Custom prompt template
│   └── context_data.json             # Optional context
├── config/
│   ├── models.yaml                   # Model configuration snapshot
│   └── run_config.json               # Run parameters
├── outputs/
│   ├── generated_taxonomy.xml        # ⭐ Generated taxonomy
│   ├── diff.json                     # Structured diff data
│   ├── diff_report.md                # Human-readable diff
│   ├── validation_report.md          # Validation results
│   ├── taxonomy_generation_report.md # Combined report
│   ├── token_usage.json              # LLM usage stats
│   └── client_cost_breakdown.json    # Cost attribution
└── metadata/
    └── run_summary.json              # Run metadata
```

## Features

### Automatic Validation with Retry

The system validates generated taxonomies and retries up to 3 times if validation fails:

1. **XML Well-Formedness** - Syntax validation
2. **Taxonomy Structure** - Required elements (slugs, titles, descriptions)
3. **Entity Encoding** - Automatic fixing of ampersands and special characters

### Comprehensive Diff Tracking

```markdown
## Summary
- Total Changes: 13
- Additions: 12
- Deletions: 0
- Modifications: 1

## Added Nodes
- /taxon[@slug='stress-mood-support']
- /taxon[@slug='stress-mood-support']/title
- /taxon[@slug='stress-mood-support']/meta/chebi-roles
...
```

### Cost Tracking

All LLM calls are tracked with client-aware cost attribution:

```json
{
  "client": "get-better-care",
  "use_case": "herbal-classification",
  "session_cost": 0.000371,
  "models_used": ["gpt-4o-mini-2024-07-18"]
}
```

## Configuration

In `config/models.yaml`:

```yaml
use_cases:
  taxonomy_generation:
    default_model: "openai/gpt-4o"     # More capable model for complex generation
    max_tokens: 4000                    # Larger context for documents
    temperature: 0.1                    # Slight creativity while maintaining consistency
    validation_retries: 3               # Retry attempts on validation failure
    include_diff_report: true
    document_format: "xml"
```

### Cost Notes

- **GPT-4o Mini**: ~$0.0004 per generation (simple taxonomies)
- **GPT-4o**: ~$0.02-0.05 per generation (complex taxonomies, better quality)

## Testing

### Smoke Tests

Run validation and diffing tests without LLM calls:

```bash
python3 tests/test_document_generation.py
```

Output:
```
============================================================
Running Document Generation Framework Smoke Tests
============================================================

Testing XML validator...
  ✅ Valid XML passed
  ✅ Invalid XML correctly rejected
✅ XML validator tests passed

Testing taxonomy structure validator...
  ✅ Valid taxonomy structure passed
...
✅ ALL TESTS PASSED
```

### End-to-End Test

Test with simple taxonomy:

```bash
python3 src/run_taxonomy_gen.py \
  --source data/test-taxonomy-simple.xml \
  --instructions @data/test-instructions.txt \
  --model gpt4o_mini
```

## Example: Real Taxonomy Refinement

```bash
# Refine the Rogue Herbalist taxonomy
python src/run_taxonomy_gen.py \
  --source data/rogue-herbalist/taxonomy_trimmed.xml \
  --instructions "Expand the Immune Support category with more detailed subcategories for seasonal support, antiviral herbs, and mushroom complexes. Add detailed descriptions for each subcategory." \
  --model gpt4o

# Results in runs/taxonomy-gen-YYYY-MM-DD-HHMMSS/
# - Review: outputs/taxonomy_generation_report.md
# - Compare: outputs/diff_report.md
# - Deploy: outputs/generated_taxonomy.xml
```

## Future Extensions

The document generation framework supports:

### Quiz Generation (`run_quiz_gen.py`)
```bash
python src/run_quiz_gen.py \
  --health-area digestive_health \
  --target-audience adults \
  --question-count 10
```

### Protocol Generation (`run_protocol_gen.py`)
```bash
python src/run_protocol_gen.py \
  --condition seasonal_allergies \
  --source-protocol protocols/allergy_base.md
```

### Form Generation (`run_form_gen.py`)
```bash
python src/run_form_gen.py \
  --form-type enrollment \
  --fields fields_spec.json
```

## Integration with Existing Use Cases

The taxonomy generation follows the same patterns as:

- **Product Classification** - Batch processing with experimental runs
- **Health Quiz** - Real-time recommendations with cost tracking

All use the same:
- Experimental run framework
- Client-aware cost tracking (via LiteLLM metadata)
- Artifact capture and reproducibility
- Analysis and reporting tools

## Best Practices

1. **Start with Simple Instructions** - Test with small changes first
2. **Review Diffs Carefully** - Check `diff_report.md` before deploying
3. **Validate Structure** - Ensure taxonomy follows required schema
4. **Use Context Data** - Provide product catalog stats for better generation
5. **Track Costs** - Monitor `client_cost_breakdown.json` for billing
6. **Version Control** - Keep run directories for reproducibility

## Troubleshooting

### Validation Failures

If generation fails validation after 3 attempts:

1. Check `outputs/generation_errors.log` for specific errors
2. Simplify instructions - break into smaller steps
3. Try a more capable model (gpt4o instead of gpt4o_mini)
4. Manually fix source taxonomy issues

### Common Issues

- **Unescaped Ampersands** - Automatically fixed by cleaner
- **Missing Required Elements** - Add explicit requirements to instructions
- **Structural Changes** - Emphasize "maintain structure" in prompt

## Files Reference

### Source Code
- `src/use_case_framework.py:167-258` - DocumentGenerationUseCase base class
- `src/document_generation_framework.py` - Validators, differs, runners
- `src/run_taxonomy_gen.py` - Taxonomy-specific runner

### Tests
- `tests/test_document_generation.py` - Smoke tests

### Configuration
- `config/models.yaml:108-117` - Taxonomy generation settings

### Example Data
- `data/test-taxonomy-simple.xml` - Simple test taxonomy
- `data/test-instructions.txt` - Example instructions
