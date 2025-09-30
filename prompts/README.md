# Prompt Templates

This directory contains prompt templates for document generation use cases.

## taxonomy-gen-prompt.md

Specialized prompt for taxonomy generation with category definitions and ingredient lists.

**Usage:**
```bash
python src/run_taxonomy_gen.py \
  --source data/rogue-herbalist/taxonomy_trimmed.xml \
  --instructions "Your specific instructions" \
  --prompt prompts/taxonomy-gen-prompt.md \
  --model gpt4o
```

The template is prepended to the source taxonomy, providing context and structure for the LLM's generation task.
