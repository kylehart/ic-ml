# Specificity Scale Design for Health Area Classification

## Overview

This document outlines the design and implementation of a configurable specificity scale (1-10) for health area classification in the Rogue Herbalist product classification system. The specificity scale allows fine-grained control over classification behavior, balancing precision and recall based on business requirements.

## Conceptual Framework

### Specificity Scale Definition

The specificity scale operates on a 1-10 continuum:

- **1-3 (Liberal/Broad)**: High recall, lower precision
  - Assigns categories based on loose associations
  - Includes indirect benefits and traditional uses
  - More categories per product
  - Errs on side of inclusion

- **4-6 (Balanced)**: Moderate recall and precision
  - Requires reasonable evidence for classification
  - Balances comprehensiveness with accuracy
  - **Default setting: Level 5**

- **7-10 (Conservative/Precise)**: Lower recall, high precision
  - Only assigns categories with strong, direct evidence
  - Fewer, more precise categories
  - Requires explicit claims or well-documented benefits

### Classification Examples

**Example Product**: "Hemp Adapt - Hemp extract with ashwagandha, reishi, skullcap, and tulsi"

**Specificity Level 1-3 (Liberal)**:
```csv
health-areas,stress-mood-anxiety,adaptogenic-support,,3677
health-areas,stress-mood-anxiety,stress-anxiety-relief,,3677
health-areas,immune-support,mushroom-immune,,3677
health-areas,sleep-relaxation,sleep-support,,3677
health-areas,focus-memory-cognition,cognitive-support,,3677
health-areas,pain-inflammation,general-inflammation,,3677
```

**Specificity Level 5 (Balanced)**:
```csv
health-areas,stress-mood-anxiety,adaptogenic-support,,3677
health-areas,stress-mood-anxiety,stress-anxiety-relief,,3677
health-areas,immune-support,mushroom-immune,,3677
```

**Specificity Level 7-10 (Conservative)**:
```csv
health-areas,stress-mood-anxiety,adaptogenic-support,,3677
```

## Technical Implementation

### Core Components

#### 1. SpecificityPromptBuilder Class

```python
class SpecificityPromptBuilder:
    def __init__(self, specificity_level: int = 5):
        self.specificity_level = specificity_level

    def build_classification_prompt(self, product, taxonomy):
        base_prompt = self._get_base_prompt(product, taxonomy)
        specificity_instructions = self._get_specificity_instructions()
        evidence_threshold = self._get_evidence_threshold()

        return f"""
{base_prompt}

{specificity_instructions}
{evidence_threshold}

SPECIFICITY LEVEL: {self.specificity_level}/10
"""

    def _get_specificity_instructions(self):
        if self.specificity_level <= 3:  # Liberal
            return """
CLASSIFICATION APPROACH: Liberal/Broad
- Include categories if there's ANY reasonable connection
- Consider indirect benefits and traditional uses
- Err on the side of inclusion rather than exclusion
- Include related/adjacent health areas
"""
        elif self.specificity_level >= 7:  # Conservative
            return """
CLASSIFICATION APPROACH: Conservative/Precise
- Only include categories with DIRECT, EXPLICIT evidence
- Require clear ingredient-to-benefit connections
- Exclude speculative or indirect associations
- Focus on primary, well-documented uses only
"""
        else:  # Balanced
            return """
CLASSIFICATION APPROACH: Balanced
- Include categories with reasonable evidence
- Consider both direct effects and well-established traditional uses
- Avoid speculative connections but include probable benefits
- Balance comprehensiveness with accuracy
"""

    def _get_evidence_threshold(self):
        thresholds = {
            1: "ANY mention or loose association",
            2: "Weak evidence or traditional use",
            3: "Some supporting evidence",
            4: "Reasonable evidence or multiple indicators",
            5: "Good evidence from ingredients or description",
            6: "Strong evidence with clear connections",
            7: "Very strong evidence, explicit claims",
            8: "Explicit claims with ingredient backing",
            9: "Direct clinical claims or specific targeting",
            10: "Only FDA-approved or clinically proven claims"
        }

        threshold = thresholds.get(self.specificity_level, thresholds[5])
        return f"EVIDENCE THRESHOLD: {threshold}"
```

#### 2. HealthAreaClassifier Integration

```python
class HealthAreaClassifier:
    def __init__(self, specificity_level: int = 5):
        self.specificity_level = specificity_level
        self.prompt_builder = SpecificityPromptBuilder(specificity_level)

    def classify_product(self, product_data, taxonomy):
        prompt = self.prompt_builder.build_classification_prompt(
            product_data, taxonomy
        )

        # Get LLM classification
        raw_classifications = self.llm_client.complete_sync(prompt)

        # Apply specificity-based post-processing
        return self._apply_specificity_filter(
            raw_classifications,
            product_data
        )

    def _apply_specificity_filter(self, classifications, product):
        """Apply additional specificity-based filtering"""
        if self.specificity_level >= 7:
            # Conservative: Remove categories without explicit evidence
            return self._filter_conservative(classifications, product)
        elif self.specificity_level <= 3:
            # Liberal: Add related categories
            return self._expand_liberal(classifications, product)
        else:
            return classifications

    def _filter_conservative(self, classifications, product):
        """Remove classifications lacking explicit evidence"""
        # Implementation: Check for direct keyword matches,
        # explicit health claims, specific ingredient benefits
        pass

    def _expand_liberal(self, classifications, product):
        """Add related/adjacent categories"""
        # Implementation: Add categories for ingredient families,
        # traditional use categories, related health areas
        pass
```

