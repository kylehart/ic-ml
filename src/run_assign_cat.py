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
                    client_cost_data: Optional[Dict[str, Any]] = None,
                    validation_report: Optional[Dict[str, Any]] = None,
                    raw_classifications: Optional[List[Dict[str, Any]]] = None):
        """Save all run outputs including validation report and separate unassigned products."""

        import csv

        # Separate assigned from unassigned products
        assigned = []
        unassigned = []

        for c in classifications:
            cat_slug = c.get('category_slug', '').strip()
            subcat_slug = c.get('sub_category_slug', '').strip()

            # Product is unassigned if both category and subcategory are empty
            if not cat_slug and not subcat_slug:
                unassigned.append(c)
            else:
                assigned.append(c)

        # Save assigned products only (main output)
        with open(self.run_dir / "outputs" / "classifications.csv", "w", newline="") as f:
            # Use exact field order from original category_assignment.csv
            fieldnames = ["taxonomy_slug", "category_slug", "sub_category_slug", "tag", "product_id"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(assigned)

        # Save unassigned products separately
        with open(self.run_dir / "outputs" / "unassigned_products.csv", "w", newline="") as f:
            fieldnames = ["product_id", "title", "slug", "reason"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()

            for c in unassigned:
                # Determine reason from validation report if available
                reason = "no_category_assigned"
                if validation_report:
                    for correction in validation_report.get('corrections', []):
                        if correction.get('product_id') == c.get('product_id'):
                            reason = correction.get('reason', 'no_category_assigned')
                            break

                writer.writerow({
                    'product_id': c.get('product_id', ''),
                    'title': c.get('title', ''),
                    'slug': c.get('slug', ''),
                    'reason': reason
                })

        # Update validation report with unassigned stats
        if validation_report:
            validation_report['assigned_count'] = len(assigned)
            validation_report['unassigned_count'] = len(unassigned)
            validation_report['unassigned_product_ids'] = [c.get('product_id') for c in unassigned]

            with open(self.run_dir / "outputs" / "validation_report.json", "w") as f:
                json.dump(validation_report, f, indent=2)

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

        print(f"📤 Outputs saved: {len(assigned)} assigned, {len(unassigned)} unassigned")


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

def validate_and_correct_slugs(classifications: List[Dict[str, Any]],
                               taxonomy_slugs: set,
                               taxonomy_tree) -> tuple:
    """
    Post-process classifications to validate and correct slugs.

    Uses fuzzy matching and hierarchical validation to auto-correct common LLM hallucinations.
    Returns corrected classifications and validation report.
    """
    from difflib import get_close_matches

    corrected = []
    validation_report = {
        "total": len(classifications),
        "valid_category": 0,
        "valid_subcategory": 0,
        "corrected_category": 0,
        "corrected_subcategory": 0,
        "invalid_category": 0,
        "invalid_subcategory": 0,
        "hierarchy_corrections": 0,
        "corrections": []
    }

    # Build hierarchical mappings
    primary_categories = set()
    subcategories = set()
    subcategory_to_parent = {}  # subcategory -> primary category
    title_to_slug = {}

    # Parse taxonomy structure
    for primary in taxonomy_tree.findall('.//taxon[@type="primary"]'):
        primary_slug = primary.get('slug')
        if primary_slug:
            primary_categories.add(primary_slug)

            # Get primary title
            title_elem = primary.find('title')
            if title_elem is not None and title_elem.text:
                title_slug = title_elem.text.lower().replace("'", "").replace(" ", "-").replace("&", "").strip()
                title_to_slug[title_slug] = primary_slug

            # Find subcategories under this primary
            for subcategory in primary.findall('.//taxon[@type="subcategory"]'):
                subcat_slug = subcategory.get('slug')
                if subcat_slug:
                    subcategories.add(subcat_slug)
                    subcategory_to_parent[subcat_slug] = primary_slug

                    # Get subcategory title
                    sub_title_elem = subcategory.find('title')
                    if sub_title_elem is not None and sub_title_elem.text:
                        sub_title_slug = sub_title_elem.text.lower().replace("'", "").replace(" ", "-").replace("&", "").strip()
                        title_to_slug[sub_title_slug] = subcat_slug

    for c in classifications:
        corrected_c = c.copy()

        # NEW APPROACH: Handle best_slug from LLM and determine hierarchy automatically
        best_slug = c.get('best_slug', '').strip()

        if best_slug:
            # Determine if it's a primary category or subcategory
            if best_slug in primary_categories:
                # It's a primary category - use it directly
                corrected_c['category_slug'] = best_slug
                corrected_c['sub_category_slug'] = ''
                validation_report['valid_category'] += 1
            elif best_slug in subcategories:
                # It's a subcategory - automatically add parent
                parent_slug = subcategory_to_parent.get(best_slug)
                if parent_slug:
                    corrected_c['category_slug'] = parent_slug
                    corrected_c['sub_category_slug'] = best_slug
                    validation_report['valid_category'] += 1
                    validation_report['valid_subcategory'] += 1
                else:
                    # Subcategory without parent - shouldn't happen but handle it
                    corrected_c['category_slug'] = ''
                    corrected_c['sub_category_slug'] = ''
                    validation_report['invalid_category'] += 1
                    validation_report['corrections'].append({
                        'product_id': c['product_id'],
                        'field': 'best_slug',
                        'old': best_slug,
                        'new': '',
                        'reason': 'subcategory_without_parent'
                    })
            elif best_slug in title_to_slug:
                # Try title-to-slug mapping
                corrected_slug = title_to_slug[best_slug]
                if corrected_slug in primary_categories:
                    corrected_c['category_slug'] = corrected_slug
                    corrected_c['sub_category_slug'] = ''
                elif corrected_slug in subcategories:
                    parent_slug = subcategory_to_parent.get(corrected_slug)
                    corrected_c['category_slug'] = parent_slug if parent_slug else ''
                    corrected_c['sub_category_slug'] = corrected_slug
                validation_report['corrected_category'] += 1
                validation_report['corrections'].append({
                    'product_id': c['product_id'],
                    'field': 'best_slug',
                    'old': best_slug,
                    'new': corrected_slug,
                    'reason': 'title_to_slug_mapping'
                })
            else:
                # Try fuzzy matching
                matches = get_close_matches(best_slug, taxonomy_slugs, n=1, cutoff=0.8)
                if matches:
                    corrected_slug = matches[0]
                    if corrected_slug in primary_categories:
                        corrected_c['category_slug'] = corrected_slug
                        corrected_c['sub_category_slug'] = ''
                    elif corrected_slug in subcategories:
                        parent_slug = subcategory_to_parent.get(corrected_slug)
                        corrected_c['category_slug'] = parent_slug if parent_slug else ''
                        corrected_c['sub_category_slug'] = corrected_slug
                    validation_report['corrected_category'] += 1
                    validation_report['corrections'].append({
                        'product_id': c['product_id'],
                        'field': 'best_slug',
                        'old': best_slug,
                        'new': corrected_slug,
                        'reason': 'fuzzy_match'
                    })
                else:
                    # No match found
                    corrected_c['category_slug'] = ''
                    corrected_c['sub_category_slug'] = ''
                    validation_report['invalid_category'] += 1
                    validation_report['corrections'].append({
                        'product_id': c['product_id'],
                        'field': 'best_slug',
                        'old': best_slug,
                        'new': '',
                        'reason': 'no_match_found'
                    })

        # OLD APPROACH (for backward compatibility if category_slug/sub_category_slug are set)
        # This handles cases where old format data exists
        cat_slug = corrected_c.get('category_slug', '').strip()
        subcat_slug = corrected_c.get('sub_category_slug', '').strip()

        if cat_slug and not best_slug:  # Only process old format if best_slug wasn't set
            # Check if it's a valid primary category
            if cat_slug in primary_categories:
                validation_report['valid_category'] += 1
            elif cat_slug in subcategories:
                # Hierarchy violation: subcategory in category position
                # Auto-correct by moving to subcategory and setting correct parent
                parent_slug = subcategory_to_parent.get(cat_slug)
                if parent_slug:
                    corrected_c['category_slug'] = parent_slug
                    corrected_c['sub_category_slug'] = cat_slug
                    validation_report['hierarchy_corrections'] += 1
                    validation_report['corrections'].append({
                        'product_id': c['product_id'],
                        'field': 'hierarchy',
                        'old': f"category={cat_slug}, subcategory={subcat_slug}",
                        'new': f"category={parent_slug}, subcategory={cat_slug}",
                        'reason': 'subcategory_in_category_position'
                    })
                else:
                    # No parent found, clear it
                    corrected_c['category_slug'] = ''
                    validation_report['invalid_category'] += 1
                    validation_report['corrections'].append({
                        'product_id': c['product_id'],
                        'field': 'category_slug',
                        'old': cat_slug,
                        'new': '',
                        'reason': 'subcategory_without_parent'
                    })
            elif cat_slug in taxonomy_slugs:
                # Valid slug but wrong type (shouldn't happen with our structure)
                validation_report['valid_category'] += 1
            else:
                # Try to auto-correct
                # 1. Check title-to-slug mapping
                if cat_slug in title_to_slug:
                    old_slug = cat_slug
                    corrected_c['category_slug'] = title_to_slug[cat_slug]
                    validation_report['corrected_category'] += 1
                    validation_report['corrections'].append({
                        'product_id': c['product_id'],
                        'field': 'category_slug',
                        'old': old_slug,
                        'new': title_to_slug[cat_slug],
                        'reason': 'title_to_slug_mapping'
                    })
                else:
                    # 2. Try fuzzy matching
                    matches = get_close_matches(cat_slug, taxonomy_slugs, n=1, cutoff=0.8)
                    if matches:
                        old_slug = cat_slug
                        corrected_c['category_slug'] = matches[0]
                        validation_report['corrected_category'] += 1
                        validation_report['corrections'].append({
                            'product_id': c['product_id'],
                            'field': 'category_slug',
                            'old': old_slug,
                            'new': matches[0],
                            'reason': 'fuzzy_match'
                        })
                    else:
                        # 3. Can't auto-correct, leave empty
                        old_slug = cat_slug
                        corrected_c['category_slug'] = ''
                        validation_report['invalid_category'] += 1
                        validation_report['corrections'].append({
                            'product_id': c['product_id'],
                            'field': 'category_slug',
                            'old': old_slug,
                            'new': '',
                            'reason': 'no_match_found'
                        })

        # Validate and correct subcategory slug (use the potentially updated subcat_slug)
        subcat_slug = corrected_c.get('sub_category_slug', '').strip()
        if subcat_slug:
            # Check if it's a valid subcategory
            if subcat_slug in subcategories:
                validation_report['valid_subcategory'] += 1
            elif subcat_slug in primary_categories:
                # Hierarchy violation: primary category in subcategory position
                # This is unusual - clear it
                corrected_c['sub_category_slug'] = ''
                validation_report['invalid_subcategory'] += 1
                validation_report['corrections'].append({
                    'product_id': c['product_id'],
                    'field': 'sub_category_slug',
                    'old': subcat_slug,
                    'new': '',
                    'reason': 'primary_category_in_subcategory_position'
                })
            elif subcat_slug in taxonomy_slugs:
                # Valid slug but wrong type
                validation_report['valid_subcategory'] += 1
            else:
                # Try to auto-correct
                if subcat_slug in title_to_slug:
                    old_slug = subcat_slug
                    corrected_c['sub_category_slug'] = title_to_slug[subcat_slug]
                    validation_report['corrected_subcategory'] += 1
                    validation_report['corrections'].append({
                        'product_id': c['product_id'],
                        'field': 'sub_category_slug',
                        'old': old_slug,
                        'new': title_to_slug[subcat_slug],
                        'reason': 'title_to_slug_mapping'
                    })
                else:
                    matches = get_close_matches(subcat_slug, taxonomy_slugs, n=1, cutoff=0.8)
                    if matches:
                        old_slug = subcat_slug
                        corrected_c['sub_category_slug'] = matches[0]
                        validation_report['corrected_subcategory'] += 1
                        validation_report['corrections'].append({
                            'product_id': c['product_id'],
                            'field': 'sub_category_slug',
                            'old': old_slug,
                            'new': matches[0],
                            'reason': 'fuzzy_match'
                        })
                    else:
                        old_slug = subcat_slug
                        corrected_c['sub_category_slug'] = ''
                        validation_report['invalid_subcategory'] += 1
                        validation_report['corrections'].append({
                            'product_id': c['product_id'],
                            'field': 'sub_category_slug',
                            'old': old_slug,
                            'new': '',
                            'reason': 'no_match_found'
                        })

        corrected.append(corrected_c)

    return corrected, validation_report

def classify_products(products: List[Product],
                     model_override: Optional[str] = None,
                     batch_size: int = 10,
                     taxonomy_path: str = "data/rogue-herbalist/taxonomy_trimmed.xml") -> tuple:
    """Main classification logic with batch processing and post-processing validation."""

    client = LLMClient(model_override)

    # Load taxonomy for classification
    taxonomy_path = Path(taxonomy_path)

    # Read taxonomy content for prompt
    taxonomy_content = ""
    valid_slugs = []
    if taxonomy_path.exists():
        taxonomy_content = taxonomy_path.read_text()

        # Extract all valid slugs from taxonomy
        import xml.etree.ElementTree as ET
        tree = ET.parse(taxonomy_path)
        root = tree.getroot()

        for taxon in root.findall('.//taxon'):
            slug = taxon.get('slug')
            if slug:
                valid_slugs.append(slug)

        valid_slugs.sort()
        valid_slugs_str = ", ".join(valid_slugs)

    # Define prompt templates for batch processing
    system_prompt = f"""You are a herbal product classifier. Use the following taxonomy to classify products into health categories.

TAXONOMY:
{taxonomy_content}

VALID SLUGS - You MUST use ONLY these exact strings:
{valid_slugs_str}

CRITICAL RULES:
1. Use ONLY slugs from the VALID SLUGS list above
2. Copy the slug EXACTLY - character-for-character
3. DO NOT modify, abbreviate, or create new slugs
4. DO NOT convert titles to slugs
5. Pick the MOST SPECIFIC slug that matches the product
6. DO NOT use product IDs as slugs

YOUR TASK (SIMPLIFIED):
- Find the single MOST SPECIFIC slug from the taxonomy that best matches each product
- Don't worry about parent/child relationships - just pick the best match
- The system will automatically add parent categories if needed

EXAMPLES:
✓ mood-balance,1234         (system will add parent: stress-mood-anxiety)
✓ mushroom-immune,5678      (system will add parent: immune-support)
✓ digestive-support,9012    (system will add parent: gut-health)
✓ immune-support,2345       (already a primary, no parent needed)

Return classifications in CSV format: best_slug,product_id
One line per product, no explanations."""

    batch_prompt_template = """Classify these {count} products based on the taxonomy provided:

{products_text}

REMINDER: Pick the MOST SPECIFIC slug for each product. Use ONLY exact slugs from the VALID SLUGS list.

Return exactly {count} lines in CSV format: best_slug,product_id
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

            # Parse batch response (new format: best_slug,product_id)
            lines = response.strip().split('\n')

            for j, line in enumerate(lines[:len(batch)]):  # Only process expected number of lines
                if j < len(batch):
                    product = batch[j]
                    parts = line.strip().split(',')

                    # New format: just the best matching slug
                    # Post-processing will determine if it's primary/subcategory and fill in parent
                    best_slug = parts[0].strip() if len(parts) > 0 else ""

                    classification = {
                        "taxonomy_slug": "health-areas",  # Standard taxonomy
                        "best_slug": best_slug,  # Store LLM's choice temporarily
                        "category_slug": "",  # Will be filled by post-processing
                        "sub_category_slug": "",  # Will be filled by post-processing
                        "tag": "",  # Empty tag field as per original format
                        "product_id": parts[1].strip() if len(parts) > 1 else product.id,
                        # Additional fields for debugging/analysis
                        "title": product.title,
                        "slug": product.slug or "",  # Product slug from WooCommerce
                        "raw_response": line.strip(),
                        "model_used": client.config.model
                    }

                    classifications.append(classification)
                    print(f"✅ {product.id}: {best_slug if best_slug else 'parse_error'}")

            print(f"  Batch {i//batch_size + 1}: Processed {len(batch)} products")

        except Exception as e:
            error_msg = f"Error processing batch {i//batch_size + 1}: {str(e)}"
            errors.append(error_msg)
            print(f"❌ {error_msg}")
            # Add empty classifications for failed batch
            for product in batch:
                classifications.append({
                    "taxonomy_slug": "health-areas",
                    "best_slug": "error",
                    "category_slug": "",
                    "sub_category_slug": "",
                    "tag": "",
                    "product_id": product.id,
                    "title": product.title,
                    "slug": product.slug or "",
                    "raw_response": "batch_error",
                    "model_used": client.config.model
                })

    end_time = time.time()

    # Post-process: validate and correct slugs
    print("\n🔍 Validating and correcting slugs...")

    # Extract taxonomy slugs for validation
    import xml.etree.ElementTree as ET
    tree = ET.parse(taxonomy_path)
    root = tree.getroot()
    taxonomy_slugs = set()
    for taxon in root.findall('.//taxon'):
        slug = taxon.get('slug')
        if slug:
            taxonomy_slugs.add(slug)

    # Save raw classifications before correction
    raw_classifications = [c.copy() for c in classifications]

    # Validate and correct
    classifications, validation_report = validate_and_correct_slugs(
        classifications,
        taxonomy_slugs,
        root
    )

    print(f"   Total: {validation_report['total']}")
    print(f"   Valid: {validation_report['valid_category']} categories, {validation_report['valid_subcategory']} subcategories")
    print(f"   Auto-corrected: {validation_report['corrected_category']} categories, {validation_report['corrected_subcategory']} subcategories")
    print(f"   Hierarchy corrections: {validation_report['hierarchy_corrections']}")
    print(f"   Invalid (cleared): {validation_report['invalid_category']} categories, {validation_report['invalid_subcategory']} subcategories")

    # Get final token usage and cost data from client
    token_usage = client.get_usage_stats()
    client_cost_data = client.get_cost_breakdown_for_reporting()

    timing_info = {
        "total_duration_seconds": end_time - start_time,
        "products_processed": len(classifications),
        "errors_count": len(errors),
        "average_time_per_product": (end_time - start_time) / len(products) if products else 0
    }

    return classifications, token_usage, timing_info, errors, prompt_templates, taxonomy_path, client_cost_data, validation_report, raw_classifications

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Run product category assignment")
    parser.add_argument("--model", help="Model override (e.g., haiku, gpt4o_mini)")
    parser.add_argument("--input", help="Input CSV file with products")
    parser.add_argument("--single-product", help="Single product title for quick test")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing (default: 10)")
    parser.add_argument("--taxonomy", default="data/rogue-herbalist/taxonomy_trimmed.xml", help="Taxonomy XML file path (default: data/rogue-herbalist/taxonomy_trimmed.xml)")

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
        classifications, token_usage, timing_info, errors, prompt_templates, taxonomy_path, client_cost_data, validation_report, raw_classifications = classify_products(
            products, args.model, args.batch_size, args.taxonomy
        )

        # Snapshot everything
        run_manager.snapshot_inputs(products, taxonomy_path, prompt_templates)
        run_manager.snapshot_config(
            model_override=args.model,
            batch_size=args.batch_size,
            input_source=args.input or args.single_product or "default_test"
        )
        run_manager.save_outputs(classifications, token_usage, timing_info, errors, client_cost_data, validation_report, raw_classifications)
        run_manager.finalize_run()

        # Calculate assigned/unassigned counts for summary
        assigned_count = sum(1 for c in classifications
                           if c.get('category_slug', '').strip() or c.get('sub_category_slug', '').strip())
        unassigned_count = len(classifications) - assigned_count

        # Print summary
        print(f"\n📊 Run Summary:")
        print(f"   Products processed: {len(classifications)}")
        print(f"   ✅ Assigned: {assigned_count}")
        print(f"   ⚠️  Unassigned: {unassigned_count}")
        print(f"   Errors: {len(errors)}")
        print(f"   Duration: {timing_info['total_duration_seconds']:.1f}s")
        print(f"   Run directory: {run_manager.run_dir}")

    except Exception as e:
        print(f"💀 Run failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()