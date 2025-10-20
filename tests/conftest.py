"""
Shared pytest fixtures and test configuration for ic-ml test suite.
"""

import pytest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock
import tempfile
import csv


@pytest.fixture
def mock_llm_response():
    """Mock LiteLLM completion response."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = """{
        "general_advice": [
            "Consider consulting with a healthcare professional",
            "Focus on a balanced diet with plenty of vegetables",
            "Ensure adequate sleep and stress management"
        ],
        "herbal_categories": ["adaptogenic herbs", "digestive herbs"],
        "lifestyle_suggestions": ["Stay hydrated", "Regular exercise"],
        "follow_up_questions": ["How long have you experienced this issue?"],
        "consultation_needed": false,
        "reasoning": "General wellness approach recommended"
    }"""

    # Mock usage data
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.model = "openai/gpt-4o-mini"

    return mock_response


@pytest.fixture
def sample_product_catalog() -> List[Dict[str, Any]]:
    """Sample product catalog for testing."""
    from src.product_recommendation_engine import ProductCatalogItem

    products = [
        ProductCatalogItem(
            id="TEST-001",
            title="Immune Support Blend",
            description="Organic blend of echinacea, elderberry, and astragalus for immune support",
            short_description="Boost your immunity naturally",
            ingredients=["echinacea", "elderberry"],
            categories=["immune_support"],
            subcategories=["immunity"],
            price=29.99,
            in_stock=True,
            rating=4.5,
            review_count=42,
            tags=["immune", "organic"],
            slug="immune-support-blend"
        ),
        ProductCatalogItem(
            id="TEST-002",
            title="Digestive Harmony Tea",
            description="Soothing blend with ginger, peppermint, and chamomile for digestive health",
            short_description="Support healthy digestion",
            ingredients=["ginger", "chamomile"],
            categories=["digestive_health"],
            subcategories=["digestion"],
            price=19.99,
            in_stock=True,
            rating=4.8,
            review_count=87,
            tags=["digestive", "tea"],
            slug="digestive-harmony-tea"
        ),
        ProductCatalogItem(
            id="TEST-003",
            title="Stress Relief Formula",
            description="Adaptogenic herbs including ashwagandha and rhodiola for stress management",
            short_description="Natural stress support",
            ingredients=["ashwagandha", "rhodiola"],
            categories=["stress_relief"],
            subcategories=["adaptogens"],
            price=34.99,
            in_stock=True,
            rating=4.7,
            review_count=63,
            tags=["stress", "adaptogen"],
            slug="stress-relief-formula"
        ),
        ProductCatalogItem(
            id="TEST-004",
            title="Out of Stock Product",
            description="This product is currently unavailable",
            short_description="Unavailable",
            ingredients=[],
            categories=["test"],
            subcategories=[],
            price=9.99,
            in_stock=False,
            rating=None,
            review_count=0,
            tags=[],
            slug="out-of-stock"
        ),
    ]

    return products


@pytest.fixture
def sample_health_quiz_input():
    """Valid HealthQuizInput instance for testing."""
    from src.health_quiz_use_case import HealthQuizInput

    return HealthQuizInput(
        health_issue_description="I've been experiencing frequent bloating and gas after meals",
        tried_already="I've tried eliminating dairy and reducing portion sizes",
        primary_health_area="digestive_health",
        secondary_health_area="stress_relief",
        age_range="30-40",
        severity_level=5,
        lifestyle_factors="Desk job, moderate exercise"
    )


@pytest.fixture
def test_config():
    """Mock model configuration for testing."""
    from src.model_config import ModelConfig

    return ModelConfig(
        model="openai/gpt-4o-mini",
        max_tokens=1000,
        temperature=0.0,
        description="Test configuration"
    )


@pytest.fixture
def temp_product_catalog_csv():
    """Create a temporary CSV file with product catalog data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['id', 'name', 'description', 'short_description', 'slug'])
        # Write sample products
        writer.writerow([
            'TEST-001',
            'Immune Support Blend',
            'Organic blend of echinacea and elderberry for immune support',
            'Boost immunity naturally',
            'immune-support-blend'
        ])
        writer.writerow([
            'TEST-002',
            'Digestive Harmony Tea',
            'Soothing ginger and chamomile tea for digestive health',
            'Support healthy digestion',
            'digestive-harmony-tea'
        ])

        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_config_yaml():
    """Create a temporary YAML config file for testing."""
    import yaml

    config_data = {
        'default': {
            'model': 'openai/gpt-4o-mini',
            'max_tokens': 1000,
            'temperature': 0.0
        },
        'models': {
            'test_model': {
                'model': 'openai/gpt-4o',
                'max_tokens': 2000,
                'temperature': 0.5,
                'description': 'Test model configuration'
            }
        },
        'experiments': {
            'test_experiment': {
                'model': 'anthropic/claude-3-haiku-20240307',
                'max_tokens': 500,
                'temperature': 0.7,
                'description': 'Test experiment'
            }
        },
        'api': {
            'retry_attempts': 3,
            'initial_retry_delay': 30
        },
        'metadata': {
            'client': 'test_client',
            'business': 'test_business'
        },
        'client_tracking': {
            'client': 'test_client',
            'use_case': 'test_use_case',
            'project': 'test_project',
            'environment': 'test',
            'tags': ['test']
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def mock_litellm_completion(mocker, mock_llm_response):
    """Mock litellm.completion for synchronous LLM calls."""
    return mocker.patch('src.llm_client.completion', return_value=mock_llm_response)


@pytest.fixture
def mock_litellm_async_completion(mocker, mock_llm_response):
    """Mock litellm.completion for async LLM calls."""
    async_mock = AsyncMock(return_value=mock_llm_response)
    return mocker.patch('src.llm_client.completion', side_effect=async_mock)


@pytest.fixture
def mock_completion_cost(mocker):
    """Mock litellm.completion_cost for cost calculation."""
    return mocker.patch('src.llm_client.completion_cost', return_value=0.0003)


@pytest.fixture
def sample_formbricks_payload() -> Dict[str, Any]:
    """Sample Formbricks webhook payload for testing."""
    return {
        "event": "responseFinished",
        "data": {
            "id": "test-response-123",
            "data": {
                "d9klpkum9vi8x9vkunhu63fn": ["", "", "test@example.com", "", ""],
                "dc185mu0h2xzutpzfgq8eyjy": "I have trouble sleeping at night",
                "ty1zv10pffpxh2a2bymi2wz7": "mn3195wdsqv6qf80tt299v2q",  # Sleep Issues
                "iht7n48iwkoc1jc8ubnzrqi7": 6,
                "ud6nnuhrgf9trqwe8j3kibii": "Tried melatonin supplements",
                "yru7w3e402yk8vpf1dfbw0tr": "nults2ndbrn6bovvs4ce03ax",  # 26-35
                "pr4jtzy9epmquvwdksj9tctb": "High stress job"
            }
        }
    }


@pytest.fixture
def mock_resend_api(mocker):
    """Mock the Resend API for email sending."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"id": "test-email-id"}'

    mock_client = Mock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    return mocker.patch('httpx.AsyncClient', return_value=mock_client)


@pytest.fixture(autouse=True)
def reset_config_manager():
    """Reset the global config manager before each test."""
    import src.model_config as model_config
    model_config._config_manager = None
    yield
    model_config._config_manager = None


@pytest.fixture
def mock_use_case_config():
    """Mock use case configuration."""
    return {
        'product_url_template': 'https://rogueherbalist.com/product/{product_slug}/',
        'max_recommendations': 5,
        'min_relevance_score': 0.3
    }


@pytest.fixture
def use_case_config():
    """Proper UseCaseConfig object for HealthQuizUseCase testing."""
    from src.use_case_framework import UseCaseConfig, ProcessingMode
    return UseCaseConfig(
        client_id="test_client",
        use_case_name="health_quiz",
        model_config="gpt4o_mini",
        processing_mode=ProcessingMode.REALTIME,
        custom_settings={
            "consultation_threshold": 7,
            "max_recommendations": 5,
            "min_relevance_score": 0.3,
            "product_url_template": "https://rogueherbalist.com/product/{product_slug}/"
        }
    )
