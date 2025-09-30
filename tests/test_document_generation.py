#!/usr/bin/env python3
"""
Smoke tests for document generation framework.

Tests basic functionality of validators, differs, and runners without calling LLMs.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from document_generation_framework import (
    DocumentFormat,
    DocumentValidator,
    DocumentDiffer,
    DocumentDiff
)


def test_xml_validator():
    """Test XML validation."""
    print("Testing XML validator...")

    validator = DocumentValidator()

    # Valid XML
    valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<taxonomy version="1.0" namespace="test">
    <taxon slug="test-cat" type="primary">
        <title>Test Category</title>
        <description>Test description</description>
    </taxon>
</taxonomy>"""

    is_valid, error = validator.validate_xml(valid_xml)
    assert is_valid, f"Valid XML failed validation: {error}"
    print("  ✅ Valid XML passed")

    # Invalid XML (unclosed tag)
    invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<taxonomy>
    <taxon slug="test">
        <title>Test</title>
    </taxonomy>"""

    is_valid, error = validator.validate_xml(invalid_xml)
    assert not is_valid, "Invalid XML should fail validation"
    print("  ✅ Invalid XML correctly rejected")

    print("✅ XML validator tests passed\n")


def test_taxonomy_structure_validator():
    """Test taxonomy-specific structure validation."""
    print("Testing taxonomy structure validator...")

    validator = DocumentValidator()

    # Valid taxonomy structure
    valid_taxonomy = """<?xml version="1.0" encoding="UTF-8"?>
<taxonomy version="1.0" namespace="test">
    <taxon slug="immune-support" type="primary">
        <title>Immune Support</title>
        <description>Immune system support</description>
    </taxon>
</taxonomy>"""

    is_valid, error = validator.validate_taxonomy_structure(valid_taxonomy)
    assert is_valid, f"Valid taxonomy failed validation: {error}"
    print("  ✅ Valid taxonomy structure passed")

    # Missing slug attribute
    invalid_taxonomy_1 = """<?xml version="1.0" encoding="UTF-8"?>
<taxonomy version="1.0" namespace="test">
    <taxon type="primary">
        <title>Immune Support</title>
    </taxon>
</taxonomy>"""

    is_valid, error = validator.validate_taxonomy_structure(invalid_taxonomy_1)
    assert not is_valid, "Taxonomy missing slug should fail"
    assert "slug" in error.lower(), f"Error should mention slug: {error}"
    print("  ✅ Missing slug correctly rejected")

    # Missing title element
    invalid_taxonomy_2 = """<?xml version="1.0" encoding="UTF-8"?>
<taxonomy version="1.0" namespace="test">
    <taxon slug="immune-support" type="primary">
        <description>Immune system support</description>
    </taxon>
</taxonomy>"""

    is_valid, error = validator.validate_taxonomy_structure(invalid_taxonomy_2)
    assert not is_valid, "Taxonomy missing title should fail"
    assert "title" in error.lower(), f"Error should mention title: {error}"
    print("  ✅ Missing title correctly rejected")

    # Wrong root element
    invalid_taxonomy_3 = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <taxon slug="test" type="primary">
        <title>Test</title>
    </taxon>
</root>"""

    is_valid, error = validator.validate_taxonomy_structure(invalid_taxonomy_3)
    assert not is_valid, "Wrong root element should fail"
    assert "taxonomy" in error.lower(), f"Error should mention taxonomy: {error}"
    print("  ✅ Wrong root element correctly rejected")

    print("✅ Taxonomy structure validator tests passed\n")


def test_json_validator():
    """Test JSON validation."""
    print("Testing JSON validator...")

    validator = DocumentValidator()

    # Valid JSON
    valid_json = '{"test": "value", "number": 123, "array": [1, 2, 3]}'
    is_valid, error = validator.validate_json(valid_json)
    assert is_valid, f"Valid JSON failed validation: {error}"
    print("  ✅ Valid JSON passed")

    # Invalid JSON (trailing comma)
    invalid_json = '{"test": "value", "number": 123,}'
    is_valid, error = validator.validate_json(invalid_json)
    assert not is_valid, "Invalid JSON should fail validation"
    print("  ✅ Invalid JSON correctly rejected")

    print("✅ JSON validator tests passed\n")


