# 🏷️ Product Assignment Examples - Tag & Taxonomy System

This directory contains practical examples showcasing the revolutionary hybrid taxonomy and tag assignment system. Each example demonstrates different approaches to product categorization and ingredient classification.

## 📂 Example Files Overview

### 1. `tag-only-example.csv` - Pure Tag Classification ⚡

**Perfect for**: Rapid ingredient classification with instant SEO benefits

```csv
tag,product_id
natural-ingredient,3671
isolated-compound,3677
synthetic-compound,3922
```

**Use this when**:
- You want to quickly classify ingredients by type
- You need instant SEO landing pages (`/tag/natural-ingredient/`)
- You're setting up FacetWP product filtering
- You want zero maintenance overhead

**Command to run**:
```bash
npm run assign:taxonomy -c examples/tag-only-example.csv
```

**Business Benefits**:
- ✅ **Instant SEO Pages**: `/tag/natural-ingredient/`, `/tag/isolated-compound/`
- ✅ **FacetWP Ready**: Works with filtering plugins out-of-the-box
- ✅ **Zero Maintenance**: WordPress handles everything automatically

---

### 2. `full-format-with-tags-example.csv` - Complete Control 📂

**Perfect for**: Complex taxonomy hierarchy + ingredient classification

```csv
taxonomy_slug,category_slug,sub_category_slug,tag,product_id
health-areas,immune-support,daily-immune,,3671
ingredients,turmeric,,natural-ingredient,3671
```

**Use this when**:
- You need both taxonomy categorization AND ingredient tagging
- You want hierarchical product organization
- You're building complex product relationships
- You need detailed categorization with sub-categories

**Command to run**:
```bash
npm run assign:taxonomy -c examples/full-format-with-tags-example.csv
```

**Advanced Features**:
- 🌳 **Hierarchical Validation**: Prevents conflicting assignments
- 🏷️ **Dual Classification**: Taxonomy + Tag in one workflow
- 📊 **Rich Metadata**: Sub-categories for deeper organization

---

### 3. `hybrid-mixed-usage-example.csv` - Best of Both Worlds 🎯

**Perfect for**: Combining simple tagging with complex categorization

```csv
taxonomy_slug,category_slug,sub_category_slug,tag,product_id
health-areas,immune-support,daily-immune,,3671
ingredients,turmeric,,natural-ingredient,3671
,,,,
ingredients,vitamin-c,,isolated-compound,3677
ingredients,zinc,,natural-ingredient,3922
```

**Use this when**:
- You have products that need both approaches
- You're gradually migrating to the new system
- You want flexibility in your assignment strategy
- You have different product types requiring different categorization

**Command to run**:
```bash
npm run assign:taxonomy -c examples/hybrid-mixed-usage-example.csv
```

**Strategic Benefits**:
- 🔄 **Flexible Migration**: Transition at your own pace
- 🎛️ **Multiple Strategies**: Use the right approach for each product
- 🔧 **Gradual Implementation**: Test new features alongside existing workflows

---

### 4. `tag-removal-example.csv` - Targeted Tag Cleanup 🗑️

**Perfect for**: Removing specific tags from individual products

```csv
tag,product_id
natural-ingredient,3671
isolated-compound,3675
synthetic-compound,3677
```

**Use this when**:
- You need to correct product classification errors
- You want to remove obsolete ingredient tags
- You're updating product categorization
- You need targeted tag cleanup

**Command to run**:
```bash
npm run assign:products -c examples/tag-removal-example.csv --remove-tags --dry-run  # Preview first
npm run assign:products -c examples/tag-removal-example.csv --remove-tags            # Apply removal
```

**Safety Features**:
- 🔍 **Always preview first** with `--dry-run`
- 🛡️ **Preserves other tags** - only removes specified tags
- 📊 **Detailed reporting** of removal operations

---

### 5. `wildcard-tag-removal-example.csv` - Catalog-Wide Cleanup ⚡

**Perfect for**: Removing tags from ALL products in your catalog

```csv
tag,product_id
natural-ingredient,*
isolated-compound,*
synthetic-compound,*
```

**Use this when**:
- You're discontinuing an ingredient classification
- You need to clean up systematic tagging errors
- You're rebranding ingredient categories
- You want to start fresh with tag assignments

**⚠️ POWERFUL WILDCARD OPERATION**:
- `*` means ALL products in your catalog
- Always test with `--dry-run` first!
- This will remove the tag from every product that has it

**Command to run**:
```bash
npm run assign:products -c examples/wildcard-tag-removal-example.csv --remove-tags --dry-run  # ESSENTIAL preview
npm run assign:products -c examples/wildcard-tag-removal-example.csv --remove-tags            # Apply to ALL products
```

**Business Use Cases**:
- 🧹 **Systematic Cleanup**: Remove obsolete classification tags
- 🔄 **Rebranding**: Change ingredient categorization system
- 🎯 **Quality Control**: Fix widespread tagging errors

---

### 6. `mixed-tag-removal-example.csv` - Flexible Tag Management 🎛️

**Perfect for**: Combining specific and wildcard tag removal operations

```csv
taxonomy_slug,category_slug,sub_category_slug,tag,product_id
,,,,3671
,,,,3675
ingredients,turmeric,,natural-ingredient,3677
ingredients,ginger,,isolated-compound,3922
,,,,*
```

