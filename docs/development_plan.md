# Herbal Product Classification System - Development Plan

## Project Overview

Development of an automated herbal product classification system that assigns health area categories to ~800 products using LLM-based classification with regulatory validation and configurable specificity controls.

## Core Features

### 1. LLM-Based Classification Engine
- **Product-by-product classification** using structured prompts
- **Configurable specificity scale (1-10)** for precision/recall control
- **Multi-label output** supporting multiple health areas per product
- **CSV format output** matching existing category_assignment structure

### 2. Regulatory Validation Framework
- **EMA monograph integration** for EU regulatory-approved herb uses
- **Gold-standard validation** using WHO, USP, ESCOP, Commission E data
- **Tiered confidence scoring** (Tier 1: Regulatory, Tier 2: Expert, Tier 3: Clinical)
- **Automated quality assurance** reducing manual review burden

### 3. Configurable Specificity System
- **1-10 scale implementation** with business-friendly controls
- **Dynamic prompt engineering** based on specificity level
- **Client-tunable parameters** for precision/recall optimization
- **A/B testing framework** for specificity level optimization

## Development Phases

### Phase 1: Foundation Infrastructure (Weeks 1-2)

#### 1.1 Core LLM Classification Engine
- [ ] **Enhance existing LLMClient** (`src/llm_client.py`)
  - Add retry logic and error handling
  - Implement rate limiting and cost tracking
  - Add temperature control for deterministic outputs

- [ ] **Build SpecificityPromptBuilder class**
  - Implement 1-10 specificity scale logic
  - Create dynamic prompt generation based on specificity level
  - Add evidence threshold mapping per specificity level

- [ ] **Create ProductClassifier class**
  - Integrate LLMClient with specificity controls
  - Implement structured output parsing
  - Add validation for CSV format compliance

#### 1.2 Data Processing Pipeline
- [ ] **Product catalog preprocessing**
  - Parse minimal-product-catalog.csv
  - Extract and normalize product information
  - Handle HTML content in descriptions

- [ ] **Taxonomy processing**
  - Parse ingredients.xml.txt for ingredient definitions
  - Create health area category mappings
  - Build lookup structures for prompt context

### Phase 2: Validation Framework (Weeks 3-4)

#### 2.1 EMA Regulatory Validation
- [ ] **Build EMA data integration**
  - Create structured parser for collected monographs
  - Implement ingredient → health area mappings
  - Build regulatory approval lookup system

- [ ] **Implement GoldStandardValidator class**
  - Tiered confidence scoring (Tier 1: 10pts, Tier 2: 5pts, Tier 3: 2pts)
  - Multi-source evidence aggregation
  - Conflict resolution hierarchy (regulatory > expert > clinical)

- [ ] **Create validation test suite**
  - Unit tests for individual herb validations
  - Integration tests for classification pipeline
  - Regression tests for consistent outputs
  - Performance benchmarks for processing speed

#### 2.2 Quality Assurance Framework
- [ ] **Automated validation checks**
  - Format validation for CSV output
  - Confidence threshold enforcement
  - Regulatory compliance verification

- [ ] **Manual review workflow**
  - Flag low-confidence classifications
  - Generate human-readable validation reports
  - Track validation accuracy metrics

### Phase 3: Specificity Controls (Weeks 5-6)

#### 3.1 Specificity Scale Implementation
- [ ] **Prompt engineering by specificity level**
  - Liberal (1-3): Broad associations, traditional uses
  - Balanced (4-6): Reasonable evidence threshold
  - Conservative (7-10): Explicit claims only

- [ ] **Configuration management system**
  - YAML-based configuration files
  - Product-specific specificity overrides
  - Environment-based settings (dev/staging/prod)

#### 3.2 Testing and Optimization
- [ ] **A/B testing framework**
  - Compare results across specificity levels
  - Generate comparative analysis reports
  - Client feedback collection system

- [ ] **Performance optimization**
  - Batch processing capabilities
  - Caching for repeated classifications
  - Progress tracking and resumability

### Phase 4: Production System (Weeks 7-8)

#### 4.1 Production Pipeline
- [ ] **Batch processing system**
  - Process full ~800 product catalog
  - Error handling and recovery
  - Progress monitoring and reporting

- [ ] **Output generation**
  - Generate category_assignment.csv format
  - Create validation reports
  - Export confidence metrics

#### 4.2 Quality Monitoring
- [ ] **Metrics collection**
  - Classification accuracy tracking
  - Processing time monitoring
  - Cost per classification analysis

- [ ] **Continuous improvement**
  - Regular validation accuracy assessment
  - Prompt optimization based on results
  - Client feedback integration

## Technical Architecture

### Core Components

