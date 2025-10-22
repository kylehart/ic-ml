#!/usr/bin/env python3
"""
Experimental runner for Health Quiz use case.
Implements complete run management with artifact capture for health quiz recommendations.
"""

import argparse
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Try to import markdown package for HTML conversion
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_client import LLMClient
from health_quiz_models import HealthQuizInput, HealthQuizOutput
from product_recommendation_engine import ProductRecommendationEngine
from model_config import get_config_manager


def verify_recommendations(persona_name: str,
                           actual_products: List[Dict[str, Any]],
                           expected: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Verify product recommendations match expectations.

    Args:
        persona_name: Name of the persona being tested
        actual_products: List of actual product recommendations
        expected: Expected recommendations dict from persona config

    Returns:
        Verification results dict or None if no expectations defined
    """
    if not expected:
        return None

    actual_slugs = [p.get('purchase_link', '').split('/')[-2] if p.get('purchase_link') else ''
                    for p in actual_products]

    results = {
        "persona": persona_name,
        "passed": True,
        "failures": [],
        "warnings": [],
        "checks": {}
    }

    # Check must_include_slugs
    must_include = expected.get("must_include_slugs", [])
    if must_include:
        found_slugs = []
        missing_slugs = []
        for slug in must_include:
            if slug in actual_slugs:
                position = actual_slugs.index(slug) + 1
                found_slugs.append((slug, position))
            else:
                missing_slugs.append(slug)
                results["passed"] = False
                results["failures"].append(f"Missing required product: {slug}")

        results["checks"]["must_include"] = {
            "required": len(must_include),
            "found": len(found_slugs),
            "found_products": found_slugs,
            "missing_products": missing_slugs
        }

    # Check min_product_count
    min_count = expected.get("min_product_count", 0)
    if min_count:
        if len(actual_products) < min_count:
            results["passed"] = False
            results["failures"].append(
                f"Only {len(actual_products)} products, expected at least {min_count}"
            )
        results["checks"]["product_count"] = {
            "expected_min": min_count,
            "actual": len(actual_products),
            "passed": len(actual_products) >= min_count
        }

    # Check min_relevance_score
    min_relevance = expected.get("min_relevance_score", 0)
    if min_relevance and actual_products:
        top_score = max([p.get('relevance_score', 0) for p in actual_products])
        if top_score < min_relevance:
            results["passed"] = False
            results["failures"].append(
                f"Top relevance score {top_score:.2f} below minimum {min_relevance:.2f}"
            )
        results["checks"]["relevance_score"] = {
            "expected_min": min_relevance,
            "top_score": top_score,
            "passed": top_score >= min_relevance
        }

    # Check should_include_slugs (warnings, not failures)
    should_include = expected.get("should_include_slugs", [])
    if should_include:
        found_optional = []
        missing_optional = []
        for slug in should_include:
            if slug in actual_slugs:
                position = actual_slugs.index(slug) + 1
                found_optional.append((slug, position))
            else:
                missing_optional.append(slug)
                results["warnings"].append(f"Expected product not found: {slug}")

        results["checks"]["should_include"] = {
            "expected": len(should_include),
            "found": len(found_optional),
            "found_products": found_optional,
            "missing_products": missing_optional
        }

    # Check primary_categories
    primary_categories = expected.get("primary_categories", [])
    if primary_categories and actual_products:
        product_categories = [p.get('category', '') for p in actual_products]
        matching_categories = [cat for cat in primary_categories if cat in product_categories]
        if not matching_categories:
            results["warnings"].append(
                f"No products from expected categories: {', '.join(primary_categories)}"
            )
        results["checks"]["categories"] = {
            "expected": primary_categories,
            "found": list(set(product_categories)),
            "matching": matching_categories
        }

    return results


class HealthQuizRunner:
    """Manages experimental health quiz runs with complete artifact capture."""

    def __init__(self, use_case: str = "health-quiz"):
        self.use_case = use_case
        self.start_time = datetime.now()
        self.run_id = f"{use_case}-{self.start_time.strftime('%Y-%m-%d-%H%M%S')}"
        self.run_dir = Path("runs") / self.run_id

        # Create run directory structure
        self.setup_run_directory()

    def setup_run_directory(self):
        """Create standardized run directory structure."""
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.run_dir / "inputs").mkdir(exist_ok=True)
        (self.run_dir / "config").mkdir(exist_ok=True)
        (self.run_dir / "outputs").mkdir(exist_ok=True)
        (self.run_dir / "metadata").mkdir(exist_ok=True)

        print(f"📁 Run directory created: {self.run_dir}")

    def snapshot_inputs(self, quiz_input: HealthQuizInput, persona_name: str = None, expected_recommendations: Optional[Dict[str, Any]] = None):
        """Snapshot quiz input data."""
        input_data = {
            "persona_name": persona_name,
            "quiz_input": quiz_input.to_dict(),
            "timestamp": self.start_time.isoformat()
        }

        # Add expected recommendations if present
        if expected_recommendations:
            input_data["expected_recommendations"] = expected_recommendations

        with open(self.run_dir / "inputs" / "quiz_input.json", "w") as f:
            json.dump(input_data, f, indent=2)

        # Copy taxonomy for reference
        taxonomy_path = Path("data/rogue-herbalist/taxonomy_trimmed.xml")
        if taxonomy_path.exists():
            shutil.copy2(taxonomy_path, self.run_dir / "inputs" / "taxonomy.xml")

        print(f"📥 Inputs snapshotted: {persona_name or 'Anonymous User'}")

    def snapshot_config(self, model_override: Optional[str] = None):
        """Snapshot configuration."""
        # Copy models.yaml
        models_config_path = Path("config") / "models.yaml"
        if models_config_path.exists():
            shutil.copy2(models_config_path, self.run_dir / "config" / "models.yaml")

        # Save run configuration
        run_config = {
            "model_override": model_override,
            "use_case": self.use_case,
            "start_time": self.start_time.isoformat(),
            "run_id": self.run_id
        }

        with open(self.run_dir / "config" / "run_config.json", "w") as f:
            json.dump(run_config, f, indent=2)

        print(f"⚙️  Configuration snapshotted")

    def save_outputs(self,
                    quiz_output: Dict[str, Any],
                    llm_response: Dict[str, Any],
                    product_recommendations: List[Dict[str, Any]],
                    token_usage: Dict[str, Any],
                    timing_info: Dict[str, Any],
                    client_cost_data: Optional[Dict[str, Any]] = None,
                    errors: List[str] = None):
        """Save all outputs from health quiz run."""

        # Save main quiz output
        with open(self.run_dir / "outputs" / "quiz_recommendations.json", "w") as f:
            json.dump(quiz_output, f, indent=2)

        # Save LLM response
        with open(self.run_dir / "outputs" / "llm_response.json", "w") as f:
            json.dump(llm_response, f, indent=2)

        # Save product recommendations
        with open(self.run_dir / "outputs" / "product_recommendations.json", "w") as f:
            json.dump(product_recommendations, f, indent=2)

        # Save token usage
        with open(self.run_dir / "outputs" / "token_usage.json", "w") as f:
            json.dump(token_usage, f, indent=2)

        # Save timing info
        with open(self.run_dir / "outputs" / "timing.json", "w") as f:
            json.dump(timing_info, f, indent=2)

        # Save client cost data
        if client_cost_data:
            with open(self.run_dir / "outputs" / "client_cost_breakdown.json", "w") as f:
                json.dump(client_cost_data, f, indent=2)

        # Save errors if any
        if errors:
            with open(self.run_dir / "outputs" / "errors.log", "w") as f:
                for error in errors:
                    f.write(f"{error}\n")

        # Load quiz_input from inputs directory for report generation
        quiz_input_data = {}
        try:
            with open(self.run_dir / "inputs" / "quiz_input.json", "r") as f:
                quiz_input_data = json.load(f)
        except:
            pass

        # Run verification if expected recommendations are provided
        verification_results = None
        if quiz_input_data.get("expected_recommendations"):
            persona_name = quiz_input_data.get("persona_name", "Unknown")
            verification_results = verify_recommendations(
                persona_name=persona_name,
                actual_products=product_recommendations,
                expected=quiz_input_data["expected_recommendations"]
            )

            # Save verification results
            if verification_results:
                with open(self.run_dir / "outputs" / "verification_results.json", "w") as f:
                    json.dump(verification_results, f, indent=2)

                # Print verification status
                status = "✅ PASSED" if verification_results["passed"] else "❌ FAILED"
                print(f"🔍 Verification: {status}")
                if verification_results["failures"]:
                    for failure in verification_results["failures"]:
                        print(f"   ❌ {failure}")
                if verification_results["warnings"]:
                    for warning in verification_results["warnings"]:
                        print(f"   ⚠️  {warning}")

        # Generate markdown report
        self.generate_markdown_report(quiz_input_data, quiz_output, llm_response, product_recommendations, timing_info, verification_results)

        print(f"📤 Outputs saved")

    def generate_markdown_report(self,
                                quiz_input: Dict[str, Any],
                                quiz_output: Dict[str, Any],
                                llm_response: Dict[str, Any],
                                product_recommendations: List[Dict[str, Any]],
                                timing_info: Dict[str, Any],
                                verification_results: Optional[Dict[str, Any]] = None):
        """Generate human-readable markdown report."""

        report = f"""# Health Quiz Report

## Run Information
- **Run ID**: {self.run_id}
- **Date**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **Processing Time**: {timing_info.get('total_duration_seconds', 0):.2f} seconds

## Quiz Input

"""
        # Add quiz input fields
        # Handle nested quiz_input structure
        quiz_data = quiz_input.get('quiz_input', quiz_input)

        if quiz_input.get('persona_name'):
            report += f"**Persona**: {quiz_input['persona_name']}\n\n"

        report += f"**Health Issue**: {quiz_data.get('health_issue_description', 'Not provided')}\n\n"

        # Show primary_health_areas (new multiselect format)
        if quiz_data.get('primary_health_areas'):
            areas = quiz_data['primary_health_areas']
            if len(areas) == 1:
                report += f"**Primary Health Area**: {areas[0]}\n\n"
            elif len(areas) > 1:
                report += f"**Primary Health Areas**: {', '.join(areas)}\n\n"

        if quiz_data.get('severity_level'):
            report += f"**Severity Level**: {quiz_data['severity_level']}/10\n\n"

        if quiz_data.get('tried_already'):
            report += f"**What You've Tried**: {quiz_data['tried_already']}\n\n"

        if quiz_data.get('age_range'):
            report += f"**Age Range**: {quiz_data['age_range']}\n\n"

        if quiz_data.get('lifestyle_factors'):
            report += f"**Lifestyle Factors**: {quiz_data['lifestyle_factors']}\n\n"

        report += """
## Health Recommendations

### General Health Advice
"""

        for advice in quiz_output.get("general_recommendations", []):
            report += f"- {advice}\n"

        report += "\n### Lifestyle Suggestions\n"
        for suggestion in quiz_output.get("lifestyle_suggestions", []):
            report += f"- {suggestion}\n"

        report += f"""

## Product Recommendations

Found {len(product_recommendations)} relevant products:

"""

        for i, product in enumerate(product_recommendations, 1):
            report += f"""### {i}. {product.get('title', 'Unknown Product')}
- **Relevance Score**: {product.get('relevance_score', 0):.2f}/1.0
- **Category**: {product.get('category', 'Unknown')}
- **Rationale**: {product.get('rationale', 'No rationale provided')}
- **Key Ingredients**: {', '.join(product.get('ingredient_highlights', []))}
- **Link**: [Purchase {product.get('title', 'Product')}]({product.get('purchase_link', '#')})

"""

        # Add verification section if present
        if verification_results:
            status_icon = "✅" if verification_results["passed"] else "❌"
            status_text = "PASSED" if verification_results["passed"] else "FAILED"

            report += f"""
## Recommendation Verification

**Status**: {status_icon} {status_text}

"""
            # Required products check
            if "must_include" in verification_results["checks"]:
                must_check = verification_results["checks"]["must_include"]
                report += f"""### Required Products
**Found**: {must_check['found']}/{must_check['required']}

"""
                for slug, position in must_check.get("found_products", []):
                    report += f"- ✅ `{slug}` (found at position {position})\n"
                for slug in must_check.get("missing_products", []):
                    report += f"- ❌ `{slug}` (missing)\n"
                report += "\n"

            # Optional products check
            if "should_include" in verification_results["checks"]:
                should_check = verification_results["checks"]["should_include"]
                if should_check["expected"] > 0:
                    report += f"""### Expected Products (Optional)
**Found**: {should_check['found']}/{should_check['expected']}

"""
                    for slug, position in should_check.get("found_products", []):
                        report += f"- ✅ `{slug}` (found at position {position})\n"
                    for slug in should_check.get("missing_products", []):
                        report += f"- ⚠️  `{slug}` (not in top recommendations)\n"
                    report += "\n"

            # Summary checks
            report += "### Verification Summary\n"
            if "product_count" in verification_results["checks"]:
                count_check = verification_results["checks"]["product_count"]
                icon = "✅" if count_check["passed"] else "❌"
                report += f"- {icon} Product count: {count_check['actual']} (minimum {count_check['expected_min']})\n"

            if "relevance_score" in verification_results["checks"]:
                rel_check = verification_results["checks"]["relevance_score"]
                icon = "✅" if rel_check["passed"] else "❌"
                report += f"- {icon} Top relevance score: {rel_check['top_score']:.2f} (minimum {rel_check['expected_min']:.2f})\n"

            if "categories" in verification_results["checks"]:
                cat_check = verification_results["checks"]["categories"]
                if cat_check["matching"]:
                    report += f"- ✅ Categories matched: {', '.join(cat_check['matching'])}\n"
                else:
                    report += f"- ⚠️  Expected categories: {', '.join(cat_check['expected'])}\n"

            # Show failures and warnings
            if verification_results["failures"]:
                report += "\n**Failures:**\n"
                for failure in verification_results["failures"]:
                    report += f"- ❌ {failure}\n"

            if verification_results["warnings"]:
                report += "\n**Warnings:**\n"
                for warning in verification_results["warnings"]:
                    report += f"- ⚠️  {warning}\n"

            report += "\n"

        if quiz_output.get("consultation_recommended"):
            report += """
## ⚠️ Professional Consultation Recommended

Based on your responses, we recommend consulting with a healthcare professional for additional guidance.
"""

        report += f"""

## Educational Resources

"""
        for resource in quiz_output.get("educational_content", []):
            report += f"- {resource}\n"

        # Save report
        with open(self.run_dir / "outputs" / "health_quiz_report.md", "w") as f:
            f.write(report)

        # Generate HTML version if markdown package is available
        self.generate_html_report(report)

    def generate_html_report(self, markdown_content: str):
        """Generate HTML version of the markdown report."""
        if not MARKDOWN_AVAILABLE:
            print("📝 Note: Install 'markdown' package to generate HTML reports: pip install markdown")
            return

        try:
            # Configure markdown with useful extensions
            md = markdown.Markdown(extensions=[
                'extra',        # Tables, footnotes, etc.
                'codehilite',   # Code syntax highlighting
                'toc',          # Table of contents
                'nl2br'         # Convert newlines to <br>
            ])

            # Convert markdown to HTML
            html_content = md.convert(markdown_content)

            # Create a complete HTML document with styling
            full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Health Quiz Report - {self.run_id}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Arvo:wght@400;700&family=Lato:wght@400;700&family=Roboto+Condensed:wght@700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Arvo', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1c390d;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .logo {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo img {{
            max-width: 200px;
            height: auto;
        }}
        h1 {{
            color: #206932;
            border-bottom: 3px solid #206932;
            padding-bottom: 10px;
            font-family: 'Roboto Condensed', sans-serif;
            font-weight: 700;
            text-transform: uppercase;
        }}
        h2 {{
            color: #206932;
            margin-top: 30px;
            font-family: 'Roboto Condensed', sans-serif;
            font-weight: 700;
            text-transform: uppercase;
        }}
        h3 {{
            color: #1c390d;
            font-family: 'Roboto Condensed', sans-serif;
            font-weight: 700;
        }}
        a {{
            color: #206932;
            text-decoration: none;
            font-weight: 600;
        }}
        a:hover {{ text-decoration: underline; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
        p {{ margin: 10px 0; }}
        strong {{ color: #206932; }}
        .quiz-input {{
            background: #e9f5ed;
            border-left: 4px solid #206932;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 0 5px 5px 0;
        }}
        .quiz-input p {{
            margin: 8px 0;
            line-height: 1.8;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .product-recommendation {{
            background: #f8f9fa;
            border-left: 4px solid #206932;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 5px 5px 0;
        }}
        .relevance-score {{
            background: #206932;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <img src="https://rogueherbalist.com/wp-content/uploads/2020/04/RogueSIGN.jpg" alt="Rogue Herbalist">
        </div>
        {html_content}
    </div>
</body>
</html>"""

            # Save HTML report
            html_path = self.run_dir / "outputs" / "health_quiz_report.html"
            with open(html_path, "w") as f:
                f.write(full_html)

            print(f"📄 HTML report generated: {html_path}")

        except Exception as e:
            print(f"⚠️  Error generating HTML report: {e}")

    def finalize_run(self):
        """Finalize run with metadata."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        metadata = {
            "run_id": self.run_id,
            "use_case": self.use_case,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "status": "completed"
        }

        with open(self.run_dir / "metadata" / "run_summary.json", "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"✅ Run completed in {duration:.1f}s: {self.run_dir}")


def process_health_quiz(quiz_input: HealthQuizInput,
                       model_override: Optional[str] = None,
                       use_case_config: Dict[str, Any] = None) -> tuple:
    """
    Process health quiz with LLM and product recommendations.

    This function now wraps the HealthQuizUseCase framework for consistency.
    Returns a 7-tuple for backward compatibility with CLI and existing code.

    Returns:
        tuple: (quiz_output, llm_response, product_recs_dict, token_usage, timing_info, client_cost_data, errors)
    """

    # Load use case configuration
    if use_case_config is None:
        config_manager = get_config_manager()
        full_config = config_manager._config
        use_case_config = full_config.get('use_cases', {}).get('health_quiz', {})

    # Determine model to use
    model = model_override or use_case_config.get('default_model', 'gpt4o_mini')

    # Import framework components
    from health_quiz_use_case import HealthQuizUseCase
    from use_case_framework import UseCaseConfig

    # Initialize use case with config
    from use_case_framework import ProcessingMode
    config_obj = UseCaseConfig(
        client_id="rogue_herbalist",
        use_case_name="health_quiz",
        model_config=model,
        processing_mode=ProcessingMode.REALTIME,
        custom_settings=use_case_config
    )

    # Add use_case_config to config object for ProductRecommendationEngine
    config_obj.use_case_config = use_case_config

    use_case = HealthQuizUseCase(config=config_obj)

    # Manually inject LLM client (framework doesn't automatically do this when instantiating directly)
    llm_client = LLMClient(model)
    use_case.set_dependencies(llm_client=llm_client, usage_tracker=None)

    start_time = time.time()
    errors = []

    # Process through framework
    try:
        result = use_case.process_request(quiz_input.to_dict())

        if not result.success:
            # Framework returned failure
            error_msg = result.metadata.get("error", "Unknown error")
            errors.append(error_msg)

            # Return minimal valid 7-tuple on failure
            quiz_output = {
                "general_recommendations": ["An error occurred processing your quiz. Please try again."],
                "lifestyle_suggestions": [],
                "educational_content": [],
                "follow_up_questions": [],
                "consultation_recommended": True,
                "confidence_score": 0.0,
                "primary_categories_addressed": [],
                "config_used": {"model": model, "error": error_msg}
            }

            return (
                quiz_output,
                {"error": error_msg},  # llm_response
                [],  # product_recs_dict
                {},  # token_usage
                {"total_duration_seconds": time.time() - start_time},  # timing_info
                {},  # client_cost_data
                errors  # errors
            )

        # Extract data from framework result
        output_data = result.data

        # Build quiz_output (first element of tuple)
        quiz_output = {
            "general_recommendations": output_data.get("general_recommendations", []),
            "lifestyle_suggestions": output_data.get("lifestyle_suggestions", []),
            "educational_content": output_data.get("educational_content", []),
            "follow_up_questions": output_data.get("follow_up_questions", []),
            "consultation_recommended": output_data.get("consultation_recommended", False),
            "confidence_score": output_data.get("confidence_score", 0.5),
            "primary_categories_addressed": output_data.get("primary_categories_addressed", []),
            "config_used": {
                "model": model,
                "max_recommendations": use_case_config.get('max_recommendations', 5),
                "min_relevance_score": use_case_config.get('min_relevance_score', 0.3),
                "consultation_threshold": use_case_config.get('consultation_threshold', 7)
            }
        }

        # Extract product recommendations and convert to dict format
        product_recs = output_data.get("specific_products", [])
        product_recs_dict = [
            {
                "product_id": p.get("product_id", ""),
                "title": p.get("title", ""),
                "description": p.get("description", ""),
                "category": p.get("category", ""),
                "relevance_score": p.get("relevance_score", 0.0),
                "purchase_link": p.get("purchase_link", ""),
                "rationale": p.get("rationale", ""),
                "ingredient_highlights": p.get("ingredient_highlights", [])
            }
            for p in product_recs
        ]

        # Build llm_response (second element - for compatibility)
        # Framework doesn't expose raw LLM response, so we construct compatible dict
        llm_response = {
            "general_advice": output_data.get("general_recommendations", []),
            "herbal_categories": [],  # Framework doesn't expose this separately
            "lifestyle_suggestions": output_data.get("lifestyle_suggestions", []),
            "educational_points": output_data.get("educational_content", []),
            "follow_up_questions": output_data.get("follow_up_questions", []),
            "consultation_needed": output_data.get("consultation_recommended", False),
            "confidence_level": output_data.get("confidence_score", 0.5),
            "reasoning": "Generated via HealthQuizUseCase framework"
        }

        end_time = time.time()

        # Get token usage and cost data from framework's LLM client
        token_usage = {}
        client_cost_data = {}
        if hasattr(use_case, 'llm_client') and use_case.llm_client:
            token_usage = use_case.llm_client.get_usage_stats()
            client_cost_data = use_case.llm_client.get_cost_breakdown_for_reporting()

        timing_info = {
            "total_duration_seconds": end_time - start_time,
            "llm_processing_time": result.processing_time if hasattr(result, 'processing_time') else end_time - start_time,
            "recommendation_engine_time": 0.0  # Not separately tracked by framework
        }

        return quiz_output, llm_response, product_recs_dict, token_usage, timing_info, client_cost_data, errors

    except Exception as e:
        # Unexpected error during framework processing
        error_msg = f"Framework error: {str(e)}"
        errors.append(error_msg)
        print(f"❌ {error_msg}")

        # Return minimal valid 7-tuple on exception
        quiz_output = {
            "general_recommendations": ["An unexpected error occurred. Please try again later."],
            "lifestyle_suggestions": [],
            "educational_content": [],
            "follow_up_questions": [],
            "consultation_recommended": True,
            "confidence_score": 0.0,
            "primary_categories_addressed": [],
            "config_used": {"model": model, "error": error_msg}
        }

        return (
            quiz_output,
            {"error": error_msg},
            [],
            {},
            {"total_duration_seconds": time.time() - start_time},
            {},
            errors
        )


def load_persona(persona_name: str) -> tuple[HealthQuizInput, str, Optional[Dict[str, Any]]]:
    """
    Load a persona from the test data.

    Returns:
        tuple: (quiz_input, persona_name, expected_recommendations)
    """
    personas_path = Path("data/health-quiz-samples/user_personas.json")

    if not personas_path.exists():
        raise FileNotFoundError(f"Personas file not found: {personas_path}")

    with open(personas_path, "r") as f:
        personas_data = json.load(f)

    # Find the persona
    for user in personas_data["users"]:
        if user["name"].lower() == persona_name.lower():
            quiz_data = user["quiz_submission"]

            # Convert to HealthQuizInput
            # Support both new primary_health_areas (list) and legacy primary_health_area (string)
            quiz_input = HealthQuizInput(
                health_issue_description=quiz_data["health_issue_description"],
                tried_already=quiz_data.get("tried_already"),
                primary_health_areas=quiz_data.get("primary_health_areas"),  # New: list of areas
                primary_health_area=quiz_data.get("primary_health_area"),    # Legacy: single area (for __post_init__)
                secondary_health_area=quiz_data.get("secondary_health_area"),  # Legacy: (for __post_init__)
                age_range=quiz_data.get("age_range"),
                severity_level=quiz_data.get("severity_level"),
                budget_preference=quiz_data.get("budget_preference"),
                lifestyle_factors=quiz_data.get("lifestyle_factors")
            )

            # Get expected recommendations if present
            expected_recommendations = user.get("expected_recommendations")

            return quiz_input, user["name"], expected_recommendations

    raise ValueError(f"Persona '{persona_name}' not found")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Run health quiz experiments")
    parser.add_argument("--model", help="Model override (e.g., gpt4o_mini, sonnet)")
    parser.add_argument("--persona", help="Test persona name (e.g., 'Sarah Chen')")
    parser.add_argument("--custom-input", help="Custom health issue description")
    parser.add_argument("--primary-area", help="Primary health area")
    parser.add_argument("--severity", type=int, help="Severity level (1-10)")

    args = parser.parse_args()

    # Initialize run manager
    runner = HealthQuizRunner()

    try:
        # Prepare quiz input
        expected_recommendations = None
        if args.persona:
            # Load from persona
            quiz_input, persona_name, expected_recommendations = load_persona(args.persona)
            print(f"🧑 Using persona: {persona_name}")
        elif args.custom_input:
            # Create from command line
            quiz_input = HealthQuizInput(
                health_issue_description=args.custom_input,
                primary_health_area=args.primary_area,
                severity_level=args.severity or 5
            )
            persona_name = "Custom Input"
        else:
            # Use default test case (Sarah Chen)
            quiz_input, persona_name, expected_recommendations = load_persona("Sarah Chen")
            print(f"🧑 Using default persona: {persona_name}")

        print(f"🚀 Starting health quiz run with model: {args.model or 'default'}")

        # Process quiz
        quiz_output, llm_response, product_recs, token_usage, timing_info, client_cost_data, errors = \
            process_health_quiz(quiz_input, args.model)

        # Save everything
        runner.snapshot_inputs(quiz_input, persona_name, expected_recommendations)
        runner.snapshot_config(model_override=args.model)
        runner.save_outputs(
            quiz_output=quiz_output,
            llm_response=llm_response,
            product_recommendations=product_recs,
            token_usage=token_usage,
            timing_info=timing_info,
            client_cost_data=client_cost_data,
            errors=errors
        )
        runner.finalize_run()

        # Print summary
        print(f"\n📊 Health Quiz Summary:")
        print(f"   Persona: {persona_name}")
        print(f"   General Recommendations: {len(quiz_output.get('general_recommendations', []))}")
        print(f"   Product Recommendations: {len(product_recs)}")
        print(f"   Consultation Recommended: {quiz_output.get('consultation_recommended', False)}")
        print(f"   Confidence Score: {quiz_output.get('confidence_score', 0):.1%}")
        print(f"   Cost: ${client_cost_data.get('session_cost', 0):.4f}")
        print(f"   Duration: {timing_info['total_duration_seconds']:.1f}s")
        print(f"   Run directory: {runner.run_dir}")

    except Exception as e:
        print(f"💀 Run failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()