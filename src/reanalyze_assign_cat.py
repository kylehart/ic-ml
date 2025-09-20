#!/usr/bin/env python3
"""
Reanalysis Tool for Category Assignment Results

Enables post-classification analysis without re-running expensive LLM calls.
Useful for iterative analysis development and quality assessment.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from analysis_engine import ClassificationAnalyzer, load_classifications_from_run, save_analysis_results


def find_run_directories(base_dir: Path = Path("runs")) -> List[Path]:
    """Find all available run directories."""
    if not base_dir.exists():
        return []

    run_dirs = []
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith("assign-cat-"):
            run_dirs.append(item)

    return sorted(run_dirs, key=lambda x: x.name, reverse=True)


def list_available_runs():
    """List all available runs for selection."""
    run_dirs = find_run_directories()

    if not run_dirs:
        print("No classification runs found in 'runs/' directory.")
        return

    print("Available Classification Runs:")
    print("=" * 50)

    for i, run_dir in enumerate(run_dirs[:10], 1):  # Show last 10 runs
        # Load run metadata if available
        metadata_file = run_dir / "metadata" / "run_summary.json"
        metadata = {}

        if metadata_file.exists():
            try:
                with open(metadata_file) as f:
                    metadata = json.load(f)
            except:
                pass

        # Check for classification results
        classifications_file = run_dir / "outputs" / "classifications.csv"
        has_results = "✅" if classifications_file.exists() else "❌"

        duration = metadata.get('duration_seconds', 'unknown')
        if isinstance(duration, (int, float)):
            duration = f"{duration:.1f}s"

        print(f"{i:2d}. {run_dir.name} {has_results}")
        print(f"    Duration: {duration}")

        if metadata.get('start_time'):
            print(f"    Started: {metadata['start_time']}")

        print()


def validate_run_directory(run_path: Path) -> bool:
    """Validate that a run directory has the required classification results."""
    if not run_path.exists():
        print(f"❌ Run directory does not exist: {run_path}")
        return False

    classifications_file = run_path / "outputs" / "classifications.csv"
    if not classifications_file.exists():
        print(f"❌ No classification results found in: {classifications_file}")
        return False

    return True


def main():
    """Main CLI entry point for reanalysis."""
    parser = argparse.ArgumentParser(
        description="Reanalyze category assignment results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available runs
  python src/reanalyze_assign_cat.py --list

  # Reanalyze latest run
  python src/reanalyze_assign_cat.py --latest

  # Reanalyze specific run
  python src/reanalyze_assign_cat.py --run runs/assign-cat-2025-09-20-071756

  # Run only specific analyses
  python src/reanalyze_assign_cat.py --latest --analyses assignment_histogram category_distribution

  # Save with custom suffix
  python src/reanalyze_assign_cat.py --latest --suffix "_v2"
        """
    )

    parser.add_argument("--list", action="store_true",
                       help="List available classification runs")
    parser.add_argument("--latest", action="store_true",
                       help="Reanalyze the most recent run")
    parser.add_argument("--run", help="Specific run directory to reanalyze")
    parser.add_argument("--analyses", nargs="+",
                       help="Specific analyses to run (default: all)")
    parser.add_argument("--suffix", default="",
                       help="Suffix to add to analysis output files")
    parser.add_argument("--version", default="1.0",
                       help="Analysis engine version to use")

    args = parser.parse_args()

    # Handle list command
    if args.list:
        list_available_runs()
        return

    # Determine target run directory
    run_dir = None

    if args.latest:
        run_dirs = find_run_directories()
        if not run_dirs:
            print("❌ No classification runs found.")
            sys.exit(1)
        run_dir = run_dirs[0]  # Most recent

    elif args.run:
        run_dir = Path(args.run)
    else:
        print("❌ Must specify either --latest, --run, or --list")
        parser.print_help()
        sys.exit(1)

    # Validate run directory
    if not validate_run_directory(run_dir):
        sys.exit(1)

    print(f"🔄 Reanalyzing: {run_dir.name}")

    # Load classification results
    classifications = load_classifications_from_run(run_dir)
    if not classifications:
        print(f"❌ Failed to load classification results from: {run_dir}")
        sys.exit(1)

    print(f"📊 Loaded {len(classifications)} classification results")

    # Initialize analyzer
    analyzer = ClassificationAnalyzer(analysis_version=args.version)

    # Run analyses
    if args.analyses:
        print(f"🔍 Running specific analyses: {', '.join(args.analyses)}")
        analysis_results = analyzer.run_specific_analyses(classifications, args.analyses)
    else:
        print(f"🔍 Running all available analyses")
        available = list(analyzer.available_analyses.keys())
        print(f"    Available: {', '.join(available)}")
        analysis_results = analyzer.run_all_analyses(classifications)

    # Load run metadata for markdown report
    run_metadata = None
    metadata_file = run_dir / "metadata" / "run_summary.json"
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                run_metadata = json.load(f)
        except:
            pass

    # Save results including markdown report
    save_analysis_results(run_dir, analysis_results, args.suffix, classifications, run_metadata)

    # Report results
    successful_analyses = []
    failed_analyses = []

    for analysis_name, analysis_data in analysis_results.items():
        if analysis_name == "analysis_metadata":
            continue

        if isinstance(analysis_data, dict) and analysis_data.get("status") == "failed":
            failed_analyses.append(analysis_name)
        else:
            successful_analyses.append(analysis_name)

    print(f"\n✅ Reanalysis completed!")
    print(f"   Successful: {len(successful_analyses)} analyses")
    if successful_analyses:
        print(f"   - {', '.join(successful_analyses)}")

    if failed_analyses:
        print(f"   Failed: {len(failed_analyses)} analyses")
        print(f"   - {', '.join(failed_analyses)}")

    # Show output files
    suffix_text = f" (suffix: {args.suffix})" if args.suffix else ""
    print(f"   Output files saved to: {run_dir}/outputs/{suffix_text}")

    # Show key insights
    if "category_distribution" in analysis_results:
        cat_dist = analysis_results["category_distribution"]
        if "summary" in cat_dist:
            summary = cat_dist["summary"]
            print(f"\n📈 Key Insights:")
            print(f"   Total categories: {summary.get('total_categories', 'unknown')}")
            print(f"   Total subcategories: {summary.get('total_subcategories', 'unknown')}")
            if summary.get('top_category'):
                print(f"   Top category: {summary['top_category']} ({summary.get('top_category_count', 0)} assignments)")


if __name__ == "__main__":
    main()