# Implementation Guide: Multi-Use Case IC-ML Platform

## Overview

This guide provides step-by-step instructions for implementing the multi-use case IC-ML platform, including the new Health Quiz feature and the refactored product classification system.

## Prerequisites

### System Requirements
- Python 3.8+
- FastAPI framework
- LiteLLM library
- PostgreSQL or SQLite for usage tracking
- Redis for caching (optional)
- Node.js for frontend development

### API Keys Required
- OpenAI API key (per client)
- Anthropic API key (per client)
- Optional: Additional LLM provider keys

### Development Tools
- Docker for containerization
- Git for version control
- Postman or similar for API testing
- VS Code or preferred IDE

## Implementation Steps

### Step 1: Environment Setup

1. **Clone and Setup Project**
```bash
git clone <repository-url>
cd ic-ml
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. **Environment Configuration**
```bash
# Create .env file
cp .env.example .env

# Configure API keys
echo "RH_OPENAI_API_KEY=sk-proj-..." >> .env
echo "RH_ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

3. **Database Setup**
```bash
# Initialize usage tracking database
python scripts/init_database.py
```

### Step 2: Multi-Client Configuration

1. **Create Client Configuration**
```bash
mkdir -p config/clients
```

2. **Configure Rogue Herbalist Client**
```yaml
# config/clients/rogue_herbalist.yaml
client_id: "rogue_herbalist"
name: "Rogue Herbalist"

api_keys:
  openai_key_env: "RH_OPENAI_API_KEY"
  anthropic_key_env: "RH_ANTHROPIC_API_KEY"

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

product_catalog:
  source: "data/rogue-herbalist/minimal-product-catalog.csv"
  taxonomy: "data/rogue-herbalist/taxonomy_trimmed.xml"
  base_url: "https://rogueherbalist.com/products/"

billing:
  cost_tracking: true
  detailed_logs: true
  alert_threshold_usd: 100.0
```

### Step 3: Use Case Registration

1. **Register Health Quiz Use Case**
```python
# In src/main.py or startup script
from health_quiz_use_case import HealthQuizUseCase
from use_case_framework import use_case_registry

# Registration happens automatically via @register_use_case decorator
# Verify registration
print("Registered use cases:", use_case_registry.list_use_cases())
```

2. **Migrate Product Classification Use Case**
```python
# Create product_classification_use_case.py
from use_case_framework import BatchUseCase, register_use_case
from product_processor import ProductCatalogReader, BatchProcessor

@register_use_case("product_classification")
class ProductClassificationUseCase(BatchUseCase):
    # Implementation details in separate file
    pass
```

### Step 4: Web Service Deployment

1. **Start Development Server**
```bash
uvicorn src.web_service:app --reload --host 0.0.0.0 --port 8000
```

2. **Test Health Check**
```bash
curl http://localhost:8000/health
```

3. **Test Authentication**
```bash
curl -H "Authorization: Bearer rogue_herbalist_token" \
     http://localhost:8000/api/v1/admin/clients
```

### Step 5: Health Quiz Integration

1. **Test Health Quiz API**
```bash
curl -X POST "http://localhost:8000/api/v1/health-quiz/rogue_herbalist" \
     -H "Authorization: Bearer rogue_herbalist_token" \
     -H "Content-Type: application/json" \
     -d '{
       "health_issue_description": "I have been experiencing frequent digestive discomfort after meals",
       "primary_health_area": "digestive_health",
       "severity_level": 6
     }'
```

2. **Verify Product Recommendations**
- Check that response includes product recommendations
- Verify purchase links are properly formatted
- Confirm educational content is relevant

### Step 6: Product Catalog Integration

1. **Prepare Product Catalog**
```bash
# Ensure catalog is properly formatted
python scripts/validate_catalog.py data/rogue-herbalist/minimal-product-catalog.csv
```

2. **Test Product Recommendation Engine**
```python
from product_recommendation_engine import ProductRecommendationEngine
from health_quiz_use_case import HealthQuizInput

engine = ProductRecommendationEngine("rogue_herbalist")
quiz_input = HealthQuizInput(
    health_issue_description="Joint pain and stiffness",
    primary_health_area="joint_health"
)
recommendations = engine.recommend_products(quiz_input)
print(f"Found {len(recommendations)} recommendations")
```

### Step 7: Frontend Integration

1. **Create React Frontend** (optional for MVP)
```bash
npx create-react-app health-quiz-frontend
cd health-quiz-frontend
npm install axios react-router-dom
```

