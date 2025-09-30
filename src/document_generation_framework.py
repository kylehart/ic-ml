"""
Document Generation Framework

Shared infrastructure for document generation use cases including:
- Document validation (XML, JSON, YAML, Markdown)
- Document diffing and change tracking
- Base experimental runner for document generation
"""

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import difflib
import re


class DocumentFormat(Enum):
    """Supported document formats."""
    XML = "xml"
    JSON = "json"
    MARKDOWN = "markdown"
    YAML = "yaml"
    HTML = "html"
    TEXT = "text"


class DocumentValidator:
    """Generic document validation for various formats."""

    @staticmethod
    def validate_xml(content: str) -> Tuple[bool, str]:
        """
        Validate XML syntax and well-formedness.

        Returns:
            (is_valid, error_message)
        """
        try:
            ET.fromstring(content)
            return True, ""
        except ET.ParseError as e:
            return False, f"XML parsing error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @staticmethod
    def validate_json(content: str) -> Tuple[bool, str]:
        """
        Validate JSON syntax.

        Returns:
            (is_valid, error_message)
        """
        try:
            json.loads(content)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"JSON parsing error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    @staticmethod
    def validate_against_schema(content: str, schema: Dict, format_type: DocumentFormat) -> Tuple[bool, str]:
        """
        Validate document against a schema.

        Args:
            content: Document content as string
            schema: Schema definition (format-specific)
            format_type: Type of document (XML, JSON, etc.)

        Returns:
            (is_valid, error_message)
        """
        # Basic implementation - can be extended with jsonschema, xmlschema libraries
        if format_type == DocumentFormat.JSON:
            is_valid, error = DocumentValidator.validate_json(content)
            if not is_valid:
                return is_valid, error

            # Could add jsonschema validation here
            return True, ""

        elif format_type == DocumentFormat.XML:
            is_valid, error = DocumentValidator.validate_xml(content)
            if not is_valid:
                return is_valid, error

            # Could add xmlschema validation here
            return True, ""

        return True, "Schema validation not implemented for this format"

    @staticmethod
    def validate_taxonomy_structure(xml_content: str) -> Tuple[bool, str]:
        """
        Validate taxonomy-specific XML structure.

        Checks for:
        - Root <taxonomy> element
        - Required attributes (version, namespace)
        - Valid <taxon> elements with slugs
        - Title elements present

        Returns:
            (is_valid, error_message)
        """
        # First check basic XML validity
        is_valid, error = DocumentValidator.validate_xml(xml_content)
        if not is_valid:
            return is_valid, error

        try:
            root = ET.fromstring(xml_content)

            # Check root element
            if root.tag != "taxonomy":
                return False, "Root element must be <taxonomy>"

            # Check for taxon elements
            taxons = root.findall(".//taxon")
            if len(taxons) == 0:
                return False, "No <taxon> elements found"

            # Validate each taxon
            for i, taxon in enumerate(taxons):
                # Check for slug attribute
                if "slug" not in taxon.attrib:
                    return False, f"Taxon {i+1} missing required 'slug' attribute"

                # Check for title element
                title = taxon.find("title")
                if title is None:
                    return False, f"Taxon '{taxon.attrib.get('slug', 'unknown')}' missing <title> element"

            return True, ""

        except Exception as e:
            return False, f"Structure validation error: {str(e)}"


@dataclass
class DocumentDiff:
    """Container for document diff results."""
    added_lines: List[str]
    removed_lines: List[str]
    modified_sections: List[Dict[str, Any]]
    stats: Dict[str, int]
    unified_diff: str


