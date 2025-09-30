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
from analysis_engine import ClassificationAnalyzer

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
                    errors: List[str] = None,
                    client_cost_data: Optional[Dict[str, Any]] = None):
        """Save all run outputs."""

        # Save main results as CSV (standard category_assignment format)
        import csv
        with open(self.run_dir / "outputs" / "classifications.csv", "w", newline="") as f:
            if classifications:
                # Use exact field order from original category_assignment.csv
                fieldnames = ["taxonomy_slug", "category_slug", "sub_category_slug", "tag", "product_id"]
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(classifications)

        # Save detailed results with additional debugging fields
        with open(self.run_dir / "outputs" / "classifications_detailed.csv", "w", newline="") as f:
            if classifications:
                # Remove raw_response and model_used fields as requested
                detailed_fieldnames = ["taxonomy_slug", "category_slug", "sub_category_slug", "tag", "product_id", "title"]
                writer = csv.DictWriter(f, fieldnames=detailed_fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(classifications)

        # Save token usage
        with open(self.run_dir / "outputs" / "token_usage.json", "w") as f:
            json.dump(token_usage, f, indent=2)

        # Save timing info
        with open(self.run_dir / "outputs" / "timing.json", "w") as f:
            json.dump(timing_info, f, indent=2)

        # Save client-aware cost data
        if client_cost_data:
            with open(self.run_dir / "outputs" / "client_cost_breakdown.json", "w") as f:
                json.dump(client_cost_data, f, indent=2)

        # Save errors if any
        if errors:
            with open(self.run_dir / "outputs" / "errors.log", "w") as f:
                for error in errors:
                    f.write(f"{error}\n")

        # Generate and save all analyses using modular analysis engine
        analyzer = ClassificationAnalyzer()

        # Extract model used from classifications
        model_used = classifications[0].get('model_used') if classifications else None

        analysis_results = analyzer.run_all_analyses(classifications, token_usage, model_used)

        # Create run metadata for markdown report
        run_metadata = {
            "run_id": self.run_id,
            "duration_seconds": timing_info.get('total_duration_seconds', 0),
            "start_time": self.start_time.isoformat(),
            "token_usage": token_usage,
            "model_used": model_used
        }

        # Generate and save markdown report
        markdown_report = analyzer.generate_markdown_report(classifications, run_metadata)
        with open(self.run_dir / "outputs" / "classification_report.md", "w") as f:
            f.write(markdown_report)

        # Save individual analysis files for backward compatibility
        for analysis_name, analysis_data in analysis_results.items():
            if analysis_name != "analysis_metadata":
                with open(self.run_dir / "outputs" / f"{analysis_name}.json", "w") as f:
                    json.dump(analysis_data, f, indent=2)

        # Save combined analysis results
        with open(self.run_dir / "outputs" / "combined_analysis.json", "w") as f:
            json.dump(analysis_results, f, indent=2)

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
                     model_override: Optional[str] = None,
                     batch_size: int = 10) -> tuple:
    """Main classification logic with batch processing."""

    client = LLMClient(model_override)

    # Load taxonomy for classification
    taxonomy_path = Path("data/rogue-herbalist/taxonomy_trimmed.xml")

    # Read taxonomy content for prompt
    taxonomy_content = ""
    if taxonomy_path.exists():
        taxonomy_content = taxonomy_path.read_text()

    # Define prompt templates for batch processing
    system_prompt = f"""You are a herbal product classifier. Use the following taxonomy to classify products into health categories.

TAXONOMY:
{taxonomy_content}

Return classifications in CSV format: category_slug,subcategory_slug,product_id
One line per product, no explanations."""

    batch_prompt_template = """Classify these {count} products based on the taxonomy provided:

{products_text}

Return exactly {count} lines in CSV format: category_slug,subcategory_slug,product_id
Match the product_id from each product. No headers, no explanations."""

    # Store prompt templates for snapshotting
    prompt_templates = {
        "system_prompt": system_prompt,
        "batch_prompt_template": batch_prompt_template
    }

    # Process products in batches
    classifications = []
    errors = []

    start_time = time.time()

    # Process in batches
    for i in range(0, len(products), batch_size):
        batch = products[i:i + batch_size]

        try:
            # Format batch prompt
            products_text = "\n\n".join([
                f"Product ID: {p.id}\nTitle: {p.title}\nDescription: {p.description[:500]}"  # Limit description length
                for p in batch
            ])

            user_prompt = batch_prompt_template.format(
                count=len(batch),
                products_text=products_text
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Get batch classification
            response = client.complete_sync(messages)

            # Parse batch response
            lines = response.strip().split('\n')

            for j, line in enumerate(lines[:len(batch)]):  # Only process expected number of lines
                if j < len(batch):
                    product = batch[j]
                    parts = line.strip().split(',')

                    classification = {
                        "taxonomy_slug": "health-areas",  # Standard taxonomy
                        "category_slug": parts[0].strip() if len(parts) > 0 else "",
                        "sub_category_slug": parts[1].strip() if len(parts) > 1 else "",
                        "tag": "",  # Empty tag field as per original format
                        "product_id": parts[2].strip() if len(parts) > 2 else product.id,
                        # Additional fields for debugging/analysis
                        "title": product.title,
                        "slug": product.slug or "",  # Product slug from WooCommerce
                        "raw_response": line.strip(),
                        "model_used": client.config.model
                    }

                    classifications.append(classification)
                    print(f"✅ {product.id}: {parts[0] if parts else 'parse_error'}")

            print(f"  Batch {i//batch_size + 1}: Processed {len(batch)} products")

        except Exception as e:
            error_msg = f"Error processing batch {i//batch_size + 1}: {str(e)}"
            errors.append(error_msg)
            print(f"❌ {error_msg}")
            # Add empty classifications for failed batch
            for product in batch:
                classifications.append({
                    "taxonomy_slug": "health-areas",
                    "category_slug": "error",
                    "sub_category_slug": "",
                    "tag": "",
                    "product_id": product.id,
                    "title": product.title,
                    "slug": product.slug or "",
                    "raw_response": "batch_error",
                    "model_used": client.config.model
                })

    end_time = time.time()

    # Get final token usage and cost data from client
    token_usage = client.get_usage_stats()
    client_cost_data = client.get_cost_breakdown_for_reporting()

    timing_info = {
        "total_duration_seconds": end_time - start_time,
        "products_processed": len(classifications),
        "errors_count": len(errors),
        "average_time_per_product": (end_time - start_time) / len(products) if products else 0
    }

    return classifications, token_usage, timing_info, errors, prompt_templates, taxonomy_path, client_cost_data

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Run product category assignment")
    parser.add_argument("--model", help="Model override (e.g., haiku, gpt4o_mini)")
    parser.add_argument("--input", help="Input CSV file with products")
    parser.add_argument("--single-product", help="Single product title for quick test")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing (default: 10)")

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
        print(f"   Batch size: {args.batch_size}")

        # Run classification
        classifications, token_usage, timing_info, errors, prompt_templates, taxonomy_path, client_cost_data = classify_products(
            products, args.model, args.batch_size
        )

        # Snapshot everything
        run_manager.snapshot_inputs(products, taxonomy_path, prompt_templates)
        run_manager.snapshot_config(
            model_override=args.model,
            batch_size=args.batch_size,
            input_source=args.input or args.single_product or "default_test"
        )
        run_manager.save_outputs(classifications, token_usage, timing_info, errors, client_cost_data)
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