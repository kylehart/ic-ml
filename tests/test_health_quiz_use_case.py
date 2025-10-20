"""
Unit tests for HealthQuizUseCase implementation.

Tests input validation, consultation logic, and business logic without LLM calls.
"""

import pytest
from src.health_quiz_use_case import (
    HealthQuizInput,
    HealthQuizOutput,
    ProductRecommendation,
    HealthQuizUseCase
)


class TestHealthQuizInput:
    """Test HealthQuizInput data structure."""

    def test_to_dict_filters_none(self):
        """Test to_dict filters out None values."""
        quiz_input = HealthQuizInput(
            health_issue_description="Test issue",
            tried_already=None,
            primary_health_area="immune_support"
        )

        result = quiz_input.to_dict()

        assert "health_issue_description" in result
        assert "primary_health_area" in result
        assert "tried_already" not in result

    def test_from_dict_creates_instance(self):
        """Test from_dict creates proper instance."""
        data = {
            "health_issue_description": "Test issue",
            "primary_health_area": "digestive_health",
            "severity_level": 5
        }

        quiz_input = HealthQuizInput.from_dict(data)

        assert quiz_input.health_issue_description == "Test issue"
        assert quiz_input.primary_health_area == "digestive_health"
        assert quiz_input.severity_level == 5

    def test_all_fields_populated(self):
        """Test instance with all optional fields."""
        quiz_input = HealthQuizInput(
            health_issue_description="Full test",
            tried_already="Tried multiple things",
            primary_health_area="stress_relief",
            secondary_health_area="sleep_support",
            age_range="30-40",
            severity_level=7,
            budget_preference="medium",
            lifestyle_factors="Active lifestyle"
        )

        assert quiz_input.health_issue_description == "Full test"
        assert quiz_input.tried_already == "Tried multiple things"
        assert quiz_input.age_range == "30-40"
        assert quiz_input.severity_level == 7


class TestProductRecommendation:
    """Test ProductRecommendation data structure."""

    def test_product_recommendation_creation(self):
        """Test creating ProductRecommendation instance."""
        rec = ProductRecommendation(
            product_id="TEST-001",
            title="Test Product",
            description="Test description",
            category="immune_support",
            relevance_score=0.85,
            purchase_link="https://example.com/product/test",
            rationale="Recommended because...",
            ingredient_highlights=["Ingredient 1", "Ingredient 2"]
        )

        assert rec.product_id == "TEST-001"
        assert rec.relevance_score == 0.85
        assert len(rec.ingredient_highlights) == 2


class TestHealthQuizOutput:
    """Test HealthQuizOutput data structure."""

    def test_to_dict_conversion(self):
        """Test converting output to dictionary."""
        output = HealthQuizOutput(
            general_recommendations=["Advice 1", "Advice 2"],
            specific_products=[],
            educational_content=["Content 1"],
            lifestyle_suggestions=["Suggestion 1"],
            follow_up_questions=["Question 1"],
            primary_categories_addressed=["immune_support"],
            confidence_score=0.7,
            consultation_recommended=False
        )

        result = output.to_dict()

        assert isinstance(result, dict)
        assert result["confidence_score"] == 0.7
        assert result["consultation_recommended"] is False


