"""
Product Recommendation Engine

Intelligent product matching system that connects health quiz responses
to relevant Rogue Herbalist products using multiple recommendation strategies.
"""

import json
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re
from collections import defaultdict
import math

from health_quiz_use_case import ProductRecommendation, HealthQuizInput


@dataclass
class ProductCatalogItem:
    """Enhanced product data structure for recommendations."""
    id: str
    title: str
    description: str
    short_description: str = ""
    ingredients: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    subcategories: List[str] = field(default_factory=list)
    price: Optional[float] = None
    in_stock: bool = True
    rating: Optional[float] = None
    review_count: int = 0
    tags: List[str] = field(default_factory=list)
    contraindications: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    slug: str = ""


    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'ProductCatalogItem':
        """Create from CSV row with intelligent field mapping."""
        # Clean BOM and normalize field names
        clean_row = {k.strip('\ufeff').lower().replace(' ', '_'): v for k, v in row.items()}

        # Map various CSV formats
        id_field = clean_row.get('id') or clean_row.get('product_id') or clean_row.get('sku', '')
        title_field = clean_row.get('name') or clean_row.get('title') or clean_row.get('product_name', '')
        desc_field = clean_row.get('description') or clean_row.get('long_description', '')
        short_desc_field = clean_row.get('short_description') or clean_row.get('summary', '')
        slug_field = clean_row.get('slug', '')

        # Extract ingredients from description text (simple approach)
        combined_text = f"{desc_field} {short_desc_field}".lower()
        common_herbs = ['ginger', 'turmeric', 'ashwagandha', 'echinacea', 'elderberry', 'ginseng',
                       'chamomile', 'valerian', 'rhodiola', 'milk thistle', 'garlic', 'ginkgo',
                       'chaga', 'turkey tail', 'reishi', 'lobelia', 'mint', 'fern']
        ingredients = [herb for herb in common_herbs if herb in combined_text]

        # Extract categories from description (simple keyword matching)
        categories = []
        if any(word in combined_text for word in ['immune', 'immunity', 'defense']):
            categories.append('immune_support')
        if any(word in combined_text for word in ['digestive', 'stomach', 'gut', 'cough', 'syrup']):
            categories.append('digestive_health')
        if any(word in combined_text for word in ['stress', 'calm', 'adaptogen']):
            categories.append('stress_relief')

        return cls(
            id=id_field,
            title=title_field,
            description=desc_field,
            short_description=short_desc_field,
            ingredients=ingredients,
            categories=categories,
            price=None,  # Not available in this CSV
            in_stock=True,  # Assume in stock for now
            tags=[],
            slug=slug_field
        )


