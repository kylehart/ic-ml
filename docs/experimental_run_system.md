# Experimental Run System Documentation

## Overview

The experimental run system provides a comprehensive framework for conducting reproducible machine learning experiments with complete artifact capture. Designed from the perspective of an experimental data scientist, it implements a "lab notebook" pattern that captures all inputs, configurations, and outputs for each experimental run.

## Design Philosophy

### Core Principles

1. **Complete Reproducibility**: Every run captures all necessary artifacts to reproduce the exact same results
2. **Artifact Isolation**: Each run is completely self-contained with its own directory
3. **Standardized Structure**: Consistent directory layout and file formats across all runs
4. **Lab Notebook Pattern**: Organized like a physical lab notebook with timestamped entries
5. **Analysis-Ready**: Output formats designed for easy post-run analysis and comparison

### Use Case Focus

The system is built around **use cases** - distinct experimental scenarios with consistent methodology. Currently supports:

- **assign-cat**: Product category assignment using LLM classification

Future use cases can be added with the same framework (e.g., `sentiment-analysis`, `text-generation`, etc.).

## System Architecture

### Run Identification

Each experimental run receives a unique identifier following the pattern:
```
<use-case>-<date>-<time>
```

Examples:
- `assign-cat-2025-09-19-165514`
- `assign-cat-2025-09-19-170203`

### Directory Structure

Every run creates a standardized directory structure in `runs/`:

```
runs/assign-cat-2025-09-19-165514/
├── inputs/
│   ├── products.json           # Input products data
│   ├── taxonomy.xml           # Taxonomy snapshot
│   └── prompt_templates.json  # All prompts used
├── config/
│   ├── models.yaml           # Full model configuration snapshot
│   ├── run_config.json       # Runtime parameters
│   └── system_info.json      # Environment information
├── outputs/
│   ├── classifications.csv   # Main results (analysis-ready)
│   ├── token_usage.json     # API usage statistics
│   ├── timing.json          # Performance metrics
│   └── errors.log           # Error logs (if any)
└── metadata/
    └── run_summary.json      # Run metadata and status
```

### Data Capture Strategy

#### Inputs Snapshot
- **Complete Capture**: All input data is snapshotted, not referenced
- **Taxonomy Files**: Full taxonomy XML copied for exact reproducibility
- **Product Data**: All input products serialized to JSON
- **Prompt Templates**: Exact prompts used, enabling prompt engineering analysis

#### Configuration Snapshot
- **Model Configuration**: Complete `models.yaml` file copied
- **Runtime Parameters**: Model overrides, batch sizes, CLI arguments
- **System Environment**: Python version, package versions, platform info
- **No Secrets**: Environment variables and API keys are NOT captured

#### Output Capture
- **CSV Format**: Main results in CSV for easy analysis and loading
- **Token Metrics**: Complete API usage tracking for cost analysis
- **Performance Data**: Timing information for optimization
- **Error Tracking**: Failed operations logged for debugging

## CLI Interface

### Main Command

```bash
python src/run_assign_cat.py [options]
```

### Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `--model` | Override model configuration | `--model gpt4o_mini` |
| `--single-product` | Test with single product | `--single-product "Turmeric Capsules"` |
| `--input` | Input CSV file with products | `--input products.csv` |
| `--batch-size` | Processing batch size | `--batch-size 10` |

### Usage Examples

```bash
# Quick single product test with default model
python src/run_assign_cat.py --single-product "Echinacea Immune Support"

# Test with specific model
python src/run_assign_cat.py --model haiku --single-product "Ashwagandha Capsules"

# Process CSV file with Anthropic model
python src/run_assign_cat.py --model sonnet --input catalog.csv

# Batch processing with OpenAI
python src/run_assign_cat.py --model gpt4o --input products.csv --batch-size 5
```

## Model Configuration

### Default Model
The system defaults to **GPT-4o-Mini** for maximum cost optimization:
- **Cost**: $0.03 per 800-product catalog
- **Quality**: Excellent for classification tasks
- **Speed**: Fast response times

### Model Switching
Easy switching between providers and tiers:

```bash
# Ultra-fast/cheap options
--model gpt4o_mini     # OpenAI cheapest
--model haiku          # Anthropic cheapest

# Balanced options
--model gpt4_turbo     # OpenAI balanced
--model sonnet         # Anthropic balanced

# Premium options
--model gpt4o          # OpenAI premium
--model opus           # Anthropic premium
```

### Configuration Management
- **Centralized**: All models defined in `config/models.yaml`
- **Snapshotted**: Full config copied to each run
- **Override Support**: Runtime model switching via CLI
- **Multi-Provider**: Supports OpenAI and Anthropic seamlessly

## Output Formats

### Primary Results (classifications.csv)
CSV format designed for easy analysis:

```csv
product_id,title,category,subcategory,raw_response,model_used
test_001,Echinacea Tincture,immune-support,daily-immune,immune-support,daily-immune,test_001,openai/gpt-4o-mini
```