**Use this when**:
- You need both specific and wildcard operations
- You're doing complex tag management
- You want maximum flexibility in one file
- You're performing mixed cleanup operations

**Command to run**:
```bash
npm run assign:products -c examples/mixed-tag-removal-example.csv --remove-tags --dry-run
npm run assign:products -c examples/mixed-tag-removal-example.csv --remove-tags
```

---

### 7. `migration-old-to-new-format.csv` - Upgrade Your Data 📈

**Perfect for**: Migrating existing ingredient assignments to include tags

```csv
taxonomy_slug,category_slug,sub_category_slug,tag,product_id
ingredients,turmeric,,natural-ingredient,3671
ingredients,vitamin-d3,,isolated-compound,3675
ingredients,ibuprofen,,synthetic-compound,3922
```

**Use this when**:
- You have existing ingredient taxonomy assignments
- You want to add tag classification to existing data
- You're upgrading from the old 3-column format
- You need to maintain existing categorization while adding tags

**Migration Process**:
1. Export your existing `ingredients` taxonomy assignments
2. Add the `tag` column with appropriate ingredient classifications
3. Run the assignment to add tags while keeping existing categories

**Command to run**:
```bash
npm run assign:taxonomy -c examples/migration-old-to-new-format.csv
```

---

## 🚀 Quick Start Guide

### Step 1: Choose Your Approach

**For Simple Ingredient Tagging**:
```bash
cp examples/tag-only-example.csv my-tags.csv
# Edit with your product IDs and run:
npm run assign:taxonomy -c my-tags.csv
```

**For Complete Product Organization**:
```bash
cp examples/full-format-with-tags-example.csv my-assignments.csv
# Edit with your data and run:
npm run assign:taxonomy -c my-assignments.csv
```

**For Tag Removal Operations**:
```bash
# Specific product tag removal
cp examples/tag-removal-example.csv my-removals.csv
npm run assign:products -c my-removals.csv --remove-tags --dry-run

# Wildcard catalog cleanup
cp examples/wildcard-tag-removal-example.csv cleanup.csv
npm run assign:products -c cleanup.csv --remove-tags --dry-run  # ALWAYS preview first!
```

### Step 2: Test First

Always validate before applying:
```bash
npm run assign:taxonomy -c your-file.csv --dry-run
```

### Step 3: Apply Changes

```bash
npm run assign:taxonomy -c your-file.csv
```

## 🏷️ Valid Ingredient Tags

| Tag | Type | Auto-Generated URL | Example Products |
|-----|------|--------------------|------------------|
| `natural-ingredient` | Plant, fungus, mineral | `/tag/natural-ingredient/` | Turmeric, Ginger, Ashwagandha |
| `isolated-compound` | Extracted substances | `/tag/isolated-compound/` | Vitamin D3, CoQ10, Curcumin Extract |
| `synthetic-compound` | Lab-created molecules | `/tag/synthetic-compound/` | Ibuprofen, Synthetic Vitamins |

## 📊 Business Impact Examples

### E-commerce Store Benefits

**Before Tags**: Products scattered across custom taxonomies
**After Tags**:
- Customers browse `/tag/natural-ingredient/` for plant-based products
- SEO improved with automatic landing pages
- FacetWP filtering by ingredient type
- Content marketing via tag archive pages

### SEO Landing Page Examples

After running assignments, you'll get automatic pages like:
- `yoursite.com/tag/natural-ingredient/` - All natural ingredient products
- `yoursite.com/tag/isolated-compound/` - All extracted compound products
- `yoursite.com/tag/synthetic-compound/` - All synthetic products

### FacetWP Integration

Tags work immediately with FacetWP:
```javascript
// FacetWP automatically detects product tags
// No additional configuration needed!
```

## 🛠️ Advanced Usage

### Generate Statistics
```bash
npm run assign:taxonomy -c examples/tag-only-example.csv --stats
```

### Validate Complex Files
```bash
npm run assign:taxonomy -c examples/full-format-with-tags-example.csv --validate
```

### Preview Changes
```bash
npm run assign:taxonomy -c examples/hybrid-mixed-usage-example.csv --dry-run --verbose
```

## 💡 Pro Tips

1. **Start with Tag-Only**: Begin with simple ingredient tagging for immediate SEO benefits
2. **Migrate Gradually**: Use hybrid approach to transition existing data
3. **Test First**: Always use `--dry-run` before applying changes
4. **Monitor Results**: Check WordPress admin and front-end tag pages
5. **Plan Content**: Use tag pages for ingredient education content

## 🔍 Troubleshooting

**Tag not appearing?**
- Check that product exists and is published
- Verify tag slug spelling
- Ensure WordPress permalinks are refreshed

**SEO page not working?**
- Refresh permalinks in WordPress admin
- Check theme supports tag archive pages
- Verify .htaccess is writable

**FacetWP not showing tags?**
- Refresh FacetWP index
- Ensure facet is configured for product tags
- Check cache plugins aren't interfering

---

## 🎯 Next Steps

1. **Choose an example** that matches your use case
2. **Copy and customize** with your product IDs
3. **Test with --dry-run** to preview changes
4. **Apply assignments** and check results
5. **Set up FacetWP** for enhanced filtering
6. **Create tag page content** for SEO benefits

This hybrid system revolutionizes product organization by combining the power of hierarchical taxonomies with the SEO benefits of WordPress native tags! 🚀