class CategoryMatcher:
    """Maps health categories to product categories."""

    def __init__(self):
        # Health category to product category mappings
        self.category_mappings = {
            "immune_support": ["immune", "immunity", "defense", "elderberry", "echinacea"],
            "digestive_health": ["digestive", "stomach", "gut", "digestion", "probiotics"],
            "stress_relief": ["stress", "anxiety", "calm", "relaxation", "adaptogen"],
            "sleep_support": ["sleep", "insomnia", "rest", "melatonin", "chamomile"],
            "joint_health": ["joint", "arthritis", "inflammation", "mobility", "turmeric"],
            "cardiovascular_health": ["heart", "cardiovascular", "circulation", "blood_pressure"],
            "respiratory_health": ["respiratory", "lungs", "breathing", "cough", "throat"],
            "skin_health": ["skin", "beauty", "complexion", "acne", "dermatology"],
            "cognitive_support": ["brain", "memory", "focus", "concentration", "cognitive"],
            "energy_vitality": ["energy", "vitality", "fatigue", "endurance", "stamina"],
            "women_health": ["women", "female", "menstrual", "hormonal", "menopause"],
            "men_health": ["men", "male", "prostate", "testosterone", "masculine"],
            "detox_cleanse": ["detox", "cleanse", "liver", "kidney", "purify"],
            "weight_management": ["weight", "metabolism", "diet", "fat", "slimming"],
            "anti_aging": ["anti-aging", "longevity", "antioxidant", "youth", "aging"],
            "inflammation": ["inflammation", "anti-inflammatory", "swelling", "pain"],
            "mood_emotional": ["mood", "emotional", "depression", "happiness", "well-being"],
            "liver_support": ["liver", "hepatic", "detox", "cleanse"],
            "kidney_health": ["kidney", "renal", "urinary", "bladder"],
            "hormonal_balance": ["hormonal", "hormone", "endocrine", "balance"]
        }

        # Ingredient to benefit mappings
        self.ingredient_benefits = {
            "turmeric": ["inflammation", "joint_health", "antioxidant"],
            "ginger": ["digestive_health", "nausea", "inflammation"],
            "echinacea": ["immune_support", "respiratory_health"],
            "elderberry": ["immune_support", "antioxidant"],
            "ashwagandha": ["stress_relief", "energy_vitality", "adaptogen"],
            "chamomile": ["sleep_support", "stress_relief", "digestive_health"],
            "ginseng": ["energy_vitality", "cognitive_support", "stress_relief"],
            "milk_thistle": ["liver_support", "detox_cleanse"],
            "valerian": ["sleep_support", "anxiety", "stress_relief"],
            "garlic": ["cardiovascular_health", "immune_support"],
            "ginkgo": ["cognitive_support", "circulation"],
            "rhodiola": ["stress_relief", "energy_vitality", "mood_emotional"]
        }

    def get_category_keywords(self, health_category: str) -> List[str]:
        """Get product keywords for a health category."""
        return self.category_mappings.get(health_category.lower(), [])

    def get_ingredient_benefits(self, ingredient: str) -> List[str]:
        """Get health benefits for an ingredient."""
        ingredient_lower = ingredient.lower().replace('_', ' ')
        for key, benefits in self.ingredient_benefits.items():
            # Normalize the key as well to handle underscore mismatches
            key_normalized = key.lower().replace('_', ' ')
            if key_normalized in ingredient_lower or ingredient_lower in key_normalized:
                return benefits
        return []


