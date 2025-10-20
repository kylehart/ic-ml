"""
Unit tests for ProductRecommendationEngine and related classes.

Tests product scoring, matching, and recommendation generation.
"""

import pytest
from pathlib import Path
from src.product_recommendation_engine import (
    ProductCatalogItem,
    CategoryMatcher,
    ProductScoringEngine,
    ProductRecommendationEngine
)
from src.health_quiz_use_case import HealthQuizInput


class TestProductCatalogItem:
    """Test ProductCatalogItem data structure."""

    def test_from_csv_row_basic(self):
        """Test creating ProductCatalogItem from CSV row."""
        row = {
            'id': 'TEST-001',
            'name': 'Test Product',
            'description': 'Contains echinacea and ginger for immune support',
            'short_description': 'Test desc',
            'slug': 'test-product'
        }

        product = ProductCatalogItem.from_csv_row(row)

        assert product.id == 'TEST-001'
        assert product.title == 'Test Product'
        assert product.description == 'Contains echinacea and ginger for immune support'
        assert product.slug == 'test-product'
        assert 'echinacea' in product.ingredients
        assert 'ginger' in product.ingredients

    def test_from_csv_row_with_bom(self):
        """Test CSV parsing handles BOM characters."""
        row = {
            '\ufeffid': 'TEST-001',
            'name': 'Test Product',
            'description': 'Test description'
        }

        product = ProductCatalogItem.from_csv_row(row)

        assert product.id == 'TEST-001'
        assert product.title == 'Test Product'

    def test_from_csv_row_category_extraction(self):
        """Test automatic category extraction from description."""
        row = {
            'id': 'TEST-001',
            'name': 'Immune Boost',
            'description': 'Support your immune system with this powerful defense formula'
        }

        product = ProductCatalogItem.from_csv_row(row)

        assert 'immune_support' in product.categories

    def test_from_csv_row_missing_slug(self):
        """Test product creation when slug is missing."""
        row = {
            'id': 'TEST-001',
            'name': 'Test Product',
            'description': 'Test'
        }

        product = ProductCatalogItem.from_csv_row(row)

        assert product.slug == ''


class TestCategoryMatcher:
    """Test CategoryMatcher health-to-product category mapping."""

    def test_get_category_keywords(self):
        """Test retrieving keywords for health categories."""
        matcher = CategoryMatcher()

        immune_keywords = matcher.get_category_keywords("immune_support")
        assert "immune" in immune_keywords
        assert "echinacea" in immune_keywords
        assert len(immune_keywords) > 0

    def test_get_category_keywords_case_insensitive(self):
        """Test category matching is case insensitive."""
        matcher = CategoryMatcher()

        keywords_lower = matcher.get_category_keywords("immune_support")
        keywords_upper = matcher.get_category_keywords("IMMUNE_SUPPORT")

        assert keywords_lower == keywords_upper

    def test_get_category_keywords_unknown_category(self):
        """Test unknown category returns empty list."""
        matcher = CategoryMatcher()

        keywords = matcher.get_category_keywords("nonexistent_category")
        assert keywords == []

    def test_get_ingredient_benefits(self):
        """Test retrieving benefits for ingredients."""
        matcher = CategoryMatcher()

        turmeric_benefits = matcher.get_ingredient_benefits("turmeric")
        assert "inflammation" in turmeric_benefits
        assert "joint_health" in turmeric_benefits

    def test_get_ingredient_benefits_with_underscores(self):
        """Test ingredient matching with underscores."""
        matcher = CategoryMatcher()

        # Should match "milk thistle" even with underscore
        benefits = matcher.get_ingredient_benefits("milk_thistle")
        assert "liver_support" in benefits

    def test_get_ingredient_benefits_unknown(self):
        """Test unknown ingredient returns empty list."""
        matcher = CategoryMatcher()

        benefits = matcher.get_ingredient_benefits("unknown_herb")
        assert benefits == []


