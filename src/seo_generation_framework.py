"""
SEO Generation Framework

Adds SEO metadata to XML documents (taxonomies, product catalogs, etc.).
Designed to be reusable across different document types.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import requests
from datetime import datetime


class SEOFieldValidator:
    """Validates SEO fields against character limits and requirements."""

    def __init__(self, field_config: Dict[str, Any]):
        """
        Args:
            field_config: Dict of field specifications from YAML
                e.g., {'meta-title': {'required': True, 'max_chars': 60}}
        """
        self.fields = field_config

    def validate(self, seo_element: ET.Element) -> Tuple[bool, List[str]]:
        """
        Validate all fields in <seo> element meet requirements.

        Args:
            seo_element: ET.Element containing SEO fields

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        for field_name, field_spec in self.fields.items():
            elem = seo_element.find(field_name)

            # Check required fields
            if field_spec.get('required', False):
                if elem is None or not elem.text or not elem.text.strip():
                    errors.append(f"Missing required field: {field_name}")
                    continue

            # Check character limits
            if elem is not None and elem.text:
                text = elem.text.strip()
                length = len(text)
                max_chars = field_spec.get('max_chars')

                if max_chars and length > max_chars:
                    errors.append(
                        f"{field_name} exceeds {max_chars} char limit: {length} chars"
                    )

                # Check suffix if specified (e.g., " | Rogue Herbalist" for meta-title)
                suffix = field_spec.get('suffix')
                if suffix and not text.endswith(suffix):
                    errors.append(
                        f"{field_name} must end with '{suffix}'"
                    )

        return len(errors) == 0, errors


class SEOURLBuilder:
    """Builds canonical URLs for different element types."""

    def __init__(self, url_config: Dict[str, str]):
        """
        Args:
            url_config: Dict with URL template patterns
                e.g., {'primary': 'https://example.com/category/{slug}/'}
        """
        self.templates = url_config

    def build_url(self, element: ET.Element, parent_slug: Optional[str] = None) -> str:
        """
        Build canonical URL for element.

        Args:
            element: XML element (taxon, product, etc.)
            parent_slug: Parent slug for hierarchical URLs

        Returns:
            Formatted URL string
        """
        slug = element.attrib.get('slug', '')
        elem_type = element.attrib.get('type', 'primary')

        # Determine template key
        if elem_type == 'subcategory' and parent_slug:
            template = self.templates.get('subcategory', self.templates.get('default', ''))
            return template.format(slug=slug, parent_slug=parent_slug)
        else:
            template = self.templates.get('primary', self.templates.get('default', ''))
            return template.format(slug=slug)

    def validate_url(self, url: str, timeout: int = 5) -> Tuple[bool, Optional[int]]:
        """
        Validate URL actually works (optional feature).

        Args:
            url: URL to validate
            timeout: Request timeout in seconds

        Returns:
            (is_valid, status_code)
        """
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code < 400, response.status_code
        except Exception:
            return False, None


class SEOElementContext:
    """Extracts context about an element for keyword differentiation."""

    @staticmethod
    def extract(element: ET.Element, root: ET.Element) -> Dict[str, Any]:
        """
        Extract context about element (parent, siblings, hierarchy).

        Args:
            element: Target element to get context for
            root: Root of XML tree

        Returns:
            Context dict with parent info, siblings, etc.
        """
        context = {
            'slug': element.attrib.get('slug', ''),
            'type': element.attrib.get('type', 'primary'),
            'title': element.find('title').text if element.find('title') is not None else '',
            'description': element.find('description').text if element.find('description') is not None else '',
            'parent_slug': None,
            'parent_title': None,
            'sibling_slugs': [],
        }

        # Find parent if subcategory
        if context['type'] == 'subcategory':
            # Find parent taxon containing this element
            for parent in root.findall('.//taxon[@type="primary"]'):
                if element in parent.findall('taxon[@type="subcategory"]'):
                    context['parent_slug'] = parent.attrib.get('slug', '')
                    context['parent_title'] = parent.find('title').text if parent.find('title') is not None else ''

                    # Get sibling slugs for differentiation
                    siblings = parent.findall('taxon[@type="subcategory"]')
                    context['sibling_slugs'] = [
                        s.attrib.get('slug', '') for s in siblings if s != element
                    ]
                    break

        return context


