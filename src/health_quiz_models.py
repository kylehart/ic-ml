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
    primary_health_areas: Optional[List[str]] = None  # Multiple choice: list of categories (Formbricks multiselect)

    # Deprecated fields (kept for backward compatibility)
    primary_health_area: Optional[str] = None  # Single category (legacy)
    secondary_health_area: Optional[str] = None  # Removed from form, kept for old data

    # Optional fields for future expansion
    age_range: Optional[str] = None
    severity_level: Optional[int] = None  # 1-10 scale
    budget_preference: Optional[str] = None  # "low", "medium", "high"
    lifestyle_factors: Optional[str] = None  # Additional context

    # UTM tracking for marketing attribution
    utm_medium: Optional[str] = None  # "email" or "web" for attribution tracking

    def __post_init__(self):
        """Normalize primary_health_areas to always be a list."""
        # If primary_health_areas is not set but primary_health_area is (legacy single choice)
        if not self.primary_health_areas and self.primary_health_area:
            self.primary_health_areas = [self.primary_health_area]

        # If secondary_health_area is set (legacy), add it to primary_health_areas
        if self.secondary_health_area and self.secondary_health_area not in (self.primary_health_areas or []):
            if not self.primary_health_areas:
                self.primary_health_areas = []
            self.primary_health_areas.append(self.secondary_health_area)

        # Ensure primary_health_areas is always a list (even if empty)
        if self.primary_health_areas is None:
            self.primary_health_areas = []

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
