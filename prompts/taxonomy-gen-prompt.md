## TAXONOMY GENERATION PROMPT

You are an expert herbalist and health category specialist. Enhance this XML taxonomy with concise descriptions and ingredient lists.

### Character Limits (STRICT)

| Element | Limit | Notes |
|---------|-------|-------|
| Primary description | 280 chars | 2-3 sentences |
| Subcategory description | 150 chars | 1-2 sentences |

**Exceeding limits = rejected output.**

### Enhanced XML Structure

For each `<taxon>` (primary and subcategory), add:

1. **`<description>`** - Concise, consumer-friendly, benefit-focused. Write naturally; ingredient mentions are optional and should only be included if they flow naturally.
2. **`<ingredients>`** - Two lists (no descriptions):
   - `<common>`: 6-10 high-confidence herbs/compounds
   - `<other>`: 3-6 emerging/regional herbs

**Item format**: Name only - "Echinacea (Echinacea purpurea)" or "Vitamin C"

### Description Writing Guidelines

**Good descriptions focus on benefits and applications:**
- "Support your body's natural defenses during seasonal changes and times of stress."
- "Promote digestive comfort and regularity with gentle, traditional botanicals."
- "Find calm and balance during stressful times."

**Avoid forced ingredient mentions:**
- ❌ "Support your body's defenses with echinacea and elderberry"
- ✅ "Support your body's natural defenses during seasonal changes"

**If mentioning ingredients feels natural, keep it brief:**
- ✅ "Traditional adaptogens help your body handle stress more effectively."
- ✅ "Time-tested botanicals support digestive health and comfort."

The `<ingredients>` section already lists specific herbs - descriptions should focus on WHAT the category helps with, not list ingredients again.

### Complete Example

```xml
<taxon slug="immune-support" type="primary" hierarchical="true">
  <title>Immune Support & Infection Resistance</title>
  <sub-title>Natural Defenses & Seasonal Wellness</sub-title>
  <description>Strengthen your body's natural defenses during seasonal changes and times of increased exposure. Support daily resilience and overall wellness with time-tested botanicals and modern nutritional support.</description>

  <meta>
    <chebi-roles>immunomodulator,antioxidant,antimicrobial</chebi-roles>
    <npclassifier>beta-glucans,phenolic_compounds,polysaccharides</npclassifier>
    <chpa-category>immune_support</chpa-category>
    <fda-claim>Supports immune system function</fda-claim>
  </meta>

  <ingredients>
    <common>
      <item>Echinacea (Echinacea purpurea)</item>
      <item>Elderberry (Sambucus canadensis)</item>
      <item>Astragalus (Astragalus membranaceus)</item>
      <item>Reishi (Ganoderma lucidum)</item>
      <item>Turkey tail (Trametes versicolor)</item>
      <item>Vitamin C</item>
      <item>Zinc</item>
      <item>Garlic (Allium sativum)</item>
    </common>
    <other>
      <item>Cat's claw (Uncaria tomentosa)</item>
      <item>Andrographis (Andrographis paniculata)</item>
      <item>Cordyceps (Cordyceps sinensis)</item>
    </other>
  </ingredients>

  <taxon slug="daily-immune" type="subcategory">
    <title>Daily Immune Maintenance</title>
    <description>Build lasting immune resilience with gentle, daily support for year-round wellness and vitality.</description>

    <ingredients>
      <common>
        <item>Reishi (Ganoderma lucidum)</item>
        <item>Astragalus (Astragalus membranaceus)</item>
        <item>Vitamin D3</item>
      </common>
      <other>
        <item>Maitake (Grifola frondosa)</item>
      </other>
    </ingredients>
  </taxon>
</taxon>
```

### Rules

**DO:**
- Use proper XML entity encoding (&amp; for &)
- Stay within ALL character limits
- Write scannable, web-friendly content
- Place ingredients by confidence level
- Preserve slugs, titles, meta elements from source

**DON'T:**
- Add explanatory text to ingredient items
- Make medical claims or diagnose conditions
- Change source structure
- Return anything except raw XML (no markdown blocks)

### Output

Return complete enhanced taxonomy as valid XML with all taxons including concise descriptions and ingredients.

Here is the source taxonomy to enhance:
