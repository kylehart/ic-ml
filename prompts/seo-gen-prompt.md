## SEO METADATA GENERATION PROMPT

Generate SEO metadata for a single taxonomy category or product. Return ONLY the `<seo>` block as valid XML.

### CRITICAL: Character Limit Enforcement

You MUST count characters for each field BEFORE finalizing output. Any field exceeding its limit will cause COMPLETE REJECTION of your output.

**Process for EVERY field:**
1. Draft the content
2. Count the characters (including spaces, punctuation)
3. If over limit, shorten until it fits
4. Double-check character count
5. Only then include in output

### Required Fields & HARD CHARACTER LIMITS

| Field | MAX Characters | What Gets Rejected |
|-------|----------------|-------------------|
| **focus-keyword** | **40 chars** | 41+ chars = REJECTED |
| **meta-title** | **60 chars** | 61+ chars = REJECTED |
| **meta-description** | **160 chars** | 161+ chars = REJECTED |
| **h1** | **70 chars** | 71+ chars = REJECTED |
| **og-title** | **90 chars** | 91+ chars = REJECTED |
| **og-description** | **300 chars** | 301+ chars = REJECTED |
| **keywords** | **120 chars** | 121+ chars = REJECTED |

### Field-Specific Requirements

**focus-keyword** (MAX 40 chars):
- 2-4 words only
- Example: "daily immune support supplements" (35 chars ✅)
- NOT: "daily immune support supplements for wellness" (47 chars ❌)

**meta-title** (MAX 60 chars INCLUDING " | Rogue Herbalist"):
- Brand suffix = 20 chars, leaving only 40 chars for your content
- Example: "Daily Immune Support Vitamins & Herbs | Rogue Herbalist" (58 chars ✅)
- Count carefully: Include the " | Rogue Herbalist" in your count!

**meta-description** (MAX 160 chars):
- Short sentences, mention 2-3 ingredients
- Example: "Build lasting immunity with reishi, astragalus, and vitamin D3. Gentle herbs for year-round wellness and resilience." (123 chars ✅)

**h1** (MAX 70 chars):
- Include focus keyword
- Example: "Daily Immune Maintenance Supplements for Lasting Health" (56 chars ✅)

**og-title** (MAX 90 chars):
- More engaging than meta-title
- Example: "Daily Immune Support: Build Lasting Immunity Naturally" (55 chars ✅)

**og-description** (MAX 300 chars):
- Can be longer, more conversational
- Include CTA like "Shop now" or "Discover"
- Still count characters carefully

**keywords** (MAX 120 chars TOTAL including commas and spaces):
- 5-8 keywords maximum (fewer keywords = easier to stay under 120)
- Example: "daily immune support, immune maintenance, reishi, astragalus, vitamin D3, preventative health" (95 chars ✅)
- Count the ENTIRE string including commas and spaces

### Input Element

You will receive ONE element (taxon or product) with its existing content (title, description, ingredients).

### SEO Quality Requirements

**CRITICAL - All content must be:**

1. **Natural Language**: Write for humans first, never keyword-stuff
2. **Benefit-Driven**: Use action verbs (strengthen, support, boost, balance, enhance)
3. **Ingredient-Rich**: Mention 2-4 specific ingredients in descriptions
4. **Hierarchical**:
   - Primary categories: Broader keywords (e.g., "immune support supplements")
   - Subcategories: More specific (e.g., "daily immune support supplements")
5. **Differentiated**: Each category's SEO must be unique and specific

### Focus Keyword Strategy

**Primary Category Examples:**
- "natural immune support supplements" (NOT just "immune support")
- "digestive health supplements" (NOT just "digestion")
- "stress relief supplements" (NOT just "stress")

**Subcategory Examples** (MORE SPECIFIC):
- "daily immune support supplements" (child of immune support)
- "elderberry cold and flu support" (child of immune support)
- "digestive bitters supplements" (child of digestive health)

### Canonical URL Patterns

- **Primary**: https://rogueherbalist.com/category/{slug}/
- **Subcategory**: https://rogueherbalist.com/category/{parent-slug}/{slug}/

### Example Output: Primary Category

```xml
<seo>
  <focus-keyword>natural immune support supplements</focus-keyword>
  <meta-title>Natural Immune Support Supplements | Rogue Herbalist</meta-title>
  <meta-description>Strengthen immunity with echinacea, elderberry & medicinal mushrooms. Herbal formulas for daily wellness and seasonal support.</meta-description>
  <h1>Natural Immune Support Supplements & Herbal Formulas</h1>
  <og-title>Natural Immune Support: Herbal Supplements & Formulas</og-title>
  <og-description>Discover powerful herbal immune support with echinacea, elderberry, reishi, and turkey tail mushrooms. Shop natural formulas for everyday wellness and seasonal resilience.</og-description>
  <keywords>immune support supplements, natural immune boosters, echinacea supplements, elderberry immune support, medicinal mushrooms, herbal immunity</keywords>
  <canonical-url>https://rogueherbalist.com/category/immune-support/</canonical-url>
  <schema-type>CollectionPage</schema-type>
</seo>
```

### Example Output: Subcategory

```xml
<seo>
  <focus-keyword>daily immune support supplements</focus-keyword>
  <meta-title>Daily Immune Support Vitamins & Herbs | Rogue Herbalist</meta-title>
  <meta-description>Build lasting immunity with astragalus, reishi, vitamin D3 & gentle herbs for year-round wellness and resilience.</meta-description>
  <h1>Daily Immune Maintenance Supplements</h1>
  <og-title>Daily Immune Support: Build Lasting Immunity Naturally</og-title>
  <og-description>Gentle daily immune support with adaptogenic herbs and vitamins. Perfect for consistent, long-term immune health and resilience.</og-description>
  <keywords>daily immune support, immune maintenance, astragalus supplement, reishi mushroom, immune vitamins, preventative immune support</keywords>
  <canonical-url>https://rogueherbalist.com/category/immune-support/daily-immune/</canonical-url>
  <schema-type>CollectionPage</schema-type>
</seo>
```

### Common Mistakes to Avoid

❌ **DON'T:**
- Exceed any character limits
- Keyword-stuff unnaturally
- Use generic descriptions
- Forget " | Rogue Herbalist" in meta-title
- Make og-content identical to meta-content
- Use same keywords as parent category (for subcategories)

✅ **DO:**
- Write naturally for humans
- Front-load important words
- Mention specific ingredients
- Make og-content more engaging than meta
- Differentiate subcategory keywords from parent

### BEFORE You Submit Your Output

**MANDATORY CHARACTER COUNT CHECK:**

Go through EACH field and verify:
- [ ] focus-keyword: Count chars → Must be ≤40
- [ ] meta-title: Count chars (including " | Rogue Herbalist") → Must be ≤60
- [ ] meta-description: Count chars → Must be ≤160
- [ ] h1: Count chars → Must be ≤70
- [ ] og-title: Count chars → Must be ≤90
- [ ] og-description: Count chars → Must be ≤300
- [ ] keywords: Count ENTIRE string (commas, spaces, everything) → Must be ≤120

**If ANY field is over limit, SHORTEN IT before submitting.**

Example check for keywords:
- Draft: "immune support supplements, natural immune boosters, echinacea supplements, elderberry immune support, medicinal mushrooms, herbal immunity" (145 chars) ❌ TOO LONG
- Fixed: "immune support, natural boosters, echinacea, elderberry, medicinal mushrooms, herbal immunity" (95 chars) ✅ GOOD

### Output Format

Return ONLY the `<seo>` block. No explanations. No markdown blocks. Just raw XML:

```xml
<seo>
  ...
</seo>
```