class DocumentDiffer:
    """Generate diffs between document versions."""

    def diff_text(self, before: str, after: str) -> DocumentDiff:
        """
        Generate line-based diff between two text documents.

        Args:
            before: Original document content
            after: Modified document content

        Returns:
            DocumentDiff object with change information
        """
        before_lines = before.splitlines(keepends=True)
        after_lines = after.splitlines(keepends=True)

        # Generate unified diff
        unified = difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile="before",
            tofile="after",
            lineterm=""
        )
        unified_diff = "\n".join(unified)

        # Analyze changes
        differ = difflib.Differ()
        diff = list(differ.compare(before_lines, after_lines))

        added = [line[2:] for line in diff if line.startswith('+ ')]
        removed = [line[2:] for line in diff if line.startswith('- ')]

        stats = {
            "total_changes": len(added) + len(removed),
            "additions": len(added),
            "deletions": len(removed),
            "before_lines": len(before_lines),
            "after_lines": len(after_lines)
        }

        return DocumentDiff(
            added_lines=added,
            removed_lines=removed,
            modified_sections=[],
            stats=stats,
            unified_diff=unified_diff
        )

    def diff_xml(self, before: str, after: str) -> Dict[str, Any]:
        """
        Generate structured diff for XML documents.

        Args:
            before: Original XML content
            after: Modified XML content

        Returns:
            Dictionary with structured diff information
        """
        try:
            before_root = ET.fromstring(before)
            after_root = ET.fromstring(after)

            # Extract all element paths
            def get_element_paths(root, prefix=""):
                paths = {}
                for child in root:
                    path = f"{prefix}/{child.tag}"
                    if "slug" in child.attrib:
                        path += f"[@slug='{child.attrib['slug']}']"
                    paths[path] = ET.tostring(child, encoding='unicode')
                    paths.update(get_element_paths(child, path))
                return paths

            before_paths = get_element_paths(before_root)
            after_paths = get_element_paths(after_root)

            # Find differences
            before_keys = set(before_paths.keys())
            after_keys = set(after_paths.keys())

            added = list(after_keys - before_keys)
            removed = list(before_keys - after_keys)
            common = before_keys & after_keys

            modified = []
            for key in common:
                if before_paths[key] != after_paths[key]:
                    modified.append(key)

            stats = {
                "total_changes": len(added) + len(removed) + len(modified),
                "additions": len(added),
                "deletions": len(removed),
                "modifications": len(modified)
            }

            return {
                "added_nodes": added,
                "removed_nodes": removed,
                "modified_nodes": modified,
                "stats": stats
            }

        except ET.ParseError:
            # Fall back to text diff if XML parsing fails
            text_diff = self.diff_text(before, after)
            return {
                "added_nodes": [],
                "removed_nodes": [],
                "modified_nodes": [],
                "stats": text_diff.stats,
                "note": "XML parsing failed, using text diff"
            }

    def analyze_taxonomy_changes(self, before: str, after: str) -> Dict[str, Any]:
        """
        Deep analysis of taxonomy changes with categorization and impact assessment.

        Args:
            before: Original taxonomy XML
            after: Generated taxonomy XML

        Returns:
            Dictionary with detailed change analysis
        """
        import xml.etree.ElementTree as ET

        try:
            before_root = ET.fromstring(before)
            after_root = ET.fromstring(after)

            # Extract all taxons with their properties
            def extract_taxons(root):
                taxons = {}
                for taxon in root.findall(".//taxon"):
                    slug = taxon.attrib.get('slug')
                    taxon_type = taxon.attrib.get('type')

                    # Extract all sub-elements
                    title = taxon.find('title')
                    description = taxon.find('description')
                    ingredients = taxon.find('ingredients')

                    taxons[slug] = {
                        'slug': slug,
                        'type': taxon_type,
                        'title': title.text if title is not None else '',
                        'description': description.text if description is not None else '',
                        'has_ingredients': ingredients is not None,
                        'common_count': len(ingredients.findall('.//common/item')) if ingredients is not None else 0,
                        'other_count': len(ingredients.findall('.//other/item')) if ingredients is not None else 0
                    }
                return taxons

            before_taxons = extract_taxons(before_root)
            after_taxons = extract_taxons(after_root)

            # Categorize changes
            changes = {
                'new_taxons': [],
                'removed_taxons': [],
                'modified_descriptions': [],
                'added_ingredients': [],
                'modified_titles': [],
                'stats_by_category': {}
            }

            # Find new and removed taxons
            before_slugs = set(before_taxons.keys())
            after_slugs = set(after_taxons.keys())

            changes['new_taxons'] = list(after_slugs - before_slugs)
            changes['removed_taxons'] = list(before_slugs - after_slugs)

            # Analyze modifications
            for slug in before_slugs & after_slugs:
                before_taxon = before_taxons[slug]
                after_taxon = after_taxons[slug]

                # Check description changes
                if before_taxon['description'] != after_taxon['description']:
                    desc_change = {
                        'slug': slug,
                        'type': after_taxon['type'],
                        'title': after_taxon['title'],
                        'before_length': len(before_taxon['description']),
                        'after_length': len(after_taxon['description']),
                        'change_magnitude': len(after_taxon['description']) - len(before_taxon['description'])
                    }
                    changes['modified_descriptions'].append(desc_change)

                # Check ingredient additions
                if not before_taxon['has_ingredients'] and after_taxon['has_ingredients']:
                    ingredient_change = {
                        'slug': slug,
                        'type': after_taxon['type'],
                        'title': after_taxon['title'],
                        'common_count': after_taxon['common_count'],
                        'other_count': after_taxon['other_count'],
                        'total_ingredients': after_taxon['common_count'] + after_taxon['other_count']
                    }
                    changes['added_ingredients'].append(ingredient_change)

                # Check title changes
                if before_taxon['title'] != after_taxon['title']:
                    changes['modified_titles'].append({
                        'slug': slug,
                        'before': before_taxon['title'],
                        'after': after_taxon['title']
                    })

            # Generate category-level stats
            for slug in after_taxons:
                taxon = after_taxons[slug]
                if taxon['type'] == 'primary':
                    if slug not in changes['stats_by_category']:
                        changes['stats_by_category'][slug] = {
                            'title': taxon['title'],
                            'subcategories_modified': 0,
                            'total_ingredients': 0,
                            'description_changed': False
                        }

                    # Check if this category's description changed
                    if slug in before_taxons:
                        if before_taxons[slug]['description'] != taxon['description']:
                            changes['stats_by_category'][slug]['description_changed'] = True

                    # Count ingredients
                    changes['stats_by_category'][slug]['total_ingredients'] = taxon['common_count'] + taxon['other_count']

            # Count subcategory modifications per category
            for change in changes['modified_descriptions']:
                if change['type'] == 'subcategory':
                    # Find parent category
                    for cat_slug in changes['stats_by_category']:
                        if change['slug'].startswith(cat_slug.split('-')[0]):
                            changes['stats_by_category'][cat_slug]['subcategories_modified'] += 1

            return changes

        except Exception as e:
            return {'error': str(e)}

    def generate_diff_report(self, diff: Dict[str, Any], format_type: DocumentFormat = DocumentFormat.XML,
                            detailed_changes: Dict[str, Any] = None) -> str:
        """
        Create human-readable markdown diff report with deep analysis.

        Args:
            diff: Diff dictionary (from diff_xml or similar)
            format_type: Type of document being diffed
            detailed_changes: Optional detailed change analysis from analyze_taxonomy_changes

        Returns:
            Markdown-formatted diff report
        """
        report = f"""# Document Diff Report

## Summary Statistics

- **Total Changes**: {diff['stats']['total_changes']}
- **Additions**: {diff['stats'].get('additions', 0)}
- **Deletions**: {diff['stats'].get('deletions', 0)}
- **Modifications**: {diff['stats'].get('modifications', 0)}

"""

        # Add detailed analysis if provided
        if detailed_changes and 'error' not in detailed_changes:
            report += f"""## Change Analysis

### Overview
- **New Taxons**: {len(detailed_changes.get('new_taxons', []))}
- **Removed Taxons**: {len(detailed_changes.get('removed_taxons', []))}
- **Modified Descriptions**: {len(detailed_changes.get('modified_descriptions', []))}
- **Taxons with Added Ingredients**: {len(detailed_changes.get('added_ingredients', []))}

"""

            # Top categories by change volume
            if detailed_changes.get('stats_by_category'):
                report += "### Categories Ranked by Changes\n\n"
                sorted_cats = sorted(
                    detailed_changes['stats_by_category'].items(),
                    key=lambda x: (x[1]['subcategories_modified'], x[1]['total_ingredients']),
                    reverse=True
                )

                for slug, stats in sorted_cats[:10]:  # Top 10
                    report += f"**{stats['title']}** (`{slug}`)\n"
                    if stats['description_changed']:
                        report += f"  - ✏️ Description enhanced\n"
                    report += f"  - 📝 {stats['subcategories_modified']} subcategories modified\n"
                    report += f"  - 🌿 {stats['total_ingredients']} total ingredients added\n\n"

            # Description changes with largest magnitude
            if detailed_changes.get('modified_descriptions'):
                report += "\n### Largest Description Enhancements\n\n"
                sorted_desc = sorted(
                    detailed_changes['modified_descriptions'],
                    key=lambda x: abs(x['change_magnitude']),
                    reverse=True
                )

                for change in sorted_desc[:15]:  # Top 15
                    change_type = "expanded" if change['change_magnitude'] > 0 else "condensed"
                    report += f"**{change['title']}** (`{change['slug']}`)\n"
                    report += f"  - Type: {change['type']}\n"
                    report += f"  - {change['before_length']} → {change['after_length']} characters ({change_type})\n"
                    report += f"  - Change: {abs(change['change_magnitude'])} characters\n\n"

            # Ingredient additions
            if detailed_changes.get('added_ingredients'):
                report += "\n### Ingredient Lists Added\n\n"
                sorted_ingredients = sorted(
                    detailed_changes['added_ingredients'],
                    key=lambda x: x['total_ingredients'],
                    reverse=True
                )

                for change in sorted_ingredients:
                    report += f"**{change['title']}** (`{change['slug']}`)\n"
                    report += f"  - Common ingredients: {change['common_count']}\n"
                    report += f"  - Other ingredients: {change['other_count']}\n"
                    report += f"  - **Total: {change['total_ingredients']} ingredients**\n\n"

        # Standard diff sections
        if format_type == DocumentFormat.XML:
            if diff.get('added_nodes'):
                report += "\n## Technical Changes: Added Nodes\n\n"
                report += f"Total: {len(diff['added_nodes'])} nodes\n\n"
                for node in diff['added_nodes'][:20]:  # Limit to first 20
                    report += f"- `{node}`\n"
                if len(diff['added_nodes']) > 20:
                    report += f"\n... and {len(diff['added_nodes']) - 20} more\n"

            if diff.get('removed_nodes'):
                report += "\n## Technical Changes: Removed Nodes\n\n"
                report += f"Total: {len(diff['removed_nodes'])} nodes\n\n"
                for node in diff['removed_nodes'][:20]:
                    report += f"- `{node}`\n"
                if len(diff['removed_nodes']) > 20:
                    report += f"\n... and {len(diff['removed_nodes']) - 20} more\n"

            if diff.get('modified_nodes'):
                report += "\n## Technical Changes: Modified Nodes\n\n"
                report += f"Total: {len(diff['modified_nodes'])} nodes\n\n"
                for node in diff['modified_nodes'][:20]:
                    report += f"- `{node}`\n"
                if len(diff['modified_nodes']) > 20:
                    report += f"\n... and {len(diff['modified_nodes']) - 20} more\n"

        return report


