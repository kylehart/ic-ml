"""
SEO Generation Runner

Adds SEO metadata to taxonomy or product catalog XML files.
Processes one element at a time for maximum quality and reliability.

Usage:
    python src/run_seo_gen.py --source taxonomy.xml --output taxonomy_with_seo.xml
    python src/run_seo_gen.py --source taxonomy.xml --output taxonomy_with_seo.xml --prompt prompts/seo-gen-prompt.md
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

from llm_client import LLMClient
from seo_generation_framework import (
    SEOFieldValidator,
    SEOURLBuilder,
    SEOElementContext,
    SEORunner
)


def load_config() -> Dict[str, Any]:
    """Load SEO generation config from models.yaml."""
    config_path = Path("config/models.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config['use_cases']['seo_generation']


def load_prompt_template(prompt_path: Optional[Path]) -> str:
    """Load prompt template from file."""
    if prompt_path is None:
        prompt_path = Path("prompts/seo-gen-prompt.md")

    with open(prompt_path) as f:
        return f.read()


def generate_seo_for_element(
    element: ET.Element,
    context: Dict[str, Any],
    prompt_template: str,
    model: str,
    config: Dict[str, Any],
    max_retries: int = 3
) -> Optional[str]:
    """
    Generate SEO block for single element.

    Args:
        element: XML element (taxon, product, etc.)
        context: Context about element (parent, siblings, etc.)
        prompt_template: SEO generation prompt
        model: LLM model to use
        config: seo_generation config
        max_retries: Maximum retry attempts

    Returns:
        SEO XML string or None if failed
    """
    client = LLMClient(model)

    # Extract element content
    slug = element.attrib.get('slug', '')
    elem_type = context.get('type', 'primary')
    title = context.get('title', '')
    description = context.get('description', '')

    # Build canonical URL
    url_builder = SEOURLBuilder(config.get('url_templates', {}))
    canonical_url = url_builder.build_url(element, context.get('parent_slug'))

    # Build prompt with element context
    element_xml = ET.tostring(element, encoding='unicode')

    prompt = f"""{prompt_template}

---

## ELEMENT TO PROCESS

**Slug**: {slug}
**Type**: {elem_type}
**Title**: {title}
**Description**: {description}

**Full Element**:
```xml
{element_xml}
```

**Context**:
- Parent Category: {context.get('parent_title', 'N/A')} ({context.get('parent_slug', 'N/A')})
- Sibling Categories: {', '.join(context.get('sibling_slugs', [])) or 'None'}

**Canonical URL**: {canonical_url}

---

