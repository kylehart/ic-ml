"""
Builds LLM context for product classification.
"""

from pathlib import Path
from typing import List, Dict

from product_processor import Product

class ContextBuilder:
    def __init__(self, taxonomy_path: Path):
        """Initialize with taxonomy file."""
        self.taxonomy = taxonomy_path.read_text()

    def build_messages(self, product: Product) -> List[Dict[str, str]]:
        """Build message list for LLM API call."""
        return [
            {
                "role": "system",
                "content": (
                    "You are a product classification expert. Analyze products "
                    "and assign them to the most relevant categories in our taxonomy. "
                    "Consider both explicit ingredients and inferred properties. "
                    "A product can belong to multiple categories."
                )
            },
            {
                "role": "user",
                "content": f"Here is our product classification taxonomy:\n\n{self.taxonomy}"
            },
            {
                "role": "user",
                "content": (
                    f"Please classify this product:\n\n"
                    f"Title: {product.title}\n"
                    f"Description: {product.description}\n"
                    f"Ingredients: {', '.join(product.ingredients)}\n\n"
                    f"Return the classifications in CSV format with these columns:\n"
                    f"taxonomy_slug,category_slug,sub_category_slug,tag,product_id"
                )
            }
        ]

    def build_batch_messages(self, products: List[Product]) -> List[Dict[str, str]]:
        """Build message list for batch classification."""
        product_texts = []
        for p in products:
            product_texts.append(
                f"Product ID: {p.id}\n"
                f"Title: {p.title}\n"
                f"Description: {p.description}\n"
                f"Ingredients: {', '.join(p.ingredients)}"
            )

        products_content = "\n\n".join(product_texts)

        return [
            {
                "role": "system",
                "content": (
                    "You are a product classification expert. Analyze products "
                    "and assign them to the most relevant categories in our taxonomy. "
                    "Consider both explicit ingredients and inferred properties. "
                    "Each product can belong to multiple categories."
                )
            },
            {
                "role": "user",
                "content": f"Here is our product classification taxonomy:\n\n{self.taxonomy}"
            },
            {
                "role": "user",
                "content": (
                    f"Please classify these products:\n\n"
                    f"{products_content}\n\n"
                    f"Return the classifications in CSV format with these columns:\n"
                    f"taxonomy_slug,category_slug,sub_category_slug,tag,product_id"
                )
            }
        ]