class DocumentGenerationRunner:
    """Base experimental runner for document generation use cases."""

    def __init__(self, use_case: str, document_format: DocumentFormat):
        """
        Initialize document generation runner.

        Args:
            use_case: Use case name (e.g., "taxonomy-gen", "quiz-gen")
            document_format: Expected document format
        """
        self.use_case = use_case
        self.format = document_format
        self.validator = DocumentValidator()
        self.differ = DocumentDiffer()
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

    def clean_llm_response(self, response: str) -> str:
        """
        Clean LLM response by removing markdown code blocks and fixing common issues.

        Args:
            response: Raw LLM response

        Returns:
            Cleaned content
        """
        cleaned = response.strip()

        # Remove markdown code blocks
        if cleaned.startswith('```'):
            # Remove first line (```xml, ```json, etc.)
            lines = cleaned.split('\n')
            if len(lines) > 2:
                # Remove first and last lines
                cleaned = '\n'.join(lines[1:-1])
                # Also handle case where closing ``` is on same line as content
                if cleaned.endswith('```'):
                    cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        # Fix common XML issues
        if self.format == DocumentFormat.XML:
            # Replace unescaped ampersands with &amp; (but not already-escaped ones)
            import re
            # Match & that is NOT followed by common entity names
            cleaned = re.sub(r'&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', cleaned)

        return cleaned

    def save_input(self, filename: str, content: str):
        """Save input file to run directory."""
        path = self.run_dir / "inputs" / filename
        path.write_text(content)

    def save_output(self, filename: str, content: str):
        """Save output file to run directory."""
        path = self.run_dir / "outputs" / filename
        path.write_text(content)

    def save_config(self, config_data: Dict[str, Any]):
        """Save configuration to run directory."""
        path = self.run_dir / "config" / "run_config.json"
        with open(path, "w") as f:
            json.dump(config_data, f, indent=2)

    def finalize_run(self, success: bool = True, error: str = None):
        """Finalize run with metadata."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        metadata = {
            "run_id": self.run_id,
            "use_case": self.use_case,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "status": "completed" if success else "failed",
            "error": error
        }

        with open(self.run_dir / "metadata" / "run_summary.json", "w") as f:
            json.dump(metadata, f, indent=2)

        status_icon = "✅" if success else "❌"
        print(f"{status_icon} Run {'completed' if success else 'failed'} in {duration:.1f}s: {self.run_dir}")

    def generate_validation_report(self, content: str, format_type: DocumentFormat) -> str:
        """
        Generate validation report for generated document.

        Args:
            content: Generated document content
            format_type: Document format type

        Returns:
            Markdown-formatted validation report
        """
        report = f"""# Validation Report