class ProductScoringEngine:
    """Calculates relevance scores for product recommendations."""

    def __init__(self, category_matcher: CategoryMatcher):
        self.category_matcher = category_matcher

    def calculate_relevance_score(self,
                                product: ProductCatalogItem,
                                quiz_input: HealthQuizInput,
                                llm_context: Dict[str, Any] = None) -> float:
        """Calculate relevance score for a product given quiz input."""
        score = 0.0
        max_score = 0.0

        # 1. Direct category matching (40% weight)
        category_score, category_max = self._score_category_match(product, quiz_input)
        score += category_score * 0.4
        max_score += category_max * 0.4

        # 2. Ingredient matching (30% weight)
        ingredient_score, ingredient_max = self._score_ingredient_match(product, quiz_input, llm_context)
        score += ingredient_score * 0.3
        max_score += ingredient_max * 0.3

        # 3. Text similarity (20% weight)
        text_score, text_max = self._score_text_similarity(product, quiz_input)
        score += text_score * 0.2
        max_score += text_max * 0.2

        # 4. Product quality factors (10% weight)
        quality_score, quality_max = self._score_quality_factors(product)
        score += quality_score * 0.1
        max_score += quality_max * 0.1

        # Normalize to 0-1 scale
        return score / max_score if max_score > 0 else 0.0

    def _score_category_match(self, product: ProductCatalogItem, quiz_input: HealthQuizInput) -> Tuple[float, float]:
        """Score based on health category matching."""
        score = 0.0
        max_score = 10.0

        categories_to_check = []
        if quiz_input.primary_health_area:
            categories_to_check.append((quiz_input.primary_health_area, 1.0))  # Full weight
        if quiz_input.secondary_health_area:
            categories_to_check.append((quiz_input.secondary_health_area, 0.7))  # Reduced weight

        for health_category, weight in categories_to_check:
            keywords = self.category_matcher.get_category_keywords(health_category)

            # Check product categories
            for product_category in product.categories:
                if any(keyword in product_category.lower() for keyword in keywords):
                    score += 5.0 * weight

            # Check product title and description
            combined_text = f"{product.title} {product.description}".lower()
            keyword_matches = sum(1 for keyword in keywords if keyword in combined_text)
            if keyword_matches > 0:
                score += min(3.0, keyword_matches) * weight

        return score, max_score

    def _score_ingredient_match(self,
                              product: ProductCatalogItem,
                              quiz_input: HealthQuizInput,
                              llm_context: Dict[str, Any] = None) -> Tuple[float, float]:
        """Score based on ingredient matching with health benefits."""
        score = 0.0
        max_score = 10.0

        # Get relevant herb categories from LLM context
        llm_herbs = []
        if llm_context and "herbal_categories" in llm_context:
            llm_herbs = llm_context["herbal_categories"]

        # Score each ingredient
        for ingredient in product.ingredients:
            benefits = self.category_matcher.get_ingredient_benefits(ingredient)

            # Check against health areas
            if quiz_input.primary_health_area and quiz_input.primary_health_area in benefits:
                score += 3.0
            if quiz_input.secondary_health_area and quiz_input.secondary_health_area in benefits:
                score += 2.0

            # Check against LLM herb recommendations
            for herb_category in llm_herbs:
                if herb_category.lower() in ingredient.lower():
                    score += 2.0

        return min(score, max_score), max_score

    def _score_text_similarity(self, product: ProductCatalogItem, quiz_input: HealthQuizInput) -> Tuple[float, float]:
        """Score based on text similarity with health issue description."""
        score = 0.0
        max_score = 10.0

        # Extract key terms from health issue description
        issue_words = self._extract_key_terms(quiz_input.health_issue_description)

        # Check against product text
        product_text = f"{product.title} {product.description} {' '.join(product.tags)}".lower()

        # Calculate word overlap
        matches = sum(1 for word in issue_words if word in product_text)
        if len(issue_words) > 0:
            overlap_ratio = matches / len(issue_words)
            score = overlap_ratio * max_score

        return score, max_score

    def _score_quality_factors(self, product: ProductCatalogItem) -> Tuple[float, float]:
        """Score based on product quality indicators."""
        score = 0.0
        max_score = 10.0

        # In stock bonus
        if product.in_stock:
            score += 3.0

        # Rating bonus
        if product.rating:
            score += (product.rating / 5.0) * 4.0

        # Review count bonus (logarithmic)
        if product.review_count > 0:
            score += min(3.0, math.log10(product.review_count))

        return score, max_score

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text for similarity matching."""
        # Simple keyword extraction (in production, use more sophisticated NLP)
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        return [word for word in words if len(word) > 3 and word not in stop_words]


class ProductRecommendationEngine:
    """Main recommendation engine that orchestrates product matching."""

    def __init__(self, client_id: str, catalog_path: Optional[Path] = None, config: Dict[str, Any] = None):
        self.client_id = client_id
        self.config = config or {}
        self.catalog = self._load_catalog(catalog_path)
        self.category_matcher = CategoryMatcher()
        self.scoring_engine = ProductScoringEngine(self.category_matcher)

    def recommend_products(self,
                          quiz_input: HealthQuizInput,
                          llm_context: Dict[str, Any] = None,
                          max_recommendations: int = 5,
                          min_score_threshold: float = 0.3) -> List[ProductRecommendation]:
        """Generate product recommendations based on quiz input."""

        recommendations = []

        # Score all products
        for product in self.catalog:
            # Skip out-of-stock products
            if not product.in_stock:
                continue

            # Calculate relevance score
            score = self.scoring_engine.calculate_relevance_score(
                product, quiz_input, llm_context
            )

            # Apply minimum threshold
            if score < min_score_threshold:
                continue

            # Create recommendation
            recommendation = ProductRecommendation(
                product_id=product.id,
                title=product.title,
                description=product.description,
                category=product.categories[0] if product.categories else "general",
                relevance_score=score,
                purchase_link=self._generate_purchase_link(product),
                rationale=self._generate_rationale(product, quiz_input, score),
                ingredient_highlights=self._get_key_ingredients(product, quiz_input)
            )

            recommendations.append(recommendation)

        # Sort by relevance score and return top recommendations
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        return recommendations[:max_recommendations]

    def _load_catalog(self, catalog_path: Optional[Path]) -> List[ProductCatalogItem]:
        """Load product catalog from CSV file."""
        if catalog_path is None:
            # Default path based on client
            catalog_path = Path(f"data/{self.client_id}/minimal-product-catalog.csv")

        if not catalog_path.exists():
            # Return empty catalog if file doesn't exist
            return []

        catalog = []
        try:
            with open(catalog_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        product = ProductCatalogItem.from_csv_row(row)
                        catalog.append(product)
                    except Exception as e:
                        print(f"Error parsing product row: {e}")
                        continue
        except Exception as e:
            print(f"Error loading catalog: {e}")

        return catalog

    def _generate_purchase_link(self, product: ProductCatalogItem) -> str:
        """Generate purchase link for a product using configuration."""
        url_template = self.config.get('product_url_template', 'https://rogueherbalist.com/product/{product_slug}/')

        # Handle different URL template formats
        if '{product_slug}' in url_template:
            # Use slug from WooCommerce export (stored in CSV)
            slug = product.slug
            if not slug:
                raise ValueError(f"Product {product.id} ({product.title}) has no slug. Ensure WooCommerce export includes slug field.")
            return url_template.format(product_slug=slug)
        elif '{product_name}' in url_template:
            return url_template.format(product_name=product.title)
        elif '{product_id}' in url_template:
            return url_template.format(product_id=product.id)
        else:
            # Static URL (like shop page)
            return url_template

    def _generate_rationale(self,
                          product: ProductCatalogItem,
                          quiz_input: HealthQuizInput,
                          score: float) -> str:
        """Generate explanation for why product is recommended."""
        rationale_parts = []

        # Category match rationale
        if quiz_input.primary_health_area:
            keywords = self.category_matcher.get_category_keywords(quiz_input.primary_health_area)
            if any(keyword in product.title.lower() or keyword in product.description.lower()
                   for keyword in keywords):
                rationale_parts.append(f"Specifically formulated for {quiz_input.primary_health_area}")

        # Ingredient rationale
        beneficial_ingredients = []
        for ingredient in product.ingredients:
            benefits = self.category_matcher.get_ingredient_benefits(ingredient)
            if benefits:
                beneficial_ingredients.append(ingredient)

        if beneficial_ingredients:
            rationale_parts.append(f"Contains beneficial ingredients: {', '.join(beneficial_ingredients[:3])}")

        # Quality rationale
        if product.rating and product.rating >= 4.0:
            rationale_parts.append(f"Highly rated product ({product.rating}/5.0)")

        # Default rationale
        if not rationale_parts:
            rationale_parts.append("Selected based on ingredient profile and category matching")

        return ". ".join(rationale_parts)

    def _get_key_ingredients(self,
                           product: ProductCatalogItem,
                           quiz_input: HealthQuizInput) -> List[str]:
        """Get key ingredients relevant to the health quiz."""
        key_ingredients = []

        for ingredient in product.ingredients:
            benefits = self.category_matcher.get_ingredient_benefits(ingredient)
            if benefits:
                # Check if ingredient benefits match health areas
                if (quiz_input.primary_health_area and quiz_input.primary_health_area in benefits) or \
                   (quiz_input.secondary_health_area and quiz_input.secondary_health_area in benefits):
                    key_ingredients.append(ingredient)

        # Return top 3 most relevant ingredients
        return key_ingredients[:3]

    def get_catalog_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded catalog."""
        return {
            "total_products": len(self.catalog),
            "in_stock_products": sum(1 for p in self.catalog if p.in_stock),
            "categories": list(set(cat for p in self.catalog for cat in p.categories)),
            "avg_ingredients_per_product": sum(len(p.ingredients) for p in self.catalog) / len(self.catalog) if self.catalog else 0
        }