2. **Basic Quiz Component**
```jsx
// src/components/HealthQuiz.js
import React, { useState } from 'react';
import axios from 'axios';

const HealthQuiz = () => {
  const [formData, setFormData] = useState({
    health_issue_description: '',
    primary_health_area: '',
    severity_level: 5
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/health-quiz/rogue_herbalist',
        formData,
        {
          headers: {
            'Authorization': 'Bearer rogue_herbalist_token',
            'Content-Type': 'application/json'
          }
        }
      );
      console.log('Recommendations:', response.data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
    </form>
  );
};
```

## Migration from Current System

### Step 1: Backup Current System
```bash
# Create backup of current runs
cp -r runs runs_backup_$(date +%Y%m%d)

# Backup current configuration
cp -r config config_backup_$(date +%Y%m%d)
```

### Step 2: Gradual Migration
1. **Keep existing scripts working** during transition
2. **Test new framework** with small product batches
3. **Verify cost tracking** accuracy
4. **Migrate experimental runs** to new format

### Step 3: Update Existing Scripts
```python
# Update run_assign_cat.py to use new framework
from use_case_framework import UseCaseManager
from product_classification_use_case import ProductClassificationUseCase

# Maintain backward compatibility
if __name__ == "__main__":
    # Existing command-line interface
    # Internal implementation uses new framework
    pass
```

## Testing Strategy

### Unit Tests
```bash
# Test use case framework
python -m pytest tests/test_use_case_framework.py

# Test health quiz implementation
python -m pytest tests/test_health_quiz.py

# Test product recommendation engine
python -m pytest tests/test_recommendation_engine.py
```

### Integration Tests
```bash
# Test complete health quiz flow
python -m pytest tests/test_health_quiz_integration.py

# Test API endpoints
python -m pytest tests/test_web_service.py

# Test multi-client functionality
python -m pytest tests/test_multi_client.py
```

### Load Testing
```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f tests/load_test_health_quiz.py --host=http://localhost:8000
```

## Monitoring and Analytics

### Usage Tracking Setup
```python
# Database schema for usage tracking
CREATE TABLE usage_logs (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50),
    use_case VARCHAR(50),
    timestamp TIMESTAMP,
    model_used VARCHAR(50),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    cost_usd DECIMAL(10,6),
    success BOOLEAN,
    processing_time FLOAT,
    metadata JSONB
);
```

### Analytics Dashboard
```python
# Basic analytics queries
SELECT
    client_id,
    use_case,
    COUNT(*) as requests,
    SUM(cost_usd) as total_cost,
    AVG(processing_time) as avg_time
FROM usage_logs
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY client_id, use_case;
```

## Deployment Configuration

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/

EXPOSE 8000
CMD ["uvicorn", "src.web_service:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Environment Variables
```bash
# Production .env
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@localhost/icml
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
MONITORING_ENABLED=true
```

### Load Balancer Configuration
```nginx
# nginx.conf
upstream icml_backend {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;
    server_name api.rogueherbalist.com;

    location / {
        proxy_pass http://icml_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Security Considerations

### API Security
- Implement proper rate limiting
- Use HTTPS in production
- Validate all input data
- Implement proper authentication/authorization
- Log security events

### Data Privacy
- Encrypt sensitive health information
- Implement data retention policies
- Provide customer data export/deletion
- Comply with HIPAA guidelines where applicable

### Infrastructure Security
- Use environment variables for secrets
- Implement network security groups
- Regular security audits
- Automated vulnerability scanning

## Troubleshooting

### Common Issues

1. **LLM API Rate Limiting**
```python
# Implement exponential backoff
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

2. **High LLM Costs**
- Monitor usage dashboards
- Implement cost alerts
- Use cheaper models for development
- Cache common responses

3. **Slow Response Times**
- Implement caching for product recommendations
- Use async processing for non-critical tasks
- Monitor database query performance
- Consider using faster LLM models

4. **Database Connection Issues**
- Implement connection pooling
- Add retry logic for database operations
- Monitor database health
- Implement graceful degradation

## Performance Optimization

### Caching Strategy
```python
# Redis caching for product recommendations
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_recommendations(quiz_hash, recommendations):
    cache_key = f"recommendations:{quiz_hash}"
    redis_client.setex(
        cache_key,
        3600,  # 1 hour TTL
        json.dumps(recommendations)
    )
```

### Database Optimization
- Index frequently queried fields
- Use connection pooling
- Implement read replicas for analytics
- Regular database maintenance

### LLM Cost Optimization
- Use prompt engineering to reduce token usage
- Implement intelligent model selection
- Cache common responses
- Monitor and alert on cost thresholds

This implementation guide provides a comprehensive roadmap for building and deploying the multi-use case IC-ML platform with the Health Quiz feature.