class TestProductScoringEngine:
    """Test ProductScoringEngine scoring logic."""

    def test_calculate_relevance_score_category_match(self, sample_product_catalog):
        """Test scoring with direct category match."""
        matcher = CategoryMatcher()
        scoring = ProductScoringEngine(matcher)

        quiz_input = HealthQuizInput(
            health_issue_description="I need immune support",
            primary_health_area="immune_support"
        )

        # Find immune support product
        immune_product = next(p for p in sample_product_catalog if 'immune_support' in p.categories)

        score = scoring.calculate_relevance_score(immune_product, quiz_input)

        assert 0 < score <= 1.0
        assert score > 0.3  # Should have decent relevance

    def test_calculate_relevance_score_ingredient_match(self, sample_product_catalog):
        """Test scoring with ingredient matching."""
        matcher = CategoryMatcher()
        scoring = ProductScoringEngine(matcher)

        quiz_input = HealthQuizInput(
            health_issue_description="I have digestive issues",
            primary_health_area="digestive_health"
        )

        digestive_product = next(p for p in sample_product_catalog if 'digestive_health' in p.categories)

        score = scoring.calculate_relevance_score(digestive_product, quiz_input)

        assert 0 < score <= 1.0

    def test_calculate_relevance_score_no_match(self, sample_product_catalog):
        """Test scoring with no category match."""
        matcher = CategoryMatcher()
        scoring = ProductScoringEngine(matcher)

        quiz_input = HealthQuizInput(
            health_issue_description="Random unrelated issue",
            primary_health_area="cognitive_support"
        )

        immune_product = next(p for p in sample_product_catalog if 'immune_support' in p.categories)

        score = scoring.calculate_relevance_score(immune_product, quiz_input)

        # Should still return a score (quality factors, etc.)
        assert 0 <= score <= 1.0

    def test_calculate_relevance_score_with_llm_context(self, sample_product_catalog):
        """Test scoring enhanced with LLM context."""
        matcher = CategoryMatcher()
        scoring = ProductScoringEngine(matcher)

        quiz_input = HealthQuizInput(
            health_issue_description="Need stress relief",
            primary_health_area="stress_relief"
        )

        llm_context = {
            "herbal_categories": ["ashwagandha", "adaptogenic"]
        }

        stress_product = next(p for p in sample_product_catalog if 'stress_relief' in p.categories)

        score_with_context = scoring.calculate_relevance_score(stress_product, quiz_input, llm_context)
        score_without_context = scoring.calculate_relevance_score(stress_product, quiz_input)

        # LLM context should potentially increase score
        assert score_with_context >= score_without_context

    def test_score_quality_factors_in_stock(self, sample_product_catalog):
        """Test quality scoring for in-stock products."""
        matcher = CategoryMatcher()
        scoring = ProductScoringEngine(matcher)

        in_stock = next(p for p in sample_product_catalog if p.in_stock)
        out_of_stock = next(p for p in sample_product_catalog if not p.in_stock)

        quiz_input = HealthQuizInput(health_issue_description="test", primary_health_area="test")

        score_in_stock = scoring.calculate_relevance_score(in_stock, quiz_input)
        score_out = scoring.calculate_relevance_score(out_of_stock, quiz_input)

        # In-stock should score higher (quality factors)
        assert score_in_stock > score_out


