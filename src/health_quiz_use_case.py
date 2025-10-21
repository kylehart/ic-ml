"""
Health Quiz Use Case Implementation

Implements the health quiz use case where customers provide health concerns
and receive personalized recommendations including Rogue Herbalist products.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from use_case_framework import RealtimeUseCase, UseCaseResult, register_use_case
from product_recommendation_engine import ProductRecommendationEngine


@dataclass
class HealthQuizInput:
    """Input data structure for health quiz."""
    health_issue_description: str  # Free text description of health issue
    tried_already: Optional[str] = None  # What they've tried, outcomes
    primary_health_area: Optional[str] = None  # From 20 categories
    secondary_health_area: Optional[str] = None  # Optional second category

    # Optional fields for future expansion
    age_range: Optional[str] = None
    severity_level: Optional[int] = None  # 1-10 scale
    budget_preference: Optional[str] = None  # "low", "medium", "high"
    lifestyle_factors: Optional[str] = None  # Additional context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, filtering None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthQuizInput':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ProductRecommendation:
    """Individual product recommendation."""
    product_id: str
    title: str
    description: str
    category: str
    relevance_score: float  # 0.0 to 1.0
    purchase_link: str
    rationale: str  # Why it's recommended
    ingredient_highlights: List[str]  # Key beneficial ingredients


@dataclass
class HealthQuizOutput:
    """Output data structure for health quiz recommendations."""
    general_recommendations: List[str]  # LLM-generated health advice
    specific_products: List[ProductRecommendation]  # RH product recommendations
    educational_content: List[str]  # Health information and tips
    lifestyle_suggestions: List[str]  # Diet, exercise, lifestyle tips
    follow_up_questions: List[str]  # Questions to consider for next time

    # Metadata
    primary_categories_addressed: List[str]
    confidence_score: float  # Overall confidence in recommendations
    consultation_recommended: bool  # Whether to recommend professional consultation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return asdict(self)


@register_use_case("health_quiz")
class HealthQuizUseCase(RealtimeUseCase):
    """Health quiz use case implementation."""

    def __init__(self, config):
        super().__init__(config)
        self.taxonomy_categories = self._load_health_categories()
        self.product_catalog = self._load_product_catalog()

    def get_use_case_name(self) -> str:
        return "health_quiz"

    def validate_input(self, input_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate health quiz input data."""
        try:
            # Convert to structured input for validation
            quiz_input = HealthQuizInput.from_dict(input_data)

            # Check required fields
            if not quiz_input.health_issue_description:
                return False, "health_issue_description is required"

            if len(quiz_input.health_issue_description.strip()) < 10:
                return False, "health_issue_description must be at least 10 characters"

            # Validate health categories if provided
            if quiz_input.primary_health_area:
                if quiz_input.primary_health_area not in self.taxonomy_categories:
                    return False, f"Invalid primary_health_area: {quiz_input.primary_health_area}"

            if quiz_input.secondary_health_area:
                if quiz_input.secondary_health_area not in self.taxonomy_categories:
                    return False, f"Invalid secondary_health_area: {quiz_input.secondary_health_area}"

            # Validate severity level if provided
            if quiz_input.severity_level is not None:
                if not (1 <= quiz_input.severity_level <= 10):
                    return False, "severity_level must be between 1 and 10"

            return True, None

        except Exception as e:
            return False, f"Input validation error: {str(e)}"

    def process_request(self, input_data: Dict[str, Any]) -> UseCaseResult:
        """Process health quiz request."""
        start_time = datetime.now()

        try:
            # Parse input
            quiz_input = HealthQuizInput.from_dict(input_data)

            # Generate LLM-based recommendations
            llm_recommendations = self._generate_llm_recommendations(quiz_input)

            # Find relevant products
            product_recommendations = self._find_relevant_products(quiz_input, llm_recommendations)

            # Generate educational content
            educational_content = self._generate_educational_content(quiz_input)

            # Create structured output
            output = HealthQuizOutput(
                general_recommendations=llm_recommendations.get("general_advice", []),
                specific_products=product_recommendations,
                educational_content=educational_content,
                lifestyle_suggestions=llm_recommendations.get("lifestyle_suggestions", []),
                follow_up_questions=llm_recommendations.get("follow_up_questions", []),
                primary_categories_addressed=self._extract_categories(quiz_input),
                confidence_score=self._calculate_confidence_score(quiz_input, llm_recommendations),
                consultation_recommended=self._should_recommend_consultation(quiz_input)
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            return self.create_result(
                success=True,
                data=output.to_dict(),
                metadata={
                    "input_summary": {
                        "primary_area": quiz_input.primary_health_area,
                        "secondary_area": quiz_input.secondary_health_area,
                        "has_tried_something": bool(quiz_input.tried_already),
                    },
                    "recommendations_count": len(product_recommendations),
                    "model_used": self.config.model_config,
                },
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return self.create_result(
                success=False,
                data={},
                metadata={"error": str(e), "error_type": type(e).__name__},
                processing_time=processing_time
            )

    def get_prompt_template(self, context: Dict[str, Any]) -> str:
        """Get the LLM prompt template for health quiz."""
        quiz_input = HealthQuizInput.from_dict(context)

        template = f"""You are a knowledgeable herbalist and wellness advisor for Rogue Herbalist, a company specializing in high-quality herbal products.

A customer has provided the following information about their health concerns:

Health Issue: {quiz_input.health_issue_description}

"""

        if quiz_input.tried_already:
            template += f"What they've tried before: {quiz_input.tried_already}\n\n"

        if quiz_input.primary_health_area:
            template += f"Primary health focus: {quiz_input.primary_health_area}\n"

        if quiz_input.secondary_health_area:
            template += f"Secondary health focus: {quiz_input.secondary_health_area}\n"

        if quiz_input.age_range:
            template += f"Age range: {quiz_input.age_range}\n"

        if quiz_input.severity_level:
            template += f"Severity level (1-10): {quiz_input.severity_level}\n"

        template += f"""
Based on this information, please provide personalized recommendations in the following JSON format:

{{
    "general_advice": [
        "Evidence-based general health advice point 1",
        "Evidence-based general health advice point 2",
        "Evidence-based general health advice point 3"
    ],
    "herbal_categories": [
        "Category 1 of herbs that might be helpful",
        "Category 2 of herbs that might be helpful"
    ],
    "lifestyle_suggestions": [
        "Dietary suggestion 1",
        "Exercise/lifestyle suggestion 2",
        "Stress management suggestion 3"
    ],
    "follow_up_questions": [
        "Question to help them think deeper about their health",
        "Question about potential underlying causes"
    ],
    "consultation_needed": false,
    "reasoning": "Brief explanation of the recommendations"
}}

Guidelines:
- Provide evidence-based, safe recommendations
- Never diagnose or replace medical advice
- Suggest professional consultation for serious conditions
- Focus on herbal and natural approaches
- Be specific and actionable
- Consider what they've already tried to avoid repetition
"""

        return template

    def _generate_llm_recommendations(self, quiz_input: HealthQuizInput) -> Dict[str, Any]:
        """Generate recommendations using LLM."""
        if not self.llm_client:
            # Fallback recommendations for testing
            return {
                "general_advice": [
                    "Consider consulting with a healthcare professional",
                    "Focus on a balanced diet with plenty of vegetables",
                    "Ensure adequate sleep and stress management"
                ],
                "herbal_categories": ["adaptogenic herbs", "digestive herbs"],
                "lifestyle_suggestions": ["Stay hydrated", "Regular exercise"],
                "follow_up_questions": ["How long have you experienced this issue?"],
                "consultation_needed": False,
                "reasoning": "General wellness approach recommended"
            }

        prompt = self.get_prompt_template(quiz_input.to_dict())

        messages = [{"role": "user", "content": prompt}]

        try:
            response = self.llm_client.complete_sync(messages)
            # Parse JSON response
            return json.loads(response)
        except Exception as e:
            # Return fallback on error
            return {
                "general_advice": ["Consider consulting with a healthcare professional"],
                "herbal_categories": [],
                "lifestyle_suggestions": [],
                "follow_up_questions": [],
                "consultation_needed": True,
                "reasoning": f"Error generating recommendations: {str(e)}"
            }

    def _find_relevant_products(self,
                              quiz_input: HealthQuizInput,
                              llm_recommendations: Dict[str, Any]) -> List[ProductRecommendation]:
        """Find relevant products from catalog using ProductRecommendationEngine."""
        # Initialize the product recommendation engine
        # Use client_id from config, default to 'rogue_herbalist'
        client_id = getattr(self.config, 'client_id', 'rogue_herbalist')

        # Get max_recommendations from use case config
        max_recs = self.config.use_case_config.get('max_recommendations', 5) if hasattr(self.config, 'use_case_config') else 5
        min_threshold = self.config.use_case_config.get('min_relevance_score', 0.3) if hasattr(self.config, 'use_case_config') else 0.3

        engine = ProductRecommendationEngine(
            client_id=client_id,
            catalog_path=None,  # Uses default catalog path
            config=self.config.use_case_config if hasattr(self.config, 'use_case_config') else {}
        )

        # Get recommendations from engine
        return engine.recommend_products(
            quiz_input=quiz_input,
            llm_context=llm_recommendations,
            max_recommendations=max_recs,
            min_score_threshold=min_threshold
        )

    def _generate_educational_content(self, quiz_input: HealthQuizInput) -> List[str]:
        """Generate educational content based on health areas."""
        content = []

        if quiz_input.primary_health_area:
            content.append(f"Learn more about {quiz_input.primary_health_area} and natural approaches")

        # Add general wellness content
        content.extend([
            "The importance of a balanced diet rich in antioxidants",
            "How stress affects your overall health and immunity",
            "The role of sleep in healing and recovery"
        ])

        return content

    def _extract_categories(self, quiz_input: HealthQuizInput) -> List[str]:
        """Extract health categories being addressed."""
        categories = []
        if quiz_input.primary_health_area:
            categories.append(quiz_input.primary_health_area)
        if quiz_input.secondary_health_area:
            categories.append(quiz_input.secondary_health_area)
        return categories

    def _calculate_confidence_score(self,
                                  quiz_input: HealthQuizInput,
                                  llm_recommendations: Dict[str, Any]) -> float:
        """Calculate confidence score for recommendations."""
        score = 0.5  # Base score

        # Increase confidence with more information
        if quiz_input.primary_health_area:
            score += 0.2
        if quiz_input.tried_already:
            score += 0.1
        if quiz_input.severity_level:
            score += 0.1
        if len(quiz_input.health_issue_description) > 50:
            score += 0.1

        return min(score, 1.0)

    def _should_recommend_consultation(self, quiz_input: HealthQuizInput) -> bool:
        """Determine if professional consultation should be recommended."""
        # Recommend consultation for high severity or certain keywords
        if quiz_input.severity_level and quiz_input.severity_level >= 8:
            return True

        # Check for concerning keywords
        concerning_terms = ["pain", "severe", "chronic", "medication", "doctor"]
        description_lower = quiz_input.health_issue_description.lower()

        return any(term in description_lower for term in concerning_terms)

    def _load_health_categories(self) -> List[str]:
        """Load available health categories from taxonomy."""
        # This would load from the actual taxonomy file
        # For now, return a mock list
        return [
            "immune_support", "digestive_health", "stress_relief",
            "sleep_support", "joint_health", "cardiovascular_health",
            "respiratory_health", "skin_health", "cognitive_support",
            "energy_vitality", "women_health", "men_health",
            "detox_cleanse", "weight_management", "anti_aging",
            "inflammation", "mood_emotional", "liver_support",
            "kidney_health", "hormonal_balance"
        ]

    def _load_product_catalog(self) -> List[Dict[str, Any]]:
        """Load product catalog for recommendations."""
        # This would load from the actual catalog file
        # For now, return empty list
        return []