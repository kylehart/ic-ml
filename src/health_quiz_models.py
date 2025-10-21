"""
Shared data models for Health Quiz use case.

This module contains data structures shared between health_quiz_use_case.py
and product_recommendation_engine.py to avoid circular imports.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


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