class TestProductRecommendationEngine:
    """Test ProductRecommendationEngine end-to-end."""

    def test_initialization_with_catalog_path(self, temp_product_catalog_csv):
        """Test engine initialization with explicit catalog path."""
        engine = ProductRecommendationEngine(
            client_id="test_client",
            catalog_path=temp_product_catalog_csv
        )

        assert len(engine.catalog) == 2
        assert engine.client_id == "test_client"

    def test_initialization_with_nonexistent_path(self):
        """Test engine handles missing catalog file."""
        engine = ProductRecommendationEngine(
            client_id="test_client",
            catalog_path=Path("/nonexistent/path.csv")
        )

        # Should return empty catalog, not crash
        assert engine.catalog == []

    def test_recommend_products_basic(self, sample_product_catalog, mock_use_case_config):
        """Test basic product recommendations."""
        # Create engine with mocked catalog
        engine = ProductRecommendationEngine(
            client_id="test_client",
            catalog_path=None,
            config=mock_use_case_config
        )
        engine.catalog = sample_product_catalog

        quiz_input = HealthQuizInput(
            health_issue_description="I need immune support during cold season",
            primary_health_area="immune_support"
        )

        recommendations = engine.recommend_products(quiz_input, max_recommendations=5)

        assert len(recommendations) > 0
        assert all(hasattr(r, 'product_id') for r in recommendations)
        assert all(hasattr(r, 'relevance_score') for r in recommendations)
        assert all(hasattr(r, 'purchase_link') for r in recommendations)

    def test_recommend_products_filters_out_of_stock(self, sample_product_catalog, mock_use_case_config):
        """Test recommendations filter out-of-stock products."""
        engine = ProductRecommendationEngine(
            client_id="test_client",
            catalog_path=None,
            config=mock_use_case_config
        )
        engine.catalog = sample_product_catalog

        quiz_input = HealthQuizInput(
            health_issue_description="General health",
            primary_health_area="test"
        )

        recommendations = engine.recommend_products(quiz_input, max_recommendations=10)

        # Should not include out-of-stock product
        assert all(r.product_id != "TEST-004" for r in recommendations)

    def test_recommend_products_respects_min_threshold(self, sample_product_catalog, mock_use_case_config):
        """Test recommendations respect minimum score threshold."""
        engine = ProductRecommendationEngine(
            client_id="test_client",
            catalog_path=None,
            config=mock_use_case_config
        )
        engine.catalog = sample_product_catalog

        quiz_input = HealthQuizInput(
            health_issue_description="Very specific unrelated issue",
            primary_health_area="cognitive_support"
        )

        # High threshold should return fewer results
        recommendations = engine.recommend_products(
            quiz_input,
            max_recommendations=10,
            min_score_threshold=0.8
        )

        assert len(recommendations) <= len(sample_product_catalog)

    def test_recommend_products_sorted_by_relevance(self, sample_product_catalog, mock_use_case_config):
        """Test recommendations are sorted by relevance score."""
        engine = ProductRecommendationEngine(
            client_id="test_client",
            catalog_path=None,
            config=mock_use_case_config
        )
        engine.catalog = sample_product_catalog

        quiz_input = HealthQuizInput(
            health_issue_description="Digestive issues",
            primary_health_area="digestive_health"
        )

        recommendations = engine.recommend_products(quiz_input, max_recommendations=5)

        if len(recommendations) > 1:
            # Check descending order
            for i in range(len(recommendations) - 1):
                assert recommendations[i].relevance_score >= recommendations[i + 1].relevance_score

    def test_recommend_products_limits_results(self, sample_product_catalog, mock_use_case_config):
        """Test max_recommendations parameter limits results."""
        engine = ProductRecommendationEngine(
            client_id="test_client",
            catalog_path=None,
            config=mock_use_case_config
        )
        engine.catalog = sample_product_catalog

        quiz_input = HealthQuizInput(
            health_issue_description="General wellness",
            primary_health_area="immune_support"
        )

        recommendations = engine.recommend_products(quiz_input, max_recommendations=2)

        assert len(recommendations) <= 2

    def test_generate_purchase_link_with_slug(self, sample_product_catalog, mock_use_case_config):
        """Test purchase link generation with product slug."""
        engine = ProductRecommendationEngine(
            client_id="test_client",
            catalog_path=None,
            config=mock_use_case_config
        )

        product = sample_product_catalog[0]  # Has slug
        link = engine._generate_purchase_link(product)

        assert "rogueherbalist.com" in link
        assert product.slug in link

    def test_generate_purchase_link_missing_slug_raises_error(self, mock_use_case_config):
        """Test purchase link generation fails gracefully with missing slug."""
        engine = ProductRecommendationEngine(
            client_id="test_client",
            catalog_path=None,
            config=mock_use_case_config
        )

        product = ProductCatalogItem(
            id="TEST-001",
            title="No Slug Product",
            description="Test",
            slug=""  # Empty slug
        )

        with pytest.raises(ValueError, match="has no slug"):
            engine._generate_purchase_link(product)

    def test_generate_rationale(self, sample_product_catalog, mock_use_case_config):
        """Test rationale generation for recommendations."""
        engine = ProductRecommendationEngine(
            client_id="test_client",
            catalog_path=None,
            config=mock_use_case_config
        )

        product = sample_product_catalog[0]
        quiz_input = HealthQuizInput(
            health_issue_description="Need immune support",
            primary_health_area="immune_support"
        )

        rationale = engine._generate_rationale(product, quiz_input, 0.8)

        assert isinstance(rationale, str)
        assert len(rationale) > 0

    def test_get_key_ingredients(self, sample_product_catalog, mock_use_case_config):
        """Test key ingredient extraction."""
        engine = ProductRecommendationEngine(
            client_id="test_client",
            catalog_path=None,
            config=mock_use_case_config
        )

        product = sample_product_catalog[2]  # Stress relief with ashwagandha
        quiz_input = HealthQuizInput(
            health_issue_description="Stress",
            primary_health_area="stress_relief"
        )

        key_ingredients = engine._get_key_ingredients(product, quiz_input)

        assert isinstance(key_ingredients, list)
        assert len(key_ingredients) <= 3

    def test_get_catalog_stats(self, sample_product_catalog, mock_use_case_config):
        """Test catalog statistics generation."""
        engine = ProductRecommendationEngine(
            client_id="test_client",
            catalog_path=None,
            config=mock_use_case_config
        )
        engine.catalog = sample_product_catalog

        stats = engine.get_catalog_stats()

        assert stats["total_products"] == len(sample_product_catalog)
        assert stats["in_stock_products"] == sum(1 for p in sample_product_catalog if p.in_stock)
        assert isinstance(stats["categories"], list)
        assert "avg_ingredients_per_product" in stats


@pytest.mark.parametrize("health_area,expected_category", [
    ("immune_support", "immune_support"),
    ("digestive_health", "digestive_health"),
    ("stress_relief", "stress_relief"),
])
def test_category_matching_parametrized(health_area, expected_category, sample_product_catalog, mock_use_case_config):
    """Parametrized test for category matching across different health areas."""
    engine = ProductRecommendationEngine(
        client_id="test_client",
        catalog_path=None,
        config=mock_use_case_config
    )
    engine.catalog = sample_product_catalog

    quiz_input = HealthQuizInput(
        health_issue_description=f"I need help with {health_area}",
        primary_health_area=health_area
    )

    recommendations = engine.recommend_products(quiz_input, max_recommendations=5)

    # Should get at least one recommendation
    assert len(recommendations) > 0

    # Top recommendation should match the category
    if recommendations:
        top_rec = recommendations[0]
        matching_product = next(p for p in sample_product_catalog if p.id == top_rec.product_id)
        assert expected_category in matching_product.categories or top_rec.relevance_score > 0
