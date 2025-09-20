"""
Product catalog reader and batch processor.
"""

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional

@dataclass
class Product:
    """Product data container."""
    id: str
    title: str
    description: str
    ingredients: List[str]

    @classmethod
    def from_csv_row(cls, row: dict) -> 'Product':
        """Create Product instance from CSV row."""
        # Handle different CSV formats
        # Standard format: id, title, description, ingredients
        # Rogue Herbalist format: ﻿ID, Name, Short description, Description

        # Map field names (remove BOM if present)
        clean_row = {k.strip('\ufeff'): v for k, v in row.items()}

        # Try standard format first
        if 'id' in clean_row:
            return cls(
                id=clean_row['id'],
                title=clean_row['title'],
                description=clean_row['description'],
                ingredients=clean_row.get('ingredients', '').split(',') if clean_row.get('ingredients') else []
            )

        # Handle Rogue Herbalist format
        elif 'ID' in clean_row:
            # Extract ingredients from description text (basic extraction)
            description = clean_row.get('Short description', '') + ' ' + clean_row.get('Description', '')

            return cls(
                id=clean_row['ID'],
                title=clean_row['Name'],
                description=description.strip(),
                ingredients=[]  # No explicit ingredients in this format
            )

        else:
            raise ValueError(f"Unrecognized CSV format. Available fields: {list(clean_row.keys())}")

class ProductCatalogReader:
    """Reads and streams products from catalog CSV."""

    def __init__(self, catalog_path: Path, batch_size: int = 50):
        self.catalog_path = catalog_path
        self.batch_size = batch_size
        self.logger = logging.getLogger("product_processor")

    def read_products(self) -> Iterator[List[Product]]:
        """Generate batches of products from catalog."""
        current_batch: List[Product] = []

        try:
            with open(self.catalog_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        product = Product.from_csv_row(row)
                        current_batch.append(product)

                        if len(current_batch) >= self.batch_size:
                            self.logger.info(
                                f"Yielding batch of {len(current_batch)} products"
                            )
                            yield current_batch
                            current_batch = []

                    except Exception as e:
                        self.logger.error(f"Error processing row: {row}")
                        self.logger.error(f"Error details: {str(e)}")
                        continue

                # Don't forget the last partial batch
                if current_batch:
                    self.logger.info(
                        f"Yielding final batch of {len(current_batch)} products"
                    )
                    yield current_batch

        except Exception as e:
            self.logger.error(f"Error reading catalog: {str(e)}")
            raise

class BatchProcessor:
    """Manages product batch processing."""

    def __init__(self,
                 catalog_path: Path,
                 batch_size: int = 50,
                 max_retries: int = 3):
        self.reader = ProductCatalogReader(catalog_path, batch_size)
        self.max_retries = max_retries
        self.logger = logging.getLogger("batch_processor")

    def process_catalog(self, process_fn) -> None:
        """
        Process entire catalog using provided processing function.

        Args:
            process_fn: Function that takes List[Product] and returns results
        """
        total_processed = 0

        for batch in self.reader.read_products():
            retry_count = 0
            while retry_count < self.max_retries:
                try:
                    results = process_fn(batch)
                    total_processed += len(batch)
                    self.logger.info(
                        f"Successfully processed batch. "
                        f"Total processed: {total_processed}"
                    )
                    break
                except Exception as e:
                    retry_count += 1
                    self.logger.error(
                        f"Error processing batch (attempt {retry_count}): {str(e)}"
                    )
                    if retry_count >= self.max_retries:
                        self.logger.error("Max retries exceeded for batch")
                        raise