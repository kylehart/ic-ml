# LLM Classification Workflow Draft

## Core Process
1. Product-by-product classification
2. Context + product info provided in each prompt
3. Structured CSV output matching category_assignment format

## Prompt Components

### System Role
```
You are an expert herbalist classifier. Analyze products and assign relevant health categories.
Output format: CSV rows with taxonomy_slug,category_slug,sub_category_slug,tag,product_id
Multiple categories allowed per product.
Match both ingredients and semantic meaning.
```

### Context Block
```
Health Categories:
[definitions from taxonomy.xml]

Ingredient Associations:
[relevant ingredient-category mappings]
```

### Product Input
```
Product ID: [id]
Title: [title]
Description: [description]
Ingredients: [ingredient list]
```

## Processing Strategy
- One product per API call
- Structured output format
- Batched processing for ~800 items
- Validation of output format
- Error handling and retries

## Notes
- May need refinement based on initial results
- Consider rate limiting and cost optimization
- Format validation important for CSV output
- Consider caching taxonomy context