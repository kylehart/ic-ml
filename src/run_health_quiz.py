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
    from model_config import UseCaseConfig

    # Initialize use case with config
    config_obj = UseCaseConfig(
        use_case_name="health_quiz",
        model_config=model,
        client_id="rogue_herbalist"
    )

    # Add use_case_config to config object for ProductRecommendationEngine
    config_obj.use_case_config = use_case_config

    use_case = HealthQuizUseCase(config=config_obj)

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