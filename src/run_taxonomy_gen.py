#!/usr/bin/env python3
"""
Experimental runner for Taxonomy Generation use case.
Implements complete run management with artifact capture for taxonomy refinement.
"""

import argparse
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_client import LLMClient
from document_generation_framework import (
    DocumentFormat,
    DocumentValidator,
    DocumentDiffer,
    DocumentGenerationRunner
)
from model_config import get_config_manager


class TaxonomyGenerationRunner(DocumentGenerationRunner):
    """Manages experimental taxonomy generation runs with complete artifact capture."""

    def __init__(self):
        super().__init__(use_case="taxonomy-gen", document_format=DocumentFormat.XML)

    def snapshot_inputs(self,
                       source_taxonomy_path: Path,
                       instructions: str,
                       context_data: Optional[Dict[str, Any]] = None,
                       prompt_template: Optional[str] = None):
        """Snapshot all input data for reproducibility."""

        # Copy source taxonomy
        if source_taxonomy_path.exists():
            shutil.copy2(source_taxonomy_path, self.run_dir / "inputs" / "source_taxonomy.xml")
            print(f"📥 Source taxonomy: {source_taxonomy_path.name}")

        # Save instructions
        self.save_input("instructions.txt", instructions)

        # Save prompt template if provided
        if prompt_template:
            self.save_input("prompt_template.md", prompt_template)

        # Save context data if provided
        if context_data:
            with open(self.run_dir / "inputs" / "context_data.json", "w") as f:
                json.dump(context_data, f, indent=2)
            print(f"📥 Context data included")

    def snapshot_config(self, model_override: Optional[str] = None):
        """Snapshot configuration."""

        # Copy models.yaml
        models_config_path = Path("config") / "models.yaml"
        if models_config_path.exists():
            shutil.copy2(models_config_path, self.run_dir / "config" / "models.yaml")

        # Save run configuration
        config_manager = get_config_manager()
        full_config = config_manager._config
        use_case_config = full_config.get('use_cases', {}).get('taxonomy_generation', {})

        run_config = {
            "model_override": model_override,
            "use_case": self.use_case,
            "start_time": self.start_time.isoformat(),
            "run_id": self.run_id,
            "use_case_config": use_case_config
        }

        self.save_config(run_config)
        print(f"⚙️  Configuration snapshotted")

    def build_context_summary(self, context_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Build context summary for the LLM prompt.

        Args:
            context_data: Optional context information (product stats, usage data, etc.)

        Returns:
            Formatted context string
        """
        if not context_data:
            return "No additional context provided."

        summary_parts = []

        if "product_catalog_stats" in context_data:
            stats = context_data["product_catalog_stats"]
            summary_parts.append(f"Product Catalog: {stats.get('total_products', 0)} products")

        if "usage_patterns" in context_data:
            patterns = context_data["usage_patterns"]
            summary_parts.append(f"Usage: {patterns}")

        return "\n".join(summary_parts) if summary_parts else "No additional context provided."

    def load_prompt_template(self, prompt_path: Optional[Path] = None) -> Optional[str]:
        """
        Load external prompt template if provided.

        Args:
            prompt_path: Path to prompt template file

        Returns:
            Prompt template content or None
        """
        if not prompt_path or not prompt_path.exists():
            return None

        try:
            content = prompt_path.read_text()
            print(f"📝 Loaded prompt template: {prompt_path.name}")
            return content
        except Exception as e:
            print(f"⚠️  Failed to load prompt template: {e}")
            return None

    def chunk_taxonomy(self, source_taxonomy: str, chunk_size: int = 5) -> List[tuple]:
        """
        Split taxonomy into chunks for processing.

        Strategy: If a primary category + subcategories exceeds chunk_size,
        split it into multiple chunks (primary alone, then batches of subcategories).

        Args:
            source_taxonomy: Full taxonomy XML string
            chunk_size: Maximum taxons per chunk (including subcategories)

        Returns:
            List of (chunk_xml, taxon_ids, chunk_type) tuples
            chunk_type is 'primary' or 'subcategories'
        """
        import xml.etree.ElementTree as ET

        root = ET.fromstring(source_taxonomy)

        # Get all primary taxons with their subcategories
        primary_taxons = [t for t in root.findall('taxon') if t.attrib.get('type') == 'primary']

        chunks = []

        for primary in primary_taxons:
            # Get subcategories
            subcats = list(primary.findall('taxon[@type="subcategory"]'))
            primary_slug = primary.attrib['slug']

            # Total taxons: 1 primary + subcategories
            total_taxon_count = 1 + len(subcats)

            if total_taxon_count <= chunk_size:
                # Small enough - process as single chunk
                chunk_root = ET.Element('taxonomy', attrib=root.attrib)
                chunk_root.text = '\n\n'

                # Deep copy primary with all subcategories
                primary_copy = ET.fromstring(ET.tostring(primary))
                chunk_root.append(primary_copy)
                primary_copy.tail = '\n\n'

                chunk_xml = ET.tostring(chunk_root, encoding='unicode')
                chunks.append((chunk_xml, [primary_slug], 'complete'))
            else:
                # Too large - split into multiple chunks
                # Chunk 1: Primary with metadata but NO subcategories
                chunk_root = ET.Element('taxonomy', attrib=root.attrib)
                chunk_root.text = '\n\n'

                primary_copy = ET.fromstring(ET.tostring(primary))
                # Remove all subcategories from copy
                for subcat in list(primary_copy.findall('taxon[@type="subcategory"]')):
                    primary_copy.remove(subcat)

                chunk_root.append(primary_copy)
                primary_copy.tail = '\n\n'

                chunk_xml = ET.tostring(chunk_root, encoding='unicode')
                chunks.append((chunk_xml, [primary_slug], 'primary_only'))

                # Chunk 2+: Batches of subcategories
                for i in range(0, len(subcats), chunk_size - 1):  # -1 to leave room for context
                    batch = subcats[i:i + chunk_size - 1]

                    chunk_root = ET.Element('taxonomy', attrib=root.attrib)
                    chunk_root.text = '\n\n'

                    # Create context: primary without ingredients/subcategories
                    context_primary = ET.Element('taxon', attrib=primary.attrib)
                    for elem in ['title', 'sub-title', 'description', 'meta']:
                        e = primary.find(elem)
                        if e is not None:
                            context_primary.append(ET.fromstring(ET.tostring(e)))

                    # Add subcategories to process
                    for subcat in batch:
                        subcat_copy = ET.fromstring(ET.tostring(subcat))
                        context_primary.append(subcat_copy)
                        subcat_copy.tail = '\n    '

                    context_primary.tail = '\n\n'
                    chunk_root.append(context_primary)

                    chunk_xml = ET.tostring(chunk_root, encoding='unicode')
                    subcat_slugs = [s.attrib['slug'] for s in batch]
                    chunks.append((chunk_xml, [primary_slug] + subcat_slugs, f'subcategories_{i//chunk_size + 1}'))

        return chunks

    def merge_enhanced_chunks(self, source_taxonomy: str, enhanced_chunks: List[tuple]) -> str:
        """
        Merge enhanced chunks back into a complete taxonomy.

        Handles split primary categories by merging primary_only chunks with their
        subcategories chunks.

        Args:
            source_taxonomy: Original full taxonomy XML
            enhanced_chunks: List of (chunk_xml, chunk_type) tuples

        Returns:
            Complete enhanced taxonomy XML
        """
        import xml.etree.ElementTree as ET

        source_root = ET.fromstring(source_taxonomy)

        # Create result taxonomy with same attributes
        result_root = ET.Element('taxonomy', attrib=source_root.attrib)
        result_root.text = '\n\n'

        # Track primary categories by slug
        primary_map = {}  # slug -> primary Element

        # Process all chunks
        for chunk_xml, chunk_type in enhanced_chunks:
            chunk_root = ET.fromstring(chunk_xml)

            for taxon in chunk_root.findall('taxon'):
                slug = taxon.attrib['slug']
                taxon_type = taxon.attrib.get('type')

                if chunk_type == 'complete':
                    # Complete primary with all subcategories - add directly
                    result_root.append(taxon)
                    taxon.tail = '\n\n'
                    primary_map[slug] = taxon
                elif chunk_type == 'primary_only':
                    # Primary without subcategories - store for later merging
                    result_root.append(taxon)
                    taxon.tail = '\n\n'
                    primary_map[slug] = taxon
                elif chunk_type.startswith('subcategories_'):
                    # Subcategories chunk - find the parent primary by slug
                    # The chunk contains a context primary with the subcategories as children
                    parent_slug = slug  # The taxon slug IS the parent primary slug

                    if parent_slug in primary_map:
                        parent_primary = primary_map[parent_slug]
                        # Add subcategories from this chunk to the parent
                        for subcat in taxon.findall('taxon[@type="subcategory"]'):
                            parent_primary.append(subcat)
                            subcat.tail = '\n    '

        return ET.tostring(result_root, encoding='unicode')

    def generate_with_validation(self,
                                 source_taxonomy: str,
                                 instructions: str,
                                 context_summary: str,
                                 model: str,
                                 max_retries: int = 3,
                                 prompt_template: Optional[str] = None) -> str:
        """
        Generate taxonomy with automatic validation and retry.

        Args:
            source_taxonomy: Original taxonomy XML content
            instructions: Generation/refinement instructions
            context_summary: Context information summary
            model: LLM model to use
            max_retries: Maximum number of generation attempts

        Returns:
            Generated and validated taxonomy XML
        """
        client = LLMClient(model)

        # Build initial prompt - use template if provided, otherwise use default
        if prompt_template:
            # Use external prompt template
            # The template should be followed by the taxonomy
            base_prompt = f"""{prompt_template}

{source_taxonomy}

CONTEXT:
{context_summary}

INSTRUCTIONS:
{instructions}

Return the complete generated taxonomy in valid XML format."""
        else:
            # Use default built-in prompt
            base_prompt = f"""You are a taxonomy expert for herbal products and health categories.

SOURCE TAXONOMY:
{source_taxonomy}

CONTEXT:
{context_summary}

INSTRUCTIONS:
{instructions}

Generate an improved taxonomy in the EXACT SAME XML format as the source.

IMPORTANT REQUIREMENTS:
- Maintain the same XML structure: <taxonomy version="1.0" namespace="...">
- Each <taxon> must have: slug attribute, <title>, <description>
- Keep the hierarchical structure with type="primary" and type="subcategory"
- Preserve the <meta> elements with chebi-roles, npclassifier, etc.
- Use proper XML entity encoding: &amp; for &, &lt; for <, &gt; for >
- Return ONLY the complete XML document
- Do NOT add explanations or comments outside the XML
- Ensure all XML is well-formed and valid
- DO NOT use markdown code blocks (```xml) - return raw XML only

Return the complete generated taxonomy now:"""

        errors_encountered = []

        for attempt in range(max_retries):
            try:
                print(f"🔄 Generation attempt {attempt + 1}/{max_retries}...")

                messages = [{"role": "user", "content": base_prompt}]
                response = client.complete_sync(messages)

                # Save raw response for debugging
                with open(self.run_dir / "outputs" / f"raw_response_attempt_{attempt+1}.txt", "w") as f:
                    f.write(response)

                # Clean response
                cleaned = self.clean_llm_response(response)

                # Save cleaned response for debugging
                with open(self.run_dir / "outputs" / f"cleaned_response_attempt_{attempt+1}.xml", "w") as f:
                    f.write(cleaned)

                # Validate XML
                is_valid_xml, xml_error = self.validator.validate_xml(cleaned)
                if not is_valid_xml:
                    error_msg = f"XML validation failed: {xml_error}"
                    print(f"⚠️  {error_msg}")
                    errors_encountered.append(error_msg)

                    # Add feedback to prompt for next attempt
                    base_prompt += f"\n\nPREVIOUS ATTEMPT FAILED:\nError: {xml_error}\nPlease fix the XML syntax and regenerate."
                    continue

                # Validate taxonomy structure
                is_valid_structure, structure_error = self.validator.validate_taxonomy_structure(cleaned)
                if not is_valid_structure:
                    error_msg = f"Structure validation failed: {structure_error}"
                    print(f"⚠️  {error_msg}")
                    errors_encountered.append(error_msg)

                    # Add feedback to prompt for next attempt
                    base_prompt += f"\n\nPREVIOUS ATTEMPT FAILED:\nError: {structure_error}\nPlease fix the taxonomy structure and regenerate."
                    continue

                # Success!
                print(f"✅ Generated valid taxonomy on attempt {attempt + 1}")

                # Save token usage and cost data
                token_usage = client.get_usage_stats()
                client_cost_data = client.get_cost_breakdown_for_reporting()

                with open(self.run_dir / "outputs" / "token_usage.json", "w") as f:
                    json.dump(token_usage, f, indent=2)

                with open(self.run_dir / "outputs" / "client_cost_breakdown.json", "w") as f:
                    json.dump(client_cost_data, f, indent=2)

                # Save any errors encountered during retries
                if errors_encountered:
                    with open(self.run_dir / "outputs" / "generation_errors.log", "w") as f:
                        for error in errors_encountered:
                            f.write(f"{error}\n")

                return cleaned

            except Exception as e:
                # Save cost data even on error attempts
                try:
                    token_usage = client.get_usage_stats()
                    client_cost_data = client.get_cost_breakdown_for_reporting()

                    with open(self.run_dir / "outputs" / "token_usage_partial.json", "w") as f:
                        json.dump(token_usage, f, indent=2)

                    with open(self.run_dir / "outputs" / "client_cost_breakdown_partial.json", "w") as f:
                        json.dump(client_cost_data, f, indent=2)
                except:
                    pass
                error_msg = f"Generation error on attempt {attempt + 1}: {str(e)}"
                print(f"❌ {error_msg}")
                errors_encountered.append(error_msg)

                if attempt == max_retries - 1:
                    # Last attempt failed
                    raise ValueError(f"Failed to generate valid taxonomy after {max_retries} attempts. Errors: {errors_encountered}")

        # Save cost data even when all retries failed
        try:
            token_usage = client.get_usage_stats()
            client_cost_data = client.get_cost_breakdown_for_reporting()

            with open(self.run_dir / "outputs" / "token_usage.json", "w") as f:
                json.dump(token_usage, f, indent=2)

            with open(self.run_dir / "outputs" / "client_cost_breakdown.json", "w") as f:
                json.dump(client_cost_data, f, indent=2)
        except:
            pass

        raise ValueError(f"Failed to generate valid taxonomy after {max_retries} attempts")

    def save_all_artifacts(self,
                          source_taxonomy: str,
                          generated_taxonomy: str,
                          instructions: str):
        """
        Save all output artifacts.

        Args:
            source_taxonomy: Original taxonomy content
            generated_taxonomy: Generated taxonomy content
            instructions: Instructions used for generation
        """

        # Save generated taxonomy
        self.save_output("generated_taxonomy.xml", generated_taxonomy)

        # Generate and save diff with deep analysis
        print("📊 Generating diff report...")
        diff_data = self.differ.diff_xml(source_taxonomy, generated_taxonomy)

        self.save_output("diff.json", json.dumps(diff_data, indent=2))

        # Perform deep change analysis
        print("🔍 Analyzing changes...")
        detailed_changes = self.differ.analyze_taxonomy_changes(source_taxonomy, generated_taxonomy)
        self.save_output("detailed_changes.json", json.dumps(detailed_changes, indent=2))

        # Generate enhanced diff report
        diff_report = self.differ.generate_diff_report(diff_data, DocumentFormat.XML, detailed_changes)
        self.save_output("diff_report.md", diff_report)

        # Generate and save validation report
        print("✓ Generating validation report...")
        validation_report = self.generate_validation_report(generated_taxonomy, DocumentFormat.XML)
        self.save_output("validation_report.md", validation_report)

        # Generate combined markdown report
        combined_report = self.generate_combined_report(
            source_taxonomy,
            generated_taxonomy,
            instructions,
            diff_data,
            validation_report
        )
        self.save_output("taxonomy_generation_report.md", combined_report)

        print(f"📤 All outputs saved")

    def generate_combined_report(self,
                                 source_taxonomy: str,
                                 generated_taxonomy: str,
                                 instructions: str,
                                 diff_data: Dict[str, Any],
                                 validation_report: str) -> str:
        """Generate comprehensive markdown report."""

        report = f"""# Taxonomy Generation Report

## Run Information
- **Run ID**: {self.run_id}
- **Date**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **Use Case**: {self.use_case}

## Instructions

{instructions}

## Changes Summary

{self.differ.generate_diff_report(diff_data, DocumentFormat.XML)}

## Validation

{validation_report}

## Files Generated

- `generated_taxonomy.xml` - The improved taxonomy
- `diff.json` - Structured diff data
- `diff_report.md` - Human-readable diff report
- `validation_report.md` - Validation results
- `token_usage.json` - LLM token usage statistics
- `client_cost_breakdown.json` - Cost attribution data

"""
        return report


def process_taxonomy_generation(source_taxonomy_path: Path,
                                instructions: str,
                                model_override: Optional[str] = None,
                                context_data: Optional[Dict[str, Any]] = None,
                                prompt_template_path: Optional[Path] = None) -> tuple:
    """
    Process taxonomy generation request.

    Args:
        source_taxonomy_path: Path to source taxonomy file
        instructions: Generation instructions
        model_override: Optional model override
        context_data: Optional context information

    Returns:
        Tuple of (generated_taxonomy, success, error_message)
    """

    # Load use case configuration
    config_manager = get_config_manager()
    full_config = config_manager._config
    use_case_config = full_config.get('use_cases', {}).get('taxonomy_generation', {})

    # Get model
    model = model_override or use_case_config.get('default_model', 'openai/gpt-4o')
    max_retries = use_case_config.get('validation_retries', 3)

    # Initialize runner
    runner = TaxonomyGenerationRunner()

    try:
        # Load prompt template if provided
        prompt_template = None
        if prompt_template_path:
            prompt_template = runner.load_prompt_template(prompt_template_path)

        # Snapshot inputs
        runner.snapshot_inputs(source_taxonomy_path, instructions, context_data, prompt_template)
        runner.snapshot_config(model_override)

        # Load source taxonomy
        source_taxonomy = source_taxonomy_path.read_text()

        # Build context summary
        context_summary = runner.build_context_summary(context_data)

        # Check if chunking is needed
        import xml.etree.ElementTree as ET
        root = ET.fromstring(source_taxonomy)
        total_taxons = len(root.findall('.//taxon'))

        chunk_size = use_case_config.get('chunk_size', 5)

        if total_taxons <= chunk_size:
            # Small taxonomy - process in one go
            print(f"🚀 Generating taxonomy with model: {model} ({total_taxons} taxons)")
            generated_taxonomy = runner.generate_with_validation(
                source_taxonomy,
                instructions,
                context_summary,
                model,
                max_retries,
                prompt_template
            )
        else:
            # Large taxonomy - chunk it
            chunks = runner.chunk_taxonomy(source_taxonomy, chunk_size)
            print(f"🚀 Processing taxonomy in {len(chunks)} chunks (chunk_size={chunk_size}, total_taxons={total_taxons})")
            print(f"   Model: {model}")

            enhanced_chunks = []
            cumulative_tokens = {"total_prompt_tokens": 0, "total_completion_tokens": 0, "calls_made": 0}
            cumulative_cost = 0.0

            for i, (chunk_xml, taxon_ids, chunk_type) in enumerate(chunks, 1):
                print(f"\n📦 Chunk {i}/{len(chunks)}: {', '.join(taxon_ids)} [{chunk_type}]")

                enhanced_chunk = runner.generate_with_validation(
                    chunk_xml,
                    instructions,
                    context_summary,
                    model,
                    max_retries,
                    prompt_template
                )

                enhanced_chunks.append((enhanced_chunk, chunk_type))

                # Accumulate token usage and costs from this chunk
                try:
                    chunk_token_file = runner.run_dir / "outputs" / "token_usage.json"
                    chunk_cost_file = runner.run_dir / "outputs" / "client_cost_breakdown.json"

                    if chunk_token_file.exists():
                        with open(chunk_token_file) as f:
                            chunk_tokens = json.load(f)
                            cumulative_tokens["total_prompt_tokens"] += chunk_tokens.get("total_prompt_tokens", 0)
                            cumulative_tokens["total_completion_tokens"] += chunk_tokens.get("total_completion_tokens", 0)
                            cumulative_tokens["calls_made"] += chunk_tokens.get("calls_made", 0)

                    if chunk_cost_file.exists():
                        with open(chunk_cost_file) as f:
                            chunk_cost = json.load(f)
                            cumulative_cost += chunk_cost.get("session_cost", 0.0)
                except Exception as e:
                    print(f"⚠️  Warning: Could not accumulate token/cost data: {e}")

            # Save cumulative totals
            with open(runner.run_dir / "outputs" / "token_usage.json", "w") as f:
                json.dump(cumulative_tokens, f, indent=2)

            # Update cost breakdown with cumulative total
            try:
                with open(runner.run_dir / "outputs" / "client_cost_breakdown.json") as f:
                    cost_data = json.load(f)
                    cost_data["session_cost"] = cumulative_cost
                    cost_data["session_calls"] = cumulative_tokens["calls_made"]
                    cost_data["cost_per_call"] = cumulative_cost / max(1, cumulative_tokens["calls_made"])

                with open(runner.run_dir / "outputs" / "client_cost_breakdown.json", "w") as f:
                    json.dump(cost_data, f, indent=2)
            except Exception as e:
                print(f"⚠️  Warning: Could not update cost breakdown: {e}")

            # Merge all chunks
            print(f"\n🔗 Merging {len(enhanced_chunks)} enhanced chunks...")
            generated_taxonomy = runner.merge_enhanced_chunks(source_taxonomy, enhanced_chunks)

        # Save all artifacts
        runner.save_all_artifacts(source_taxonomy, generated_taxonomy, instructions)

        # Finalize run
        runner.finalize_run(success=True)

        # Open summary report in TextEdit for review
        report_path = runner.run_dir / "outputs" / "taxonomy_generation_report.md"
        if report_path.exists():
            import subprocess
            subprocess.run(["open", "-a", "TextEdit", str(report_path)])
            print(f"📄 Opened report in TextEdit for review")

        return generated_taxonomy, True, None

    except Exception as e:
        error_msg = str(e)
        print(f"💀 Generation failed: {error_msg}")

        # Save error log
        runner.save_output("error.log", error_msg)
        runner.finalize_run(success=False, error=error_msg)

        return None, False, error_msg


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run taxonomy generation experiments",
        epilog="""
Examples:
  # Using custom prompt template (recommended)
  python src/run_taxonomy_gen.py \\
    --prompt prompts/taxonomy-gen-prompt.md \\
    --source data/rogue-herbalist/taxonomy_trimmed.xml

  # Using inline instructions (for simple modifications)
  python src/run_taxonomy_gen.py \\
    --source data/rogue-herbalist/taxonomy_trimmed.xml \\
    --instructions "Add a new category for Sleep Support"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--prompt", help="Prompt template file (e.g., prompts/taxonomy-gen-prompt.md)")
    parser.add_argument("--source", required=True, help="Source taxonomy XML file path")
    parser.add_argument("--instructions", help="Generation instructions (for simple mods; use --prompt for complex generation)")
    parser.add_argument("--model", help="Model override (e.g., gpt4o, sonnet, gpt4o_mini)")
    parser.add_argument("--context-file", help="Optional context data JSON file")

    args = parser.parse_args()

    # Validate inputs
    if not args.prompt and not args.instructions:
        print("❌ Error: Must provide either --prompt or --instructions")
        print("   Use --prompt for complex generation with a template")
        print("   Use --instructions for simple inline modifications")
        sys.exit(1)

    # Load source taxonomy
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"❌ Source taxonomy not found: {source_path}")
        sys.exit(1)

    # Load instructions (or use empty string if using prompt template)
    instructions = ""
    if args.instructions:
        instructions = args.instructions
        if instructions.startswith("@"):
            # Load from file
            instructions_path = Path(instructions[1:])
            if not instructions_path.exists():
                print(f"❌ Instructions file not found: {instructions_path}")
                sys.exit(1)
            instructions = instructions_path.read_text()

    # Load context data if provided
    context_data = None
    if args.context_file:
        context_path = Path(args.context_file)
        if context_path.exists():
            with open(context_path, "r") as f:
                context_data = json.load(f)
        else:
            print(f"⚠️  Context file not found: {context_path}, continuing without context")

    # Load prompt template if provided
    prompt_template_path = None
    if args.prompt:
        prompt_template_path = Path(args.prompt)
        if not prompt_template_path.exists():
            print(f"❌ Prompt template not found: {prompt_template_path}")
            sys.exit(1)

    # Process generation
    generated_taxonomy, success, error = process_taxonomy_generation(
        source_path,
        instructions,
        args.model,
        context_data,
        prompt_template_path
    )

    if success:
        print(f"\n✅ Taxonomy generation completed successfully")
        sys.exit(0)
    else:
        print(f"\n❌ Taxonomy generation failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()