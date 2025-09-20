# Multi-Client Architecture Design

## Overview

This document outlines the architectural design for expanding IC-ML from a single-use case (product classification) to a multi-client, multi-use case platform supporting both the existing product classification and the new Health Quiz recommendation system.

## Current Architecture Analysis

### Reusable Components
- **LLMClient** (`src/llm_client.py`): Well-designed unified interface for OpenAI/Anthropic via LiteLLM
- **ModelConfigManager** (`src/model_config.py`): Good abstraction with override support
- **Analysis Engine** (`src/analysis_engine.py`): Modular analysis components

### Components Requiring Refactoring
- **RunManager** (`src/run_assign_cat.py`): Hardcoded for "assign-cat" use case
- **Product Classes** (`src/product_processor.py`): Specific to product catalog processing
- **Configuration System**: Single client metadata, global API settings

## Multi-Client Billing System Design

### 1. Client Configuration Structure

```yaml
# config/clients.yaml
clients:
  rogue_herbalist:
    name: "Rogue Herbalist"
    api_keys:
      openai: "sk-proj-..."  # Client-specific OpenAI key
      anthropic: "sk-ant-..."  # Client-specific Anthropic key
    use_cases:
      - "product_classification"
      - "health_quiz"
    default_model_tier: "ultra_fast"
    billing_contact: "admin@rogueherbalist.com"

  future_client_2:
    name: "Future Client"
    api_keys:
      openai: "sk-proj-..."
    use_cases:
      - "health_quiz"
    default_model_tier: "balanced"

# Global defaults
global:
  models: # Reference to existing models.yaml structure
  fallback_api_keys: # System defaults if client keys fail
```

### 2. Enhanced LLM Client with Multi-Client Support

```python
class MultiClientLLMClient:
    def __init__(self, client_id: str, use_case: str, model_override: Optional[str] = None):
        self.client_id = client_id
        self.use_case = use_case
        self.client_config = get_client_config(client_id)

        # Set client-specific API keys
        self._setup_client_credentials()

        # Initialize base LLM client with model config
        self.llm_client = LLMClient(model_override)

        # Enhanced usage tracking with client/use_case dimensions
        self.usage_tracker = ClientUsageTracker(client_id, use_case)
```

### 3. Usage Tracking with Client Dimensions

```python
@dataclass
class ClientUsage:
    client_id: str
    use_case: str
    timestamp: datetime
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    request_metadata: Dict[str, Any]

class ClientUsageTracker:
    def track_request(self, response, metadata: Dict[str, Any] = None):
        """Track usage with client/use case dimensions."""
        usage = ClientUsage(
            client_id=self.client_id,
            use_case=self.use_case,
            timestamp=datetime.now(),
            model_used=response.model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            cost_usd=litellm.cost_per_token(response.model,
                                          response.usage.prompt_tokens,
                                          response.usage.completion_tokens),
            request_metadata=metadata or {}
        )
        self._persist_usage(usage)
```

## Use Case Abstraction Framework

### 1. Abstract Base Use Case

```python
from abc import ABC, abstractmethod

class UseCase(ABC):
    """Abstract base class for all use cases."""

    def __init__(self, client_id: str, config: Dict[str, Any]):
        self.client_id = client_id
        self.config = config
        self.llm_client = MultiClientLLMClient(client_id, self.get_use_case_name())

    @abstractmethod
    def get_use_case_name(self) -> str:
        """Return the use case identifier."""
        pass

    @abstractmethod
    def process_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single request for this use case."""
        pass

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for this use case."""
        pass

    @abstractmethod
    def get_prompt_template(self) -> str:
        """Get the LLM prompt template for this use case."""
        pass
```

### 2. Product Classification Use Case (Refactored)

```python
class ProductClassificationUseCase(UseCase):
    def get_use_case_name(self) -> str:
        return "product_classification"

    def process_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process product classification request."""
        products = input_data['products']
        taxonomy = input_data['taxonomy']

        # Use existing batch processing logic (refactored)
        processor = ProductBatchProcessor(self.llm_client)
        results = processor.process_batch(products, taxonomy)

        return {
            'classifications': results,
            'metadata': {
                'use_case': self.get_use_case_name(),
                'client_id': self.client_id,
                'processed_count': len(products)
            }
        }
```

### 3. Health Quiz Use Case (New)

```python
class HealthQuizUseCase(UseCase):
    def get_use_case_name(self) -> str:
        return "health_quiz"

    def process_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process health quiz recommendation request."""
        quiz_data = self.validate_and_extract_quiz_data(input_data)

        # Generate recommendations using LLM
        recommendations = self._generate_recommendations(quiz_data)

        # Link to RH products
        product_links = self._link_to_products(recommendations, quiz_data)

        return {
            'recommendations': recommendations,
            'product_links': product_links,
            'metadata': {
                'use_case': self.get_use_case_name(),
                'client_id': self.client_id,
                'primary_category': quiz_data.get('primary_health_area'),
                'secondary_category': quiz_data.get('secondary_health_area')
            }
        }

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate health quiz input."""
        required_fields = ['health_issue_description', 'primary_health_area']
        return all(field in input_data for field in required_fields)
```

## Health Quiz Specific Architecture

### 1. Quiz Input Data Structure

