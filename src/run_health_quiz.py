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
from health_quiz_use_case import HealthQuizInput, HealthQuizOutput
from product_recommendation_engine import ProductRecommendationEngine
from model_config import get_config_manager


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

    def snapshot_inputs(self, quiz_input: HealthQuizInput, persona_name: str = None):
        """Snapshot quiz input data."""
        input_data = {
            "persona_name": persona_name,
            "quiz_input": quiz_input.to_dict(),
            "timestamp": self.start_time.isoformat()
        }

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

        # Generate markdown report
        self.generate_markdown_report(quiz_output, llm_response, product_recommendations, timing_info)

        print(f"📤 Outputs saved")

    def generate_markdown_report(self,
                                quiz_output: Dict[str, Any],
                                llm_response: Dict[str, Any],
                                product_recommendations: List[Dict[str, Any]],
                                timing_info: Dict[str, Any]):
        """Generate human-readable markdown report."""

        report = f"""# Health Quiz Report

## Run Information
- **Run ID**: {self.run_id}
- **Date**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **Processing Time**: {timing_info.get('total_duration_seconds', 0):.2f} seconds

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
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
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
        h1 {{ color: #2c5aa0; border-bottom: 3px solid #2c5aa0; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .product-recommendation {{
            background: #f8f9fa;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 5px 5px 0;
        }}
        .relevance-score {{
            background: #e9ecef;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
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
    """Process health quiz with LLM and product recommendations."""

    # Load use case configuration
    if use_case_config is None:
        config_manager = get_config_manager()
        full_config = config_manager._config
        use_case_config = full_config.get('use_cases', {}).get('health_quiz', {})

    # Initialize LLM client with cheapest model by default
    model = model_override or use_case_config.get('default_model', 'openai/gpt-4o-mini')
    client = LLMClient(model)

    # Create prompt for health recommendations
    prompt = f"""You are a knowledgeable herbalist and wellness advisor for Rogue Herbalist.

A customer has provided the following health information:

Health Issue: {quiz_input.health_issue_description}
What They've Tried: {quiz_input.tried_already or "Nothing specified"}
Primary Health Area: {quiz_input.primary_health_area or "Not specified"}
Secondary Health Area: {quiz_input.secondary_health_area or "None"}
Severity Level: {quiz_input.severity_level or 5}/10
Age Range: {quiz_input.age_range or "Not specified"}
Lifestyle: {quiz_input.lifestyle_factors or "Not specified"}

Please provide personalized recommendations in the following JSON format:

{{
    "general_advice": [
        "Evidence-based general health advice point 1",
        "Evidence-based general health advice point 2",
        "Evidence-based general health advice point 3"
    ],
    "herbal_categories": [
        "Relevant herbal category 1 (e.g., adaptogenic herbs)",
        "Relevant herbal category 2 (e.g., digestive herbs)"
    ],
    "lifestyle_suggestions": [
        "Specific dietary suggestion",
        "Exercise or movement suggestion",
        "Stress management or sleep suggestion"
    ],
    "educational_points": [
        "Educational fact about their condition",
        "Information about natural approaches"
    ],
    "follow_up_questions": [
        "Question to gather more information",
        "Question about symptoms or triggers"
    ],
    "consultation_needed": false,
    "confidence_level": 0.8,
    "reasoning": "Brief explanation of why these recommendations are appropriate"
}}