### Token Usage (token_usage.json)
API usage tracking for cost analysis:

```json
{
  "total_prompt_tokens": 1250,
  "total_completion_tokens": 45,
  "calls_made": 3,
  "model_used": "openai/gpt-4o-mini"
}
```

### Performance Metrics (timing.json)
Timing data for optimization:

```json
{
  "total_duration_seconds": 2.3,
  "products_processed": 3,
  "errors_count": 0,
  "average_time_per_product": 0.77
}
```

## Integration Points

### Existing Codebase Integration
- **LLMClient**: Seamless integration with existing model client
- **ProductProcessor**: Uses existing product data structures
- **Configuration System**: Leverages centralized model configuration
- **Taxonomy System**: Automatically includes taxonomy in runs

### Analysis Workflows
- **CSV Loading**: Results easily loaded into pandas/R for analysis
- **Cross-Run Comparison**: Standardized format enables run comparisons
- **Cost Analysis**: Token usage data supports cost optimization
- **Quality Metrics**: Classification results enable accuracy measurement

## Git Integration

### Repository Exclusion
Run directories are excluded from git via `.gitignore`:
```
runs/
```

### Benefits
- **No Repository Bloat**: Large result files don't inflate repo size
- **Local Experiments**: Researchers can experiment without affecting others
- **Artifact Safety**: No risk of accidentally committing sensitive results

### Sharing Strategy
- **Selective Sharing**: Share specific runs via tar/zip if needed
- **Results Documentation**: Key findings documented in committed markdown files
- **Configuration Sharing**: Model configurations committed for team coordination

## Reproducibility Features

### Complete Input Capture
Every run contains everything needed to reproduce results:
- Exact products used
- Exact taxonomy version
- Exact prompts and templates
- Model configuration snapshot
- System environment details

### Version Independence
- **No Git Dependencies**: Runs don't require specific git commits
- **Taxonomy Snapshots**: No dependency on current taxonomy file state
- **Configuration Snapshots**: Independent of current config file changes

### Analysis Reproducibility
- **Timestamped Data**: Clear temporal ordering of experiments
- **Standardized Formats**: Consistent output structure across runs
- **Complete Metadata**: Full context for result interpretation

## Cost Optimization Features

### Model Cost Tracking
- **Token Usage**: Precise API usage capture per run
- **Cost Projection**: Easy cost analysis and budgeting
- **Model Comparison**: Compare costs across different model choices

### Default Optimization
- **GPT-4o-Mini Default**: Most cost-effective model as default
- **Easy Upgrading**: Simple model override for quality needs
- **Batch Processing**: Framework ready for batch cost optimizations

## Error Handling and Reliability

### Graceful Degradation
- **Partial Failures**: Individual product failures don't stop entire run
- **Error Logging**: Complete error capture for debugging
- **Progress Tracking**: Clear indication of run progress and completion

### Run Validation
- **Directory Creation**: Automatic run directory setup
- **File Validation**: Input file existence checking
- **Configuration Validation**: Model configuration verification

## Future Extensions

### Additional Use Cases
The framework easily extends to new experimental scenarios:
- Sentiment analysis: `sentiment-2025-09-19-140000/`
- Text generation: `generation-2025-09-19-140000/`
- Document classification: `doc-class-2025-09-19-140000/`

### Analysis Tools
Potential additions:
- **Run Comparison Tools**: Automated cross-run analysis
- **Visualization**: Automated chart generation from run results
- **Report Generation**: Automated experimental reports
- **Quality Metrics**: Automated accuracy and quality assessment

### Scaling Features
Framework ready for:
- **Parallel Processing**: Multiple concurrent runs
- **Distributed Execution**: Cloud-based run execution
- **Pipeline Integration**: CI/CD integration for automated experiments

## Best Practices

### Experimental Workflow
1. **Plan Experiments**: Define hypothesis and success criteria
2. **Start Small**: Use single products or small batches for initial testing
3. **Document Goals**: Use descriptive product names or input files
4. **Iterate Models**: Test different models systematically
5. **Analyze Results**: Use CSV outputs for statistical analysis

### Directory Management
- **Regular Cleanup**: Archive old runs periodically
- **Meaningful Names**: Use descriptive input sources when possible
- **Organized Storage**: Consider organizing runs by experiment phases

### Documentation
- **Key Findings**: Document important results in committed markdown
- **Configuration Changes**: Document model configuration evolution
- **Analysis Scripts**: Commit analysis scripts that operate on run results

## Conclusion

The experimental run system provides a robust foundation for reproducible machine learning experimentation. By capturing complete experimental context and providing standardized output formats, it enables rigorous analysis workflows while maintaining the flexibility needed for rapid experimentation and model comparison.

The system's design prioritizes both experimental rigor and practical usability, making it suitable for both exploratory research and production validation workflows.