class TestHealthQuizUseCase:
    """Test HealthQuizUseCase business logic."""

    @pytest.fixture
    def health_quiz_use_case(self, use_case_config):
        """Create HealthQuizUseCase instance for testing."""
        return HealthQuizUseCase(config=use_case_config)

    def test_get_use_case_name(self, health_quiz_use_case):
        """Test use case name is correct."""
        assert health_quiz_use_case.get_use_case_name() == "health_quiz"

    def test_validate_input_valid(self, health_quiz_use_case, sample_health_quiz_input):
        """Test validation passes for valid input."""
        is_valid, error = health_quiz_use_case.validate_input(sample_health_quiz_input.to_dict())

        assert is_valid is True
        assert error is None

    def test_validate_input_missing_description(self, health_quiz_use_case):
        """Test validation fails when description is missing."""
        input_data = {
            "health_issue_description": "",
            "primary_health_area": "immune_support"
        }

        is_valid, error = health_quiz_use_case.validate_input(input_data)

        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_input_description_too_short(self, health_quiz_use_case):
        """Test validation fails when description is too short."""
        input_data = {
            "health_issue_description": "Short",
            "primary_health_area": "immune_support"
        }

        is_valid, error = health_quiz_use_case.validate_input(input_data)

        assert is_valid is False
        assert "at least 10 characters" in error

    def test_validate_input_invalid_health_area(self, health_quiz_use_case):
        """Test validation fails for invalid health area."""
        input_data = {
            "health_issue_description": "Valid description here",
            "primary_health_area": "invalid_category_name"
        }

        is_valid, error = health_quiz_use_case.validate_input(input_data)

        assert is_valid is False
        assert "Invalid primary_health_area" in error

    def test_validate_input_severity_out_of_range(self, health_quiz_use_case):
        """Test validation fails for invalid severity level."""
        input_data = {
            "health_issue_description": "Valid description here",
            "severity_level": 15  # Out of 1-10 range
        }

        is_valid, error = health_quiz_use_case.validate_input(input_data)

        assert is_valid is False
        assert "between 1 and 10" in error

    def test_should_recommend_consultation_high_severity(self, health_quiz_use_case):
        """Test consultation recommended for high severity."""
        quiz_input = HealthQuizInput(
            health_issue_description="Severe pain",
            severity_level=8
        )

        should_consult = health_quiz_use_case._should_recommend_consultation(quiz_input)

        assert should_consult is True

    def test_should_recommend_consultation_low_severity(self, health_quiz_use_case):
        """Test consultation not recommended for low severity."""
        quiz_input = HealthQuizInput(
            health_issue_description="Mild discomfort",
            severity_level=3
        )

        should_consult = health_quiz_use_case._should_recommend_consultation(quiz_input)

        assert should_consult is False

    def test_should_recommend_consultation_concerning_keywords(self, health_quiz_use_case):
        """Test consultation recommended for concerning keywords."""
        quiz_input = HealthQuizInput(
            health_issue_description="I have severe chronic pain and my doctor said...",
            severity_level=5
        )

        should_consult = health_quiz_use_case._should_recommend_consultation(quiz_input)

        assert should_consult is True

    def test_calculate_confidence_score_minimal_info(self, health_quiz_use_case):
        """Test confidence score with minimal information."""
        quiz_input = HealthQuizInput(
            health_issue_description="Brief issue"
        )

        llm_recommendations = {}
        score = health_quiz_use_case._calculate_confidence_score(quiz_input, llm_recommendations)

        assert 0 <= score <= 1.0
        assert score < 0.8  # Should be lower with minimal info

    def test_calculate_confidence_score_complete_info(self, health_quiz_use_case):
        """Test confidence score with complete information."""
        quiz_input = HealthQuizInput(
            health_issue_description="Detailed description of health issue with many details about symptoms and timeline",
            primary_health_area="digestive_health",
            tried_already="Tried several approaches",
            severity_level=6
        )

        llm_recommendations = {}
        score = health_quiz_use_case._calculate_confidence_score(quiz_input, llm_recommendations)

        assert 0 <= score <= 1.0
        assert score > 0.5  # Should be higher with more info

    def test_extract_categories(self, health_quiz_use_case):
        """Test category extraction from input."""
        quiz_input = HealthQuizInput(
            health_issue_description="Test",
            primary_health_area="immune_support",
            secondary_health_area="stress_relief"
        )

        categories = health_quiz_use_case._extract_categories(quiz_input)

        assert "immune_support" in categories
        assert "stress_relief" in categories
        assert len(categories) == 2

    def test_extract_categories_primary_only(self, health_quiz_use_case):
        """Test category extraction with only primary area."""
        quiz_input = HealthQuizInput(
            health_issue_description="Test",
            primary_health_area="immune_support"
        )

        categories = health_quiz_use_case._extract_categories(quiz_input)

        assert "immune_support" in categories
        assert len(categories) == 1

    def test_load_health_categories(self, health_quiz_use_case):
        """Test health categories are loaded."""
        categories = health_quiz_use_case._load_health_categories()

        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "immune_support" in categories
        assert "digestive_health" in categories

    def test_generate_educational_content(self, health_quiz_use_case):
        """Test educational content generation."""
        quiz_input = HealthQuizInput(
            health_issue_description="Test",
            primary_health_area="immune_support"
        )

        content = health_quiz_use_case._generate_educational_content(quiz_input)

        assert isinstance(content, list)
        assert len(content) > 0

    def test_generate_llm_recommendations_no_client(self, health_quiz_use_case):
        """Test fallback recommendations when LLM client is not available."""
        # health_quiz_use_case has no llm_client by default
        quiz_input = HealthQuizInput(
            health_issue_description="Test issue",
            primary_health_area="immune_support"
        )

        recommendations = health_quiz_use_case._generate_llm_recommendations(quiz_input)

        assert isinstance(recommendations, dict)
        assert "general_advice" in recommendations
        assert isinstance(recommendations["general_advice"], list)
        assert len(recommendations["general_advice"]) > 0

    def test_get_prompt_template_basic(self, health_quiz_use_case):
        """Test prompt template generation with basic input."""
        quiz_input = HealthQuizInput(
            health_issue_description="I have digestive issues"
        )

        prompt = health_quiz_use_case.get_prompt_template(quiz_input.to_dict())

        assert isinstance(prompt, str)
        assert "digestive issues" in prompt
        assert "JSON" in prompt  # Should request JSON format

    def test_get_prompt_template_complete(self, health_quiz_use_case, sample_health_quiz_input):
        """Test prompt template with complete input."""
        prompt = health_quiz_use_case.get_prompt_template(sample_health_quiz_input.to_dict())

        assert sample_health_quiz_input.health_issue_description in prompt
        assert sample_health_quiz_input.tried_already in prompt
        assert sample_health_quiz_input.primary_health_area in prompt
        assert str(sample_health_quiz_input.severity_level) in prompt


