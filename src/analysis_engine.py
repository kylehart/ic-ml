#!/usr/bin/env python3
"""
Analysis Engine for Category Assignment Results

Provides modular, reusable analysis functions that can be applied to
classification results either during initial runs or in post-processing.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class ClassificationAnalyzer:
    """Modular analysis engine for category assignment results."""

    def __init__(self, analysis_version: str = "1.0"):
        self.analysis_version = analysis_version
        self.available_analyses = {
            "assignment_histogram": self.generate_assignment_histogram,
            "category_distribution": self.generate_category_distribution,
            "quality_metrics": self.generate_quality_metrics,
        }

    def run_all_analyses(self, classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run all available analyses on classification results."""
        results = {
            "analysis_metadata": {
                "version": self.analysis_version,
                "timestamp": datetime.now().isoformat(),
                "total_classifications": len(classifications)
            }
        }

        for analysis_name, analysis_func in self.available_analyses.items():
            try:
                results[analysis_name] = analysis_func(classifications)
            except Exception as e:
                results[analysis_name] = {
                    "error": str(e),
                    "status": "failed"
                }

        return results

    def run_specific_analyses(self, classifications: List[Dict[str, Any]],
                            analysis_names: List[str]) -> Dict[str, Any]:
        """Run only specified analyses."""
        results = {
            "analysis_metadata": {
                "version": self.analysis_version,
                "timestamp": datetime.now().isoformat(),
                "total_classifications": len(classifications),
                "requested_analyses": analysis_names
            }
        }

        for analysis_name in analysis_names:
            if analysis_name in self.available_analyses:
                try:
                    results[analysis_name] = self.available_analyses[analysis_name](classifications)
                except Exception as e:
                    results[analysis_name] = {
                        "error": str(e),
                        "status": "failed"
                    }
            else:
                results[analysis_name] = {
                    "error": f"Analysis '{analysis_name}' not available",
                    "status": "unavailable"
                }

        return results

    def generate_assignment_histogram(self, classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate histogram analysis of classification assignments per product."""
        assignments_per_product = defaultdict(int)

        for classification in classifications:
            product_id = str(classification.get('product_id', '')).strip()
            if product_id:  # Only count non-empty product IDs
                assignments_per_product[product_id] += 1

        # Count frequency of assignment counts
        assignment_counts = list(assignments_per_product.values())
        histogram_data = defaultdict(int)

        for count in assignment_counts:
            histogram_data[count] += 1

        # Count products with zero assignments (empty product_id)
        zero_assignments = 0
        for classification in classifications:
            product_id = str(classification.get('product_id', '')).strip()
            if not product_id:
                zero_assignments += 1

        if zero_assignments > 0:
            histogram_data[0] = zero_assignments

        # Convert to regular dict and calculate statistics
        histogram_dict = dict(histogram_data)
        total_products = sum(histogram_dict.values())

        # Calculate percentages
        histogram_with_percentages = {}
        for assignments, count in histogram_dict.items():
            percentage = (count / total_products * 100) if total_products > 0 else 0
            histogram_with_percentages[str(assignments)] = {
                "products": count,
                "percentage": round(percentage, 1)
            }

        # Find examples of products with multiple assignments
        multi_assigned_examples = []
        multi_assigned = {k: v for k, v in assignments_per_product.items() if v > 1}
        for product_id, count in sorted(multi_assigned.items(), key=lambda x: x[1], reverse=True)[:10]:
            # Get the actual assignments for this product
            product_assignments = []
            for classification in classifications:
                if str(classification.get('product_id', '')).strip() == product_id:
                    category = classification.get('category_slug', '')
                    subcategory = classification.get('sub_category_slug', '')
                    product_assignments.append(f"{category}/{subcategory}" if subcategory else category)

            multi_assigned_examples.append({
                "product_id": product_id,
                "assignment_count": count,
                "assignments": product_assignments
            })

        return {
            "total_products_classified": total_products,
            "assignment_histogram": histogram_with_percentages,
            "summary": {
                "zero_assignments": histogram_dict.get(0, 0),
                "single_assignments": histogram_dict.get(1, 0),
                "multiple_assignments": sum(count for assignments, count in histogram_dict.items() if assignments > 1),
                "max_assignments_per_product": max(histogram_dict.keys()) if histogram_dict else 0
            },
            "multi_assignment_examples": multi_assigned_examples
        }

    def generate_category_distribution(self, classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate category and subcategory distribution analysis."""
        category_counts = defaultdict(int)
        subcategory_counts = defaultdict(int)

        for classification in classifications:
            category = str(classification.get('category_slug', '')).strip()
            subcategory = str(classification.get('sub_category_slug', '')).strip()

            if category:
                category_counts[category] += 1

                if subcategory:
                    subcategory_key = f"{category}/{subcategory}"
                    subcategory_counts[subcategory_key] += 1

        # Convert to regular dicts and sort
        category_dict = dict(category_counts)
        subcategory_dict = dict(subcategory_counts)

        total_assignments = sum(category_dict.values())

        # Create structured distribution with percentages
        distribution = {}
        for category, count in sorted(category_dict.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_assignments * 100) if total_assignments > 0 else 0

            # Find subcategories for this category
            subcategories = {}
            for subcat_key, subcat_count in subcategory_dict.items():
                if subcat_key.startswith(f"{category}/"):
                    subcategory = subcat_key.split('/', 1)[1]
                    subcat_percentage = (subcat_count / count * 100) if count > 0 else 0
                    subcategories[subcategory] = {
                        "count": subcat_count,
                        "percentage": round(subcat_percentage, 1)
                    }

            # Sort subcategories by count
            sorted_subcategories = dict(sorted(subcategories.items(), key=lambda x: x[1]['count'], reverse=True))

            distribution[category] = {
                "count": count,
                "percentage": round(percentage, 1),
                "subcategories": sorted_subcategories
            }

        return {
            "total_assignments": total_assignments,
            "category_distribution": distribution,
            "summary": {
                "total_categories": len(category_dict),
                "total_subcategories": len(subcategory_dict),
                "top_category": max(category_dict.items(), key=lambda x: x[1])[0] if category_dict else None,
                "top_category_count": max(category_dict.values()) if category_dict else 0
            }
        }

    def generate_quality_metrics(self, classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate quality and consistency metrics for classifications."""
        metrics = {
            "total_classifications": len(classifications),
            "unique_products": len(set(str(c.get('product_id', '')).strip() for c in classifications if c.get('product_id', '').strip())),
            "empty_categories": sum(1 for c in classifications if not str(c.get('category_slug', '')).strip()),
            "empty_subcategories": sum(1 for c in classifications if not str(c.get('sub_category_slug', '')).strip()),
            "consistency_rate": 0.0
        }

        # Calculate consistency rate (products with single assignments)
        if metrics["total_classifications"] > 0:
            assignments_per_product = defaultdict(int)
            for classification in classifications:
                product_id = str(classification.get('product_id', '')).strip()
                if product_id:
                    assignments_per_product[product_id] += 1

            single_assignments = sum(1 for count in assignments_per_product.values() if count == 1)
            metrics["consistency_rate"] = round((single_assignments / len(assignments_per_product) * 100), 1) if assignments_per_product else 0

        return metrics

    def generate_markdown_report(self, classifications: List[Dict[str, Any]],
                                run_metadata: Optional[Dict[str, Any]] = None) -> str:
        """Generate comprehensive markdown report for human review."""

        # Run all analyses
        histogram = self.generate_assignment_histogram(classifications)
        distribution = self.generate_category_distribution(classifications)
        quality = self.generate_quality_metrics(classifications)

        # Start building the report
        report_lines = []

        # Header and Executive Summary
        report_lines.extend([
            "# Classification Analysis Report",
            "",
            "## Executive Summary",
            "",
            f"**Total Products Classified:** {len(classifications)}",
            f"**Classification Accuracy:** {quality['consistency_rate']}% (products with single category assignment)",
            f"**Categories Utilized:** {distribution['summary']['total_categories']} main categories, {distribution['summary']['total_subcategories']} subcategories",
            f"**Top Category:** {distribution['summary']['top_category']} ({distribution['summary']['top_category_count']} products)",
            "",
        ])

        # Add run metadata if available
        if run_metadata:
            report_lines.extend([
                "### Run Information",
                "",
                f"- **Run ID:** {run_metadata.get('run_id', 'Unknown')}",
                f"- **Duration:** {run_metadata.get('duration_seconds', 'Unknown')}s",
                f"- **Timestamp:** {run_metadata.get('start_time', 'Unknown')}",
                "",
            ])

        # Assignment Quality Analysis
        report_lines.extend([
            "## Assignment Quality Analysis",
            "",
            "_This section shows how many category assignments each product received, indicating classification consistency._",
            "",
        ])

        # Assignment histogram in markdown table
        hist_data = histogram['assignment_histogram']
        report_lines.extend([
            "| Assignments per Product | Product Count | Percentage | Quality Indicator |",
            "|------------------------|---------------|------------|-------------------|",
        ])

        for assignments, data in sorted(hist_data.items(), key=lambda x: int(x[0])):
            assignments_num = int(assignments)
            count = data['products']
            percentage = data['percentage']

            if assignments_num == 0:
                quality_indicator = "⚠️ Failed Classification"
            elif assignments_num == 1:
                quality_indicator = "✅ Perfect Classification"
            else:
                quality_indicator = "🔄 Multiple Categories"

            report_lines.append(f"| {assignments} | {count} | {percentage}% | {quality_indicator} |")

        report_lines.extend([
            "",
            "### Key Quality Insights:",
            "",
            f"- **{quality['consistency_rate']}% Consistency Rate:** Products receiving exactly one category assignment",
            f"- **{histogram['summary']['multiple_assignments']} Products** received multiple category assignments (indicates overlapping health benefits)",
            f"- **{histogram['summary']['zero_assignments']} Products** failed to receive category assignments (requires investigation)",
            "",
        ])

        # Show examples of multiple assignments if any
        if histogram['multi_assignment_examples']:
            report_lines.extend([
                "### Products with Multiple Categories:",
                "",
                "_These products legitimately fit multiple health categories, indicating comprehensive health benefits._",
                "",
            ])

            for example in histogram['multi_assignment_examples'][:5]:  # Show top 5
                assignments_str = ", ".join(example['assignments'])
                report_lines.append(f"- **Product {example['product_id']}:** {assignments_str}")

            report_lines.extend(["", ""])

        # Category Distribution Analysis
        report_lines.extend([
            "## Category Distribution Analysis",
            "",
            "_This section shows which health categories are most commonly represented in the product catalog._",
            "",
        ])

        # Category distribution in the requested format
        cat_dist = distribution['category_distribution']
        for category, data in cat_dist.items():
            count = data['count']
            percentage = data['percentage']
            report_lines.append(f"**{category}:** {count} ({percentage}%)")

            # Add subcategories with indentation
            for subcategory, subdata in data['subcategories'].items():
                subcount = subdata['count']
                subpercentage = subdata['percentage']
                report_lines.append(f"  {subcategory}: {subcount} ({subpercentage}%)")

            report_lines.append("")  # Empty line between categories

        # Business Insights
        report_lines.extend([
            "## Business Insights",
            "",
        ])

        # Top categories analysis
        top_categories = list(cat_dist.items())[:5]  # Top 5 categories
        report_lines.extend([
            "### Market Focus Areas:",
            "",
        ])

        for i, (category, data) in enumerate(top_categories, 1):
            category_name = category.replace('-', ' ').title()
            report_lines.append(f"{i}. **{category_name}** ({data['percentage']}% of catalog)")

            # Add business context based on category
            if category == "immune-support":
                report_lines.append("   - Strong focus on immune system health products")
            elif category == "gut-health":
                report_lines.append("   - Significant emphasis on digestive wellness")
            elif category == "stress-mood-anxiety":
                report_lines.append("   - Mental wellness and stress management focus")
            elif category == "energy-vitality":
                report_lines.append("   - Energy and vitality enhancement products")
            else:
                report_lines.append(f"   - Specialized health focus area")

        report_lines.extend([
            "",
            "### Catalog Diversity:",
            "",
            f"- **{distribution['summary']['total_categories']} Main Categories:** Comprehensive health coverage",
            f"- **{distribution['summary']['total_subcategories']} Subcategories:** Detailed product specialization",
            f"- **Balanced Distribution:** No single category dominates (top category: {distribution['summary']['top_category']} at {cat_dist[distribution['summary']['top_category']]['percentage']}%)",
            "",
        ])

        # Technical Quality Metrics
        report_lines.extend([
            "## Technical Quality Metrics",
            "",
            "_For QA and system monitoring purposes._",
            "",
            "| Metric | Value | Status |",
            "|--------|-------|--------|",
            f"| Total Classifications | {quality['total_classifications']} | ✅ |",
            f"| Unique Products | {quality['unique_products']} | ✅ |",
            f"| Empty Categories | {quality['empty_categories']} | {'⚠️' if quality['empty_categories'] > 0 else '✅'} |",
            f"| Empty Subcategories | {quality['empty_subcategories']} | {'⚠️' if quality['empty_subcategories'] > 0 else '✅'} |",
            f"| Consistency Rate | {quality['consistency_rate']}% | {'✅' if quality['consistency_rate'] >= 95 else '⚠️' if quality['consistency_rate'] >= 90 else '❌'} |",
            "",
        ])

        # Quality Assessment
        if quality['consistency_rate'] >= 95:
            quality_assessment = "🟢 **Excellent** - Classification system performing optimally"
        elif quality['consistency_rate'] >= 90:
            quality_assessment = "🟡 **Good** - Minor inconsistencies, monitoring recommended"
        else:
            quality_assessment = "🔴 **Needs Attention** - Classification inconsistencies require investigation"

        report_lines.extend([
            "### Overall Quality Assessment:",
            "",
            quality_assessment,
            "",
        ])

        # Recommendations
        report_lines.extend([
            "## Recommendations",
            "",
        ])

        if quality['empty_categories'] > 0:
            report_lines.append(f"- **Address {quality['empty_categories']} products with missing categories** - Review classification logic")

        if histogram['summary']['multiple_assignments'] > len(classifications) * 0.05:  # More than 5%
            report_lines.append(f"- **Review {histogram['summary']['multiple_assignments']} products with multiple assignments** - Ensure categorization precision")

        if quality['consistency_rate'] < 95:
            report_lines.append("- **Improve classification consistency** - Current rate below 95% threshold")

        # Business recommendations
        top_category_pct = cat_dist[distribution['summary']['top_category']]['percentage']
        if top_category_pct > 30:
            report_lines.append(f"- **Consider catalog diversification** - {distribution['summary']['top_category']} represents {top_category_pct}% of products")

        report_lines.extend([
            "",
            "---",
            "",
            f"*Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')} using Analysis Engine v{self.analysis_version}*"
        ])

        return "\n".join(report_lines)


def load_classifications_from_run(run_dir: Path) -> Optional[List[Dict[str, Any]]]:
    """Load classification results from a run directory."""
    classifications_file = run_dir / "outputs" / "classifications.csv"

    if not classifications_file.exists():
        return None

    import csv
    classifications = []

    with open(classifications_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            classifications.append(dict(row))

    return classifications


def save_analysis_results(run_dir: Path, analysis_results: Dict[str, Any],
                         analysis_suffix: str = "",
                         classifications: Optional[List[Dict[str, Any]]] = None,
                         run_metadata: Optional[Dict[str, Any]] = None) -> None:
    """Save analysis results to run directory."""
    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    # Save individual analysis files
    for analysis_name, analysis_data in analysis_results.items():
        if analysis_name == "analysis_metadata":
            continue

        filename = f"{analysis_name}{analysis_suffix}.json"
        with open(outputs_dir / filename, "w") as f:
            json.dump(analysis_data, f, indent=2)

    # Save combined analysis results
    combined_filename = f"combined_analysis{analysis_suffix}.json"
    with open(outputs_dir / combined_filename, "w") as f:
        json.dump(analysis_results, f, indent=2)

    # Generate and save markdown report if classifications provided
    if classifications:
        analyzer = ClassificationAnalyzer()
        markdown_report = analyzer.generate_markdown_report(classifications, run_metadata)

        markdown_filename = f"classification_report{analysis_suffix}.md"
        with open(outputs_dir / markdown_filename, "w") as f:
            f.write(markdown_report)