Guidelines:
- Provide evidence-based, safe recommendations
- Be specific and actionable
- Consider what they've already tried
- Recommend professional consultation if severity is high (>7) or concerning symptoms
- Focus on natural and herbal approaches
- Do not diagnose medical conditions"""

    start_time = time.time()
    errors = []

    # Get LLM response with retry logic
    messages = [{"role": "user", "content": prompt}]

    # Get retry configuration
    api_config = get_config_manager().get_api_config()
    max_retries = api_config.get('retry_attempts', 3)

    llm_response = None

    for attempt in range(max_retries):
        try:
            response = client.complete_sync(messages)

            # Debug: save raw response for troubleshooting
            if attempt == 0:  # Save on first attempt
                with open(f"debug_raw_response_{attempt}.txt", "w") as f:
                    f.write(f"Response length: {len(response) if response else 0}\n")
                    f.write(f"Response content: {repr(response)}\n")

            # Clean response by removing markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove ```
            cleaned_response = cleaned_response.strip()

            # Parse JSON response
            llm_response = json.loads(cleaned_response)
            break  # Success, exit retry loop

        except json.JSONDecodeError as e:
            error_msg = f"Attempt {attempt + 1}: Failed to parse LLM JSON - {str(e)} | Raw response: {repr(response[:100]) if response else 'Empty'}"
            print(f"⚠️  {error_msg}")
            errors.append(error_msg)

            if attempt == max_retries - 1:  # Last attempt
                llm_response = {
                    "general_advice": ["Unable to generate structured recommendations - please consult with a healthcare professional"],
                    "herbal_categories": [],
                    "lifestyle_suggestions": [],
                    "educational_points": [],
                    "follow_up_questions": [],
                    "consultation_needed": True,
                    "confidence_level": 0.2,
                    "reasoning": "Failed to parse LLM response after multiple attempts"
                }

        except Exception as e:
            error_msg = f"Attempt {attempt + 1}: LLM error - {str(e)}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)

            if attempt == max_retries - 1:  # Last attempt
                llm_response = {
                    "general_advice": ["System error - please try again later"],
                    "herbal_categories": [],
                    "lifestyle_suggestions": [],
                    "educational_points": [],
                    "follow_up_questions": [],
                    "consultation_needed": True,
                    "confidence_level": 0.0,
                    "reasoning": f"System error after {max_retries} attempts: {str(e)}"
                }

    # Initialize product recommendation engine with config
    recommendation_engine = ProductRecommendationEngine(
        "rogue_herbalist",
        catalog_path=Path("data/rogue-herbalist/minimal-product-catalog.csv"),
        config=use_case_config
    )

    # Get product recommendations using config
    max_recs = use_case_config.get('max_recommendations', 5)
    min_score = use_case_config.get('min_relevance_score', 0.3)

    product_recommendations = recommendation_engine.recommend_products(
        quiz_input=quiz_input,
        llm_context=llm_response,
        max_recommendations=max_recs,
        min_score_threshold=min_score
    )

    # Convert product recommendations to dict format
    product_recs_dict = [
        {
            "product_id": p.product_id,
            "title": p.title,
            "description": p.description,
            "category": p.category,
            "relevance_score": p.relevance_score,
            "purchase_link": p.purchase_link,
            "rationale": p.rationale,
            "ingredient_highlights": p.ingredient_highlights
        }
        for p in product_recommendations
    ]

    # Check consultation threshold
    consultation_threshold = use_case_config.get('consultation_threshold', 7)
    consultation_needed = (
        llm_response.get("consultation_needed", False) or
        (quiz_input.severity_level and quiz_input.severity_level >= consultation_threshold)
    )

    # Build final output
    quiz_output = {
        "general_recommendations": llm_response.get("general_advice", []),
        "lifestyle_suggestions": llm_response.get("lifestyle_suggestions", []),
        "educational_content": llm_response.get("educational_points", []) if use_case_config.get('include_educational_content', True) else [],
        "follow_up_questions": llm_response.get("follow_up_questions", []),
        "consultation_recommended": consultation_needed,
        "confidence_score": llm_response.get("confidence_level", 0.5),
        "primary_categories_addressed": [quiz_input.primary_health_area] if quiz_input.primary_health_area else [],
        "config_used": {
            "model": model,
            "max_recommendations": max_recs,
            "min_relevance_score": min_score,
            "consultation_threshold": consultation_threshold
        }
    }

    end_time = time.time()

    # Get token usage and cost data
    token_usage = client.get_usage_stats()
    client_cost_data = client.get_cost_breakdown_for_reporting()

    timing_info = {
        "total_duration_seconds": end_time - start_time,
        "llm_processing_time": end_time - start_time,
        "recommendation_engine_time": 0.1  # Placeholder
    }

    return quiz_output, llm_response, product_recs_dict, token_usage, timing_info, client_cost_data, errors


def load_persona(persona_name: str) -> tuple[HealthQuizInput, str]:
    """Load a persona from the test data."""
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
            quiz_input = HealthQuizInput(
                health_issue_description=quiz_data["health_issue_description"],
                tried_already=quiz_data.get("tried_already"),
                primary_health_area=quiz_data.get("primary_health_area"),
                secondary_health_area=quiz_data.get("secondary_health_area"),
                age_range=quiz_data.get("age_range"),
                severity_level=quiz_data.get("severity_level"),
                budget_preference=quiz_data.get("budget_preference"),
                lifestyle_factors=quiz_data.get("lifestyle_factors")
            )

            return quiz_input, user["name"]

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
        if args.persona:
            # Load from persona
            quiz_input, persona_name = load_persona(args.persona)
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
            quiz_input, persona_name = load_persona("Sarah Chen")
            print(f"🧑 Using default persona: {persona_name}")

        print(f"🚀 Starting health quiz run with model: {args.model or 'default'}")

        # Process quiz
        quiz_output, llm_response, product_recs, token_usage, timing_info, client_cost_data, errors = \
            process_health_quiz(quiz_input, args.model)

        # Save everything
        runner.snapshot_inputs(quiz_input, persona_name)
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