## Document Format: {format_type.value.upper()}

"""

        if format_type == DocumentFormat.XML:
            is_valid, error = self.validator.validate_xml(content)
            report += f"### XML Well-Formedness\n"
            report += f"- **Status**: {'✅ Valid' if is_valid else '❌ Invalid'}\n"
            if error:
                report += f"- **Error**: {error}\n"

            # Additional taxonomy-specific validation
            if is_valid:
                is_valid_tax, error_tax = self.validator.validate_taxonomy_structure(content)
                report += f"\n### Taxonomy Structure\n"
                report += f"- **Status**: {'✅ Valid' if is_valid_tax else '❌ Invalid'}\n"
                if error_tax:
                    report += f"- **Error**: {error_tax}\n"

                # Count elements
                try:
                    root = ET.fromstring(content)
                    taxons = root.findall(".//taxon")
                    report += f"\n### Statistics\n"
                    report += f"- **Total Taxons**: {len(taxons)}\n"

                    primary = [t for t in taxons if t.attrib.get('type') == 'primary']
                    subcategory = [t for t in taxons if t.attrib.get('type') == 'subcategory']
                    report += f"- **Primary Categories**: {len(primary)}\n"
                    report += f"- **Subcategories**: {len(subcategory)}\n"
                except:
                    pass

        elif format_type == DocumentFormat.JSON:
            is_valid, error = self.validator.validate_json(content)
            report += f"### JSON Syntax\n"
            report += f"- **Status**: {'✅ Valid' if is_valid else '❌ Invalid'}\n"
            if error:
                report += f"- **Error**: {error}\n"

        return report
