#!/usr/bin/env python3
"""
Main runner for product category assignment use case.
Implements experimental run management with complete artifact capture.
"""

import argparse
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_client import LLMClient
from product_processor import Product, ProductCatalogReader, BatchProcessor
from model_config import get_config_manager

class RunManager:
    """Manages experimental runs with complete artifact capture."""

    def __init__(self, use_case: str = "assign-cat"):
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

    def snapshot_inputs(self,
                       products: List[Product],
                       taxonomy_path: Optional[Path] = None,
                       prompt_templates: Optional[Dict[str, str]] = None):
        """Snapshot all input data for reproducibility."""

        # Save input products
        products_data = [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "ingredients": p.ingredients
            } for p in products
        ]

        with open(self.run_dir / "inputs" / "products.json", "w") as f:
            json.dump(products_data, f, indent=2)

        # Copy taxonomy file if provided
        if taxonomy_path and taxonomy_path.exists():
            shutil.copy2(taxonomy_path, self.run_dir / "inputs" / "taxonomy.xml")

        # Save prompt templates
        if prompt_templates:
            with open(self.run_dir / "inputs" / "prompt_templates.json", "w") as f:
                json.dump(prompt_templates, f, indent=2)

        print(f"📥 Inputs snapshotted: {len(products)} products")

    def snapshot_config(self,
                       model_override: Optional[str] = None,
                       batch_size: int = 1,
                       **kwargs):
        """Snapshot all configuration data."""

        # Copy full models.yaml
        config_manager = get_config_manager()
        models_config_path = Path("config") / "models.yaml"
        if models_config_path.exists():
            shutil.copy2(models_config_path, self.run_dir / "config" / "models.yaml")

        # Save runtime configuration
        run_config = {
            "model_override": model_override,
            "batch_size": batch_size,
            "start_time": self.start_time.isoformat(),
            "run_id": self.run_id,
            **kwargs
        }

        with open(self.run_dir / "config" / "run_config.json", "w") as f:
            json.dump(run_config, f, indent=2)

        # Save system info
        import platform
        try:
            import litellm
            litellm_version = getattr(litellm, '__version__', 'unknown')
        except:
            litellm_version = 'unknown'

        system_info = {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "litellm_version": litellm_version,
            "run_timestamp": self.start_time.isoformat()
        }

        with open(self.run_dir / "config" / "system_info.json", "w") as f:
            json.dump(system_info, f, indent=2)

        print(f"⚙️  Configuration snapshotted")

    def save_outputs(self,
                    classifications: List[Dict[str, Any]],
                    token_usage: Dict[str, Any],
                    timing_info: Dict[str, Any],
                    errors: List[str] = None):
        """Save all run outputs."""

        # Save main results as CSV (previous load-form pattern)
        import csv
        with open(self.run_dir / "outputs" / "classifications.csv", "w", newline="") as f:
            if classifications:
                writer = csv.DictWriter(f, fieldnames=classifications[0].keys())
                writer.writeheader()
                writer.writerows(classifications)

        # Save token usage
        with open(self.run_dir / "outputs" / "token_usage.json", "w") as f:
            json.dump(token_usage, f, indent=2)

        # Save timing info
        with open(self.run_dir / "outputs" / "timing.json", "w") as f:
            json.dump(timing_info, f, indent=2)

        # Save errors if any
        if errors:
            with open(self.run_dir / "outputs" / "errors.log", "w") as f:
                for error in errors:
                    f.write(f"{error}\n")

        print(f"📤 Outputs saved: {len(classifications)} classifications")

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

