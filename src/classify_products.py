#!/usr/bin/env python3
"""
Product Classification CLI

A command-line tool for classifying herbal products using LLMs.
Each run creates a timestamped directory containing all inputs, outputs, and logs.
"""

import argparse
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

load_dotenv()

def setup_run_directory(base_dir: str = "runs") -> Path:
    """Create timestamped run directory with required subdirectories."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(base_dir) / timestamp

    # Create directory structure
    (run_dir / "inputs").mkdir(parents=True)
    (run_dir / "config").mkdir()
    (run_dir / "outputs").mkdir()
    (run_dir / "logs").mkdir()

    return run_dir

def save_run_config(run_dir: Path, args: argparse.Namespace) -> None:
    """Save run configuration to JSON file."""
    config = {
        "timestamp": datetime.now().isoformat(),
        "model": args.model,
        "batch_size": args.batch_size,
        "input_files": {
            "catalog": str(args.catalog),
            "taxonomy": str(args.taxonomy)
        }
    }

    with open(run_dir / "config" / "config.json", "w") as f:
        json.dump(config, f, indent=2)

def setup_logging(run_dir: Path) -> logging.Logger:
    """Configure logging to both file and console."""
    logger = logging.getLogger("product_classifier")
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(run_dir / "logs" / "run.log")
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def copy_input_files(run_dir: Path, catalog_path: Path, taxonomy_path: Path) -> None:
    """Copy input files to run directory for reproducibility."""
    shutil.copy2(catalog_path, run_dir / "inputs" / "product_catalog.csv")
    shutil.copy2(taxonomy_path, run_dir / "inputs" / "taxonomy.xml")

def main(args: Optional[argparse.Namespace] = None) -> None:
    if args is None:
        parser = argparse.ArgumentParser(description="Classify herbal products using LLM")
        parser.add_argument("--catalog", type=Path, required=True,
                          help="Path to product catalog CSV")
        parser.add_argument("--taxonomy", type=Path, required=True,
                          help="Path to taxonomy XML")
        parser.add_argument("--output-dir", type=str, default="runs",
                          help="Base directory for output (default: runs)")
        parser.add_argument("--model", type=str,
                          default="anthropic/claude-3-5-sonnet-20241022",
                          help="LLM model to use")
        parser.add_argument("--batch-size", type=int, default=50,
                          help="Number of products to process in each batch")
        parser.add_argument("--prompt-template", type=Path,
                          help="Custom prompt template file")
        parser.add_argument("--dry-run", action="store_true",
                          help="Set up run directory but don't execute classification")
        args = parser.parse_args()

    # Create run directory
    run_dir = setup_run_directory(args.output_dir)
    logger = setup_logging(run_dir)
    logger.info(f"Created run directory: {run_dir}")

    # Save configuration
    save_run_config(run_dir, args)
    logger.info("Saved run configuration")

    # Copy input files
    copy_input_files(run_dir, args.catalog, args.taxonomy)
    logger.info("Copied input files")

    if args.dry_run:
        logger.info("Dry run complete - exiting")
        return

    # TODO: Implement classification logic
    logger.info("Starting classification")

if __name__ == "__main__":
    main()