#### 3. Configuration Management

```yaml
# config/classification_config.yaml
classification:
  specificity_level: 5  # 1-10 scale (default)
  min_categories_per_product: 1
  max_categories_per_product: 8

specificity_overrides:
  # Product-specific overrides for special cases
  hemp_products: 4      # More liberal for hemp (complex benefits)
  single_ingredient: 7  # More conservative for simple products
  tinctures: 5         # Balanced for tinctures
  teas: 6              # Slightly conservative for tea blends

validation:
  manual_review_threshold: 3  # Flag products with >3 categories for review
  confidence_threshold: 0.7   # Minimum confidence for auto-assignment
```

## Validation and Iteration Strategy

### 1. A/B Testing Framework

```python
class SpecificityValidator:
    def run_specificity_comparison(self, product_sample, levels=[3, 5, 7]):
        """Compare classification results across specificity levels"""
        results = {}

        for level in levels:
            classifier = HealthAreaClassifier(specificity_level=level)
            results[level] = classifier.classify_batch(product_sample)

        return self._generate_comparison_report(results)

    def _generate_comparison_report(self, results):
        """Generate metrics comparing specificity levels"""
        report = {
            'coverage': {},      # % products with at least one category
            'avg_categories': {}, # Average categories per product
            'category_distribution': {},  # Distribution across health areas
            'overlap_analysis': {}       # Category overlap between levels
        }

        for level, classifications in results.items():
            report['coverage'][level] = self._calculate_coverage(classifications)
            report['avg_categories'][level] = self._calculate_avg_categories(classifications)
            # Additional metrics...

        return report
```

### 2. Client Feedback Integration

```python
class ClientFeedbackCollector:
    def present_classification_options(self, product, levels=[3, 5, 7]):
        """Present classification results at different specificity levels"""
        options = {}

        for level in levels:
            classifier = HealthAreaClassifier(specificity_level=level)
            options[f"Level_{level}"] = classifier.classify_product(product)

        return {
            'product': product,
            'options': options,
            'recommendation': options['Level_5'],  # Default recommendation
            'feedback_form': self._generate_feedback_form()
        }

    def _generate_feedback_form(self):
        return {
            'preferred_level': None,  # Client selects preferred specificity
            'missing_categories': [], # Categories client thinks should be included
            'incorrect_categories': [], # Categories client thinks are wrong
            'overall_satisfaction': None  # 1-5 scale
        }
```

### 3. Performance Metrics

| Metric | Description | Target |
|--------|-------------|---------|
| **Coverage** | % of products receiving ≥1 health area | >95% |
| **Precision** | % of assigned categories deemed correct | >85% |
| **Recall** | % of expected categories captured | >80% |
| **Client Satisfaction** | Subjective quality rating | >4.0/5.0 |
| **Processing Time** | Average time per product | <30 seconds |
| **Cost per Classification** | LLM API cost per product | <$0.10 |

## Deployment Strategy

### Phase 1: Implementation
- Build SpecificityPromptBuilder and integrate with existing LLMClient
- Implement configuration management system
- Create validation framework

### Phase 2: Calibration
- Run specificity comparison on sample products (n=50)
- Collect initial client feedback on different specificity levels
- Establish baseline metrics

### Phase 3: Optimization
- Iteratively adjust specificity level based on client feedback
- Fine-tune prompts for optimal performance at chosen specificity
- Implement product-specific overrides as needed

### Phase 4: Production
- Deploy with specificity_level=5 as default
- Monitor performance metrics
- Establish regular review cycles for specificity adjustments

## Risk Mitigation

### Potential Issues and Solutions

1. **Inconsistent Classifications**
   - Risk: Same product classified differently across runs
   - Solution: Use temperature=0 for deterministic outputs, implement caching

2. **Edge Case Handling**
   - Risk: Unusual products don't fit standard specificity patterns
   - Solution: Product-specific overrides, fallback to manual review

3. **Client Expectation Management**
   - Risk: Clients expect perfect classifications immediately
   - Solution: Clear communication about iterative improvement process

4. **Cost Escalation**
   - Risk: High specificity levels require more complex prompts
   - Solution: Monitor API costs, optimize prompts for efficiency

## Success Criteria

The specificity scale implementation will be considered successful when:

1. **Client Control**: Client can adjust specificity level and see predictable changes in classification behavior
2. **Quality Metrics**: Achieve target precision/recall at chosen specificity level
3. **Operational Efficiency**: System processes full catalog within acceptable time/cost constraints
4. **Scalability**: Framework supports future taxonomy expansions and product types
5. **Maintainability**: Non-technical users can adjust specificity settings without developer intervention

## Conclusion

The specificity scale provides a powerful, intuitive control mechanism for balancing precision and recall in health area classification. By implementing this system, we enable iterative optimization with client feedback while maintaining technical flexibility for future enhancements.