def classify_products(products: List[Product],
                     model_override: Optional[str] = None) -> tuple:
    """Main classification logic."""

    client = LLMClient(model_override)

    # Load taxonomy for classification
    taxonomy_path = Path("data/rogue-herbalist/taxonomy_trimmed.xml")

    # Read taxonomy content for prompt
    taxonomy_content = ""
    if taxonomy_path.exists():
        taxonomy_content = taxonomy_path.read_text()

    # Define prompt template
    system_prompt = "You are a herbal product classifier. Classify products into health categories and return CSV format."

    prompt_template = """Classify this product:

Title: {title}
Description: {description}
Ingredients: {ingredients}

Health categories:
- immune-support
- stress-mood-anxiety
- sleep-relaxation
- energy-vitality
- gut-health
- pain-inflammation

Return format: category,subcategory,product_id
Return only the classification, no explanation."""

    # Store prompt templates for snapshotting
    prompt_templates = {
        "system_prompt": system_prompt,
        "user_prompt_template": prompt_template
    }

    # Process products
    classifications = []
    token_usage = {"total_prompt_tokens": 0, "total_completion_tokens": 0, "calls_made": 0}
    errors = []

    start_time = time.time()

    for product in products:
        try:
            # Format prompt
            user_prompt = prompt_template.format(
                title=product.title,
                description=product.description,
                ingredients=', '.join(product.ingredients)
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Get classification
            response = client.complete_sync(messages)

            # Parse response (basic CSV parsing)
            parts = response.strip().split(',')
            classification = {
                "product_id": product.id,
                "title": product.title,
                "category": parts[0] if len(parts) > 0 else "",
                "subcategory": parts[1] if len(parts) > 1 else "",
                "raw_response": response.strip(),
                "model_used": client.config.model
            }

            classifications.append(classification)
            token_usage["calls_made"] += 1

            print(f"✅ {product.id}: {parts[0] if parts else 'parse_error'}")

        except Exception as e:
            error_msg = f"Error processing {product.id}: {str(e)}"
            errors.append(error_msg)
            print(f"❌ {error_msg}")

    end_time = time.time()

    timing_info = {
        "total_duration_seconds": end_time - start_time,
        "products_processed": len(classifications),
        "errors_count": len(errors),
        "average_time_per_product": (end_time - start_time) / len(products) if products else 0
    }

    return classifications, token_usage, timing_info, errors, prompt_templates, taxonomy_path

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Run product category assignment")
    parser.add_argument("--model", help="Model override (e.g., haiku, gpt4o_mini)")
    parser.add_argument("--input", help="Input CSV file with products")
    parser.add_argument("--single-product", help="Single product title for quick test")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size for processing")

    args = parser.parse_args()

    # Initialize run manager
    run_manager = RunManager()

    try:
        # Prepare products
        products = []

        if args.single_product:
            # Create test product from title
            products = [Product(
                id="test_single",
                title=args.single_product,
                description="Single product test",
                ingredients=["Unknown"]
            )]
        elif args.input:
            # Load from CSV file
            csv_path = Path(args.input)
            if not csv_path.exists():
                raise FileNotFoundError(f"Input file not found: {csv_path}")

            reader = ProductCatalogReader(csv_path, batch_size=1000)  # Load all at once for now
            for batch in reader.read_products():
                products.extend(batch)
                break  # Just get first batch for now
        else:
            # Create a test product
            products = [Product(
                id="test_default",
                title="Ashwagandha Stress Relief Capsules",
                description="Organic ashwagandha root extract to support stress management and promote calm energy. 500mg per capsule.",
                ingredients=["Ashwagandha Root Extract", "Organic Rice Flour", "Vegetable Capsule"]
            )]

        print(f"🚀 Starting run with {len(products)} products using model: {args.model or 'default'}")

        # Run classification
        classifications, token_usage, timing_info, errors, prompt_templates, taxonomy_path = classify_products(
            products, args.model
        )

        # Snapshot everything
        run_manager.snapshot_inputs(products, taxonomy_path, prompt_templates)
        run_manager.snapshot_config(
            model_override=args.model,
            batch_size=args.batch_size,
            input_source=args.input or args.single_product or "default_test"
        )
        run_manager.save_outputs(classifications, token_usage, timing_info, errors)
        run_manager.finalize_run()

        # Print summary
        print(f"\n📊 Run Summary:")
        print(f"   Products processed: {len(classifications)}")
        print(f"   Errors: {len(errors)}")
        print(f"   Duration: {timing_info['total_duration_seconds']:.1f}s")
        print(f"   Run directory: {run_manager.run_dir}")

    except Exception as e:
        print(f"💀 Run failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()