```
ic-ml/
├── src/
│   ├── llm_client.py                 # Enhanced LLM interface
│   ├── classification/
│   │   ├── __init__.py
│   │   ├── product_classifier.py     # Main classification engine
│   │   ├── specificity_builder.py    # Prompt engineering by specificity
│   │   └── output_formatter.py       # CSV generation and validation
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── gold_standard_validator.py # EMA/regulatory validation
│   │   ├── confidence_scorer.py       # Multi-tier scoring system
│   │   └── quality_assessor.py        # Automated QA checks
│   └── data/
│       ├── __init__.py
│       ├── product_parser.py          # Product catalog processing
│       └── taxonomy_parser.py         # Health area and ingredient parsing
├── tests/
│   ├── unit/
│   │   ├── test_classification.py     # Unit tests for classifiers
│   │   ├── test_validation.py         # Validation framework tests
│   │   └── test_specificity.py        # Specificity scale tests
│   ├── integration/
│   │   ├── test_end_to_end.py         # Full pipeline tests
│   │   └── test_ema_validation.py     # EMA integration tests
│   └── regression/
│       └── test_consistency.py        # Output consistency tests
├── config/
│   ├── classification_config.yaml     # Specificity and processing settings
│   ├── validation_config.yaml         # Validation framework settings
│   └── ema_mappings.yaml              # EMA → health area mappings
└── scripts/
    ├── run_classification.py          # Main execution script
    ├── validate_results.py             # Post-processing validation
    └── generate_reports.py             # Analysis and reporting
```

### Key Classes and Interfaces

```python
# Core classification interface
class ProductClassifier:
    def __init__(self, specificity_level: int = 5):
        self.specificity_level = specificity_level
        self.prompt_builder = SpecificityPromptBuilder(specificity_level)
        self.validator = GoldStandardValidator()

    def classify_product(self, product_data) -> ClassificationResult:
        # Main classification logic
        pass

# Specificity control system
class SpecificityPromptBuilder:
    def build_classification_prompt(self, product, taxonomy, specificity_level):
        # Dynamic prompt generation based on specificity
        pass

# Validation framework
class GoldStandardValidator:
    def validate_classification(self, ingredient, health_area):
        # Multi-tier validation using EMA, WHO, USP data
        pass
```

## Success Criteria

### Technical Metrics
- **Processing Speed**: <30 seconds per product classification
- **Accuracy**: >85% validation accuracy on manual spot checks
- **Coverage**: >95% of products receive at least one health area assignment
- **Consistency**: <5% variation in repeated classifications of same products

### Business Metrics
- **Client Satisfaction**: >4.0/5.0 rating on classification quality
- **Manual Review Rate**: <20% of classifications require human review
- **Cost Efficiency**: <$0.10 per product classification
- **Time to Market**: Complete ~800 product classification within 2 weeks

### Quality Metrics
- **Regulatory Compliance**: 100% compliance with EMA-approved uses where applicable
- **False Positive Rate**: <10% incorrect category assignments
- **Confidence Distribution**: >60% high or medium confidence classifications

## Risk Mitigation

### Technical Risks
- **LLM API Reliability**: Implement robust retry logic and fallback mechanisms
- **Output Format Consistency**: Extensive validation and testing of CSV generation
- **Processing Cost**: Monitor and optimize API usage, implement caching

### Data Quality Risks
- **Incomplete Product Information**: Handle missing or poor-quality product descriptions
- **Regulatory Data Gaps**: Use tiered validation approach, flag unknown herbs
- **Classification Conflicts**: Implement hierarchical decision rules

### Business Risks
- **Client Expectation Management**: Clear communication about iterative improvement process
- **Regulatory Compliance**: Focus on approved uses, avoid unsubstantiated health claims
- **Scalability**: Design system to handle catalog growth beyond initial 800 products

## Delivery Timeline

| Week | Deliverables | Key Milestones |
|------|-------------|----------------|
| 1-2 | Foundation Infrastructure | LLM engine, specificity system, data processing |
| 3-4 | Validation Framework | EMA integration, validation test suite |
| 5-6 | Specificity Controls | A/B testing, configuration management |
| 7-8 | Production System | Full catalog processing, quality monitoring |

## Next Steps

1. **Immediate (Week 1)**:
   - Enhance `src/llm_client.py` with specificity controls
   - Create `SpecificityPromptBuilder` class
   - Build EMA validation lookup from collected monographs

2. **Short-term (Weeks 2-3)**:
   - Implement `GoldStandardValidator` using EMA data
   - Create comprehensive test suite for validation
   - Build configuration management system

3. **Medium-term (Weeks 4-6)**:
   - Develop A/B testing framework for specificity optimization
   - Create client feedback collection system
   - Optimize performance for batch processing

This development plan provides a clear roadmap for implementing the herbal product classification system with regulatory validation and configurable specificity controls, ensuring high-quality results while minimizing manual review burden.