@pytest.mark.parametrize("severity,expected_consultation", [
    (1, False),
    (3, False),
    (5, False),
    (7, False),  # Threshold is 8 (>= 8)
    (8, True),
    (9, True),
    (10, True),
])
def test_consultation_threshold_parametrized(severity, expected_consultation):
    """Parametrized test for consultation threshold logic."""
    from src.use_case_framework import UseCaseConfig, ProcessingMode
    config = UseCaseConfig(
        client_id="test_client",
        use_case_name="health_quiz",
        model_config="gpt4o_mini",
        processing_mode=ProcessingMode.REALTIME,
        custom_settings={"consultation_threshold": 8}
    )
    use_case = HealthQuizUseCase(config=config)

    quiz_input = HealthQuizInput(
        health_issue_description="Test issue with no concerning keywords",
        severity_level=severity
    )

    should_consult = use_case._should_recommend_consultation(quiz_input)

    assert should_consult == expected_consultation


@pytest.mark.parametrize("description,should_recommend", [
    ("I have mild bloating after meals", False),
    ("I have severe pain in my abdomen", True),
    ("My doctor recommended I see a specialist", True),
    ("I'm taking medication for this condition", True),
    ("Chronic headaches for weeks", True),
    ("Just feeling a bit tired lately", False),
])
def test_consultation_keywords_parametrized(description, should_recommend):
    """Parametrized test for consultation based on keywords."""
    from src.use_case_framework import UseCaseConfig, ProcessingMode
    config = UseCaseConfig(
        client_id="test_client",
        use_case_name="health_quiz",
        model_config="gpt4o_mini",
        processing_mode=ProcessingMode.REALTIME,
        custom_settings={"consultation_threshold": 10}  # High threshold so only keywords trigger
    )
    use_case = HealthQuizUseCase(config=config)

    quiz_input = HealthQuizInput(
        health_issue_description=description,
        severity_level=5  # Medium severity
    )

    should_consult = use_case._should_recommend_consultation(quiz_input)

    assert should_consult == should_recommend