class SEORunner:
    """
    Orchestrates SEO generation for a document.

    Idempotent: Re-running replaces existing <seo> elements.
    """

    def __init__(self, run_dir: Path, config: Dict[str, Any]):
        """
        Args:
            run_dir: Directory for this run's outputs
            config: seo_generation config from models.yaml
        """
        self.run_dir = run_dir
        self.config = config
        self.validator = SEOFieldValidator(config.get('fields', {}))
        self.url_builder = SEOURLBuilder(config.get('url_templates', {}))
        self.stats = {
            'elements_processed': 0,
            'elements_succeeded': 0,
            'elements_failed': 0,
            'validation_errors': [],
            'url_validation_results': [],
        }

    def is_seo_present(self, element: ET.Element) -> bool:
        """Check if element already has <seo> block."""
        return element.find('seo') is not None

    def remove_existing_seo(self, element: ET.Element) -> None:
        """Remove existing <seo> element (for idempotency)."""
        seo = element.find('seo')
        if seo is not None:
            element.remove(seo)

    def add_seo_to_element(self, element: ET.Element, seo_xml: str) -> Tuple[bool, List[str]]:
        """
        Add <seo> element to target element.

        Args:
            element: Target element (taxon, product, etc.)
            seo_xml: Generated <seo> XML string

        Returns:
            (success, errors)
        """
        try:
            # Parse SEO XML
            seo_element = ET.fromstring(seo_xml)

            # Validate
            is_valid, errors = self.validator.validate(seo_element)
            if not is_valid:
                return False, errors

            # Remove existing (idempotent)
            self.remove_existing_seo(element)

            # Add new SEO element
            element.append(seo_element)
            seo_element.tail = '\n  '  # Format nicely

            return True, []

        except ET.ParseError as e:
            return False, [f"XML parse error: {str(e)}"]
        except Exception as e:
            return False, [f"Unexpected error: {str(e)}"]

    def validate_canonical_url(self, seo_element: ET.Element) -> Tuple[bool, Optional[int]]:
        """
        Validate canonical URL actually works.

        Args:
            seo_element: SEO element containing canonical-url

        Returns:
            (is_valid, status_code)
        """
        canonical_elem = seo_element.find('canonical-url')
        if canonical_elem is None or not canonical_elem.text:
            return False, None

        url = canonical_elem.text.strip()
        return self.url_builder.validate_url(url)

    def generate_report(self, output_path: Path) -> None:
        """Generate summary report of SEO generation run."""
        report = f"""# SEO Generation Report

**Run Directory**: `{self.run_dir}`
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Elements Processed**: {self.stats['elements_processed']}
- **Succeeded**: {self.stats['elements_succeeded']}
- **Failed**: {self.stats['elements_failed']}
- **Success Rate**: {self.stats['elements_succeeded'] / max(1, self.stats['elements_processed']) * 100:.1f}%

## Validation Errors

"""
        if self.stats['validation_errors']:
            for error in self.stats['validation_errors']:
                report += f"- {error}\n"
        else:
            report += "No validation errors.\n"

        report += "\n## URL Validation Results\n\n"

        if self.stats['url_validation_results']:
            for result in self.stats['url_validation_results']:
                status = "✅" if result['valid'] else "❌"
                report += f"{status} {result['url']} (HTTP {result['status_code']})\n"
        else:
            report += "URL validation not performed.\n"

        # Write report
        with open(output_path, 'w') as f:
            f.write(report)