```python
@dataclass
class HealthQuizInput:
    health_issue_description: str  # Free text description
    tried_already: Optional[str]   # What they've tried, outcomes
    primary_health_area: str       # From 20 categories
    secondary_health_area: Optional[str]  # Optional second category

    # Optional additional fields for future expansion
    age_range: Optional[str] = None
    severity_level: Optional[int] = None
    budget_preference: Optional[str] = None

@dataclass
class HealthQuizOutput:
    general_recommendations: List[str]  # LLM-generated advice
    specific_products: List[ProductRecommendation]  # RH products
    educational_content: List[str]  # Health information
    metadata: Dict[str, Any]  # Tracking info
```

### 2. Product Recommendation Engine

```python
class ProductRecommendationEngine:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.product_catalog = self._load_client_catalog(client_id)
        self.category_mapping = self._load_category_mapping()

    def recommend_products(self,
                          health_categories: List[str],
                          quiz_context: HealthQuizInput,
                          max_recommendations: int = 5) -> List[ProductRecommendation]:
        """Generate product recommendations based on health categories."""

        # Filter products by relevant categories
        relevant_products = self._filter_by_categories(health_categories)

        # Score products based on quiz context
        scored_products = self._score_products(relevant_products, quiz_context)

        # Return top recommendations
        return scored_products[:max_recommendations]

@dataclass
class ProductRecommendation:
    product_id: str
    title: str
    description: str
    relevance_score: float
    purchase_link: str
    category_match: str  # Which health category it matches
    rationale: str  # Why it's recommended
```

## Web Service Architecture

### 1. API Endpoints

```python
# FastAPI or Flask endpoints
@app.post("/api/v1/health-quiz/{client_id}")
async def process_health_quiz(client_id: str, quiz_data: HealthQuizInput):
    """Process health quiz for specific client."""

    # Validate client exists and has health_quiz use case
    client_config = get_client_config(client_id)
    if "health_quiz" not in client_config.use_cases:
        raise HTTPException(status_code=403, detail="Use case not enabled")

    # Process quiz
    use_case = HealthQuizUseCase(client_id, client_config)
    result = use_case.process_request(quiz_data.dict())

    # Track usage for billing
    await track_api_usage(client_id, "health_quiz", result)

    return result

@app.post("/api/v1/product-classification/{client_id}")
async def process_product_classification(client_id: str, products: List[Product]):
    """Process product classification for specific client."""
    # Similar pattern for existing use case
```

### 2. Real-time vs Batch Processing

```python
class ProcessingMode(Enum):
    REALTIME = "realtime"  # Individual requests (Health Quiz)
    BATCH = "batch"        # Bulk processing (Product Classification)

class UniversalProcessor:
    def __init__(self, client_id: str, use_case: str, mode: ProcessingMode):
        self.client_id = client_id
        self.use_case_handler = self._get_use_case_handler(use_case)
        self.mode = mode

    async def process(self, input_data: Any) -> Any:
        if self.mode == ProcessingMode.REALTIME:
            return await self._process_realtime(input_data)
        else:
            return await self._process_batch(input_data)
```

## Configuration Management

### 1. Enhanced Configuration Structure

```yaml
# config/clients/rogue_herbalist.yaml
client_id: "rogue_herbalist"
name: "Rogue Herbalist"

# API credentials (stored securely)
api_keys:
  openai_key_env: "RH_OPENAI_API_KEY"
  anthropic_key_env: "RH_ANTHROPIC_API_KEY"

# Enabled use cases
use_cases:
  product_classification:
    enabled: true
    default_model: "gpt4o_mini"
    batch_size: 10

  health_quiz:
    enabled: true
    default_model: "sonnet"
    recommendation_count: 5
    include_educational_content: true

# Product catalog configuration
product_catalog:
  source: "data/rogue-herbalist/minimal-product-catalog.csv"
  taxonomy: "data/rogue-herbalist/taxonomy_trimmed.xml"
  base_url: "https://rogueherbalist.com/products/"

# Billing settings
billing:
  cost_tracking: true
  detailed_logs: true
  alert_threshold_usd: 100.0
```

## Implementation Plan

### Phase 1: Core Infrastructure
1. ✅ Multi-client configuration system
2. ✅ Enhanced LLM client with client-specific credentials
3. ✅ Usage tracking with client/use case dimensions
4. ✅ Abstract use case framework

### Phase 2: Health Quiz Implementation
1. ✅ Health quiz use case implementation
2. ✅ Product recommendation engine
3. ✅ Quiz input/output data structures
4. ✅ Integration with existing product catalog

### Phase 3: Web Service
1. ✅ FastAPI web service framework
2. ✅ API endpoints for both use cases
3. ✅ Real-time processing for health quiz
4. ✅ Authentication and client validation

### Phase 4: Migration and Testing
1. ✅ Migrate existing product classification to new framework
2. ✅ Comprehensive testing of both use cases
3. ✅ Documentation and deployment guides
4. ✅ Cost tracking validation

## Benefits of This Architecture

1. **Scalability**: Easy to add new clients and use cases
2. **Cost Transparency**: Granular tracking per client/use case
3. **Security**: Client-specific API keys and access control
4. **Maintainability**: Shared infrastructure with use case specialization
5. **Business Model**: Clear billing separation enables multi-client revenue

## Migration Strategy

1. **Backward Compatibility**: Existing scripts continue to work
2. **Gradual Migration**: Move components one at a time
3. **Configuration Migration**: Convert existing config to new format
4. **Testing**: Validate both old and new systems during transition

This architecture provides a solid foundation for the Health Quiz use case while maintaining and enhancing the existing product classification capabilities.