Generate the `<seo>` block now. Return ONLY the XML, no explanations:
"""

    for attempt in range(max_retries):
        try:
            messages = [{"role": "user", "content": prompt}]
            response = client.complete_sync(messages)

            # Clean response (remove markdown blocks if present)
            cleaned = response.strip()
            if cleaned.startswith("```xml"):
                cleaned = cleaned[6:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            # Fix XML entity encoding (replace unescaped & with &amp;)
            # But preserve already-escaped entities
            import re
            # Find & that are NOT followed by amp;, lt;, gt;, quot;, or apos;
            cleaned = re.sub(r'&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', r'&amp;', cleaned)

            # Validate it's actually an <seo> block
            seo_elem = ET.fromstring(cleaned)
            if seo_elem.tag != 'seo':
                raise ValueError(f"Expected <seo> element, got <{seo_elem.tag}>")

            return cleaned

        except Exception as e:
            print(f"  ⚠️  Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt == max_retries - 1:
                return None

    return None


def process_seo_generation(
    source_path: Path,
    output_path: Path,
    prompt_path: Optional[Path] = None
) -> bool:
    """
    Main SEO generation pipeline.

    Args:
        source_path: Input taxonomy/catalog XML
        output_path: Output XML with SEO metadata
        prompt_path: Optional custom prompt template

    Returns:
        True if successful
    """
    print("📁 SEO Generation Starting")
    print(f"📥 Source: {source_path.name}")
    print(f"📤 Output: {output_path.name}")

    # Load config
    config = load_config()
    model = config.get('default_model', 'gpt4o')
    validate_urls = config.get('validate_urls', False)

    print(f"   Model: {model}")
    print(f"   URL Validation: {'Enabled' if validate_urls else 'Disabled'}")

    # Create run directory
    timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    run_dir = Path(f"runs/seo-gen-{timestamp}")
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outputs").mkdir(exist_ok=True)

    # Initialize runner
    runner = SEORunner(run_dir, config)
    validator = SEOFieldValidator(config.get('fields', {}))
    url_builder = SEOURLBuilder(config.get('url_templates', {}))

    # Load prompt
    prompt_template = load_prompt_template(prompt_path)

    # Load source XML
    tree = ET.parse(source_path)
    root = tree.getroot()

    # Find elements to enhance
    element_xpath = config.get('element_xpath', './/taxon')
    elements = root.findall(element_xpath)

    print(f"\n🚀 Processing {len(elements)} elements\n")

    # Process each element
    cumulative_tokens = {"total_prompt_tokens": 0, "total_completion_tokens": 0, "calls_made": 0}
    cumulative_cost = 0.0

    for i, element in enumerate(elements, 1):
        slug = element.attrib.get('slug', f'element-{i}')
        elem_type = element.attrib.get('type', 'primary')

        print(f"📦 {i}/{len(elements)}: {slug} [{elem_type}]")

        # Extract context
        context = SEOElementContext.extract(element, root)

        # Generate SEO
        seo_xml = generate_seo_for_element(
            element, context, prompt_template, model, config
        )

        if seo_xml is None:
            print(f"  ❌ Failed after {config.get('validation_retries', 3)} attempts")
            runner.stats['elements_failed'] += 1
            runner.stats['validation_errors'].append(f"{slug}: Generation failed")
            continue

        # Add to element
        success, errors = runner.add_seo_to_element(element, seo_xml)

        if not success:
            print(f"  ❌ Validation failed: {errors}")
            runner.stats['elements_failed'] += 1
            runner.stats['validation_errors'].append(f"{slug}: {'; '.join(errors)}")
            continue

        # Validate URL if enabled
        if validate_urls:
            seo_elem = element.find('seo')
            is_valid, status_code = runner.validate_canonical_url(seo_elem)
            status_icon = "✅" if is_valid else "⚠️"
            print(f"  {status_icon} URL validation: HTTP {status_code or 'N/A'}")

            runner.stats['url_validation_results'].append({
                'slug': slug,
                'url': seo_elem.find('canonical-url').text,
                'valid': is_valid,
                'status_code': status_code
            })

        print(f"  ✅ SEO metadata added")
        runner.stats['elements_succeeded'] += 1
        runner.stats['elements_processed'] += 1

        # Accumulate token usage
        try:
            client = LLMClient(model)
            token_usage = client.get_usage_stats()
            cumulative_tokens["total_prompt_tokens"] += token_usage.get("total_prompt_tokens", 0)
            cumulative_tokens["total_completion_tokens"] += token_usage.get("total_completion_tokens", 0)
            cumulative_tokens["calls_made"] += token_usage.get("calls_made", 0)

            cost_data = client.get_cost_breakdown_for_reporting()
            cumulative_cost += cost_data.get("session_cost", 0.0)
        except:
            pass

    # Save enhanced XML
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    print(f"\n💾 Enhanced XML saved: {output_path}")

    # Save token usage and cost data
    with open(run_dir / "outputs" / "token_usage.json", "w") as f:
        json.dump(cumulative_tokens, f, indent=2)

    # Update cost breakdown
    try:
        cost_breakdown = {
            "client": "get-better-care",
            "use_case": "seo-generation",
            "project": "ic-ml",
            "environment": "production",
            "session_cost": cumulative_cost,
            "session_calls": cumulative_tokens["calls_made"],
            "cost_per_call": cumulative_cost / max(1, cumulative_tokens["calls_made"]),
            "models_used": [model]
        }
        with open(run_dir / "outputs" / "client_cost_breakdown.json", "w") as f:
            json.dump(cost_breakdown, f, indent=2)
    except Exception as e:
        print(f"⚠️  Warning: Could not save cost breakdown: {e}")

    # Generate report
    report_path = run_dir / "outputs" / "seo_generation_report.md"
    runner.generate_report(report_path)

    print(f"\n📊 Summary:")
    print(f"   Processed: {runner.stats['elements_processed']}")
    print(f"   Succeeded: {runner.stats['elements_succeeded']}")
    print(f"   Failed: {runner.stats['elements_failed']}")
    print(f"   Cost: ${cumulative_cost:.4f}")
    print(f"\n📄 Report: {report_path}")
    print(f"✅ SEO generation completed: {run_dir}")

    return runner.stats['elements_failed'] == 0


def main():
    parser = argparse.ArgumentParser(description="Add SEO metadata to taxonomy or product catalog")
    parser.add_argument("--source", required=True, help="Source XML file (taxonomy or catalog)")
    parser.add_argument("--output", required=True, help="Output XML file with SEO metadata")
    parser.add_argument("--prompt", help="Custom SEO generation prompt (optional)")

    args = parser.parse_args()

    source_path = Path(args.source)
    output_path = Path(args.output)
    prompt_path = Path(args.prompt) if args.prompt else None

    if not source_path.exists():
        print(f"❌ Source file not found: {source_path}")
        sys.exit(1)

    try:
        success = process_seo_generation(source_path, output_path, prompt_path)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ SEO generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