def test_text_differ():
    """Test text-based diff generation."""
    print("Testing text differ...")

    differ = DocumentDiffer()

    before = """Line 1
Line 2
Line 3
Line 4"""

    after = """Line 1
Line 2 modified
Line 3
Line 5"""

    diff = differ.diff_text(before, after)

    assert isinstance(diff, DocumentDiff), "Should return DocumentDiff object"
    assert diff.stats['before_lines'] == 4, "Should count before lines correctly"
    assert diff.stats['after_lines'] == 4, "Should count after lines correctly"
    assert diff.stats['additions'] > 0, "Should detect additions"
    assert diff.stats['deletions'] > 0, "Should detect deletions"
    assert len(diff.unified_diff) > 0, "Should generate unified diff"

    print("  ✅ Text diff generated successfully")
    print(f"  📊 Stats: {diff.stats['additions']} additions, {diff.stats['deletions']} deletions")
    print("✅ Text differ tests passed\n")


def test_xml_differ():
    """Test XML-specific diff generation."""
    print("Testing XML differ...")

    differ = DocumentDiffer()

    before_xml = """<?xml version="1.0" encoding="UTF-8"?>
<taxonomy>
    <taxon slug="immune-support" type="primary">
        <title>Immune Support</title>
    </taxon>
    <taxon slug="digestive-health" type="primary">
        <title>Digestive Health</title>
    </taxon>
</taxonomy>"""

    after_xml = """<?xml version="1.0" encoding="UTF-8"?>
<taxonomy>
    <taxon slug="immune-support" type="primary">
        <title>Immune Support Enhanced</title>
    </taxon>
    <taxon slug="stress-relief" type="primary">
        <title>Stress Relief</title>
    </taxon>
</taxonomy>"""

    diff = differ.diff_xml(before_xml, after_xml)

    assert isinstance(diff, dict), "Should return dict"
    assert 'stats' in diff, "Should include stats"
    assert 'added_nodes' in diff, "Should include added nodes"
    assert 'removed_nodes' in diff, "Should include removed nodes"
    assert 'modified_nodes' in diff, "Should include modified nodes"

    print("  ✅ XML diff generated successfully")
    print(f"  📊 Stats: {diff['stats']}")
    print("✅ XML differ tests passed\n")


def test_diff_report_generation():
    """Test markdown diff report generation."""
    print("Testing diff report generation...")

    differ = DocumentDiffer()

    # Sample diff data
    diff_data = {
        'added_nodes': ['/taxonomy/taxon[@slug="new-category"]'],
        'removed_nodes': ['/taxonomy/taxon[@slug="old-category"]'],
        'modified_nodes': ['/taxonomy/taxon[@slug="modified-category"]'],
        'stats': {
            'total_changes': 3,
            'additions': 1,
            'deletions': 1,
            'modifications': 1
        }
    }

    report = differ.generate_diff_report(diff_data, DocumentFormat.XML)

    assert isinstance(report, str), "Should return string"
    assert "Total Changes" in report, "Should include stats"
    assert "Added Nodes" in report, "Should include added nodes section"
    assert "Removed Nodes" in report, "Should include removed nodes section"
    assert "Modified Nodes" in report, "Should include modified nodes section"

    print("  ✅ Diff report generated successfully")
    print(f"  📄 Report length: {len(report)} characters")
    print("✅ Diff report generation tests passed\n")


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 60)
    print("Running Document Generation Framework Smoke Tests")
    print("=" * 60 + "\n")

    try:
        test_xml_validator()
        test_taxonomy_structure_validator()
        test_json_validator()
        test_text_differ()
        test_xml_differ()
        test_diff_report_generation()

        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
