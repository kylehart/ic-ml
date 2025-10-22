# LLM Pricing Reference

**Last Updated**: October 22, 2025
**Source**: Official vendor pricing pages + web research

---

## OpenAI Models (All Prices per 1M Tokens)

### GPT-5 Series (Released August 2025)

| Model | Input | Output | Cached Input | Context | Max Output |
|-------|-------|--------|--------------|---------|------------|
| **GPT-5** | $1.25 | $10.00 | $0.125 (90%) | 400K | 128K |
| **GPT-5 mini** | $0.25 | $2.00 | $0.025 (90%) | 400K | 128K |
| **GPT-5 nano** | $0.05 | $0.40 | $0.005 (90%) | 400K | 128K |

**Key Features:**
- 90% cache discount (best in class)
- 400K token context window
- 128K maximum output tokens
- Advanced reasoning capabilities

---

### GPT-4.1 Series (Released April 2025)

| Model | Input | Output | Cached Input | Notes |
|-------|-------|--------|--------------|-------|
| **GPT-4.1** | ~$3.00 | ~$10.00 | TBD | Latest general-purpose multimodal |
| **GPT-4.1 Mini** | ~$0.30 | ~$1.00 | TBD | Cost-effective latest |
| **GPT-4.1 Nano** | TBD | TBD | TBD | Not yet released |

**Key Features:**
- Improved coding performance
- Better instruction-following
- Enhanced long-context understanding

---

### GPT-4o Series (Current Production Standard)

| Model | Input | Output | Cached Input | Context |
|-------|-------|--------|--------------|---------|
| **GPT-4o** | $2.50 | $10.00 | N/A | 128K |
| **GPT-4o-mini** | $0.15 | $0.60 | $0.075 (50%) | 128K |

**Key Features:**
- GPT-4o-mini: Best cost/quality balance (current default)
- GPT-4o: Premium quality for taxonomy generation
- 50% cache discount on GPT-4o-mini

---

### o-Series Reasoning Models (2024-2025)

| Model | Input | Output | Cached Input | Use Case |
|-------|-------|--------|--------------|----------|
| **o4-mini** | $0.20 | $0.80 | N/A | Latest compact reasoning |
| **o3-mini** | $1.10 | $4.40 | N/A | STEM reasoning |
| **o3** | ~$15.00 | ~$60.00 | N/A | Advanced reasoning |
| **o1-mini** | $3.00 | $12.00 | N/A | Legacy (use o3-mini) |
| **o1** | $15.00 | $60.00 | N/A | Advanced reasoning |
| **o1-pro** | $150.00 | $600.00 | N/A | Extreme difficulty only |

**Key Features:**
- Chain-of-thought reasoning
- Excellent for math, coding, science
- o4-mini: Best reasoning price/performance
- o1-pro: Most expensive model (100x GPT-4o-mini)

---

### Legacy Models (Still Available)

| Model | Input | Output | Cached Input | Status |
|-------|-------|--------|--------------|--------|
| **GPT-4 Turbo** | $10.00 | $30.00 | N/A | Use GPT-4o instead |
| **GPT-3.5 Turbo** | $0.50 | $1.50 | N/A | Use GPT-4o-mini instead |

---

## Anthropic Claude Models (All Prices per 1M Tokens)

### Haiku Models (Fast & Cost-Effective)

| Model | Input | Output | Cached Input |
|-------|-------|--------|--------------|
| **Claude 3 Haiku** | $0.25 | $1.25 | $0.025 (90%) |
| **Claude 3.5 Haiku** | $0.80 | $4.00 | $0.080 (90%) |
| **Claude 4.5 Haiku** | $1.00 | $5.00 | $0.100 (90%) |

---

### Sonnet Models (Balanced)

| Model | Input | Output | Cached Input |
|-------|-------|--------|--------------|
| **Claude 3.5 Sonnet** | $3.00 | $15.00 | $0.30 (90%) |
| **Claude 4.5 Sonnet** | $3.00 | $15.00 | $0.30 (90%) |

---

### Opus Models (Premium)

| Model | Input | Output | Cached Input |
|-------|-------|--------|--------------|
| **Claude 4.1 Opus** | $15.00 | $75.00 | $1.50 (90%) |

**Key Features:**
- 90% cache discount across all models
- Batch API: 50% discount for async processing
- Excellent for complex reasoning and analysis

---

## Cost Comparison (Sorted by Input Price)

| Rank | Model | Provider | Input | Output | Best For |
|------|-------|----------|-------|--------|----------|
| 1 | **GPT-5 nano** | OpenAI | $0.05 | $0.40 | Ultra-fast classification |
| 2 | **GPT-4o-mini** | OpenAI | $0.15 | $0.60 | **Current default** |
| 3 | **o4-mini** | OpenAI | $0.20 | $0.80 | Compact reasoning |
| 4 | **Claude 3 Haiku** | Anthropic | $0.25 | $1.25 | Fast Anthropic option |
| 5 | **GPT-5 mini** | OpenAI | $0.25 | $2.00 | Fast reasoning |
| 6 | **GPT-3.5 Turbo** | OpenAI | $0.50 | $1.50 | Legacy budget |
| 7 | **Claude 3.5 Haiku** | Anthropic | $0.80 | $4.00 | Balanced speed/quality |
| 8 | **Claude 4.5 Haiku** | Anthropic | $1.00 | $5.00 | Latest fast Anthropic |
| 9 | **o3-mini** | OpenAI | $1.10 | $4.40 | STEM reasoning |
| 10 | **GPT-5** | OpenAI | $1.25 | $10.00 | Advanced reasoning flagship |
| 11 | **GPT-4o** | OpenAI | $2.50 | $10.00 | **Current premium** |
| 12 | **o1-mini** | OpenAI | $3.00 | $12.00 | Legacy reasoning |
| 13 | **Claude 3.5/4.5 Sonnet** | Anthropic | $3.00 | $15.00 | High-quality Anthropic |
| 14 | **GPT-4 Turbo** | OpenAI | $10.00 | $30.00 | Legacy premium |
| 15 | **o1 / o3** | OpenAI | $15.00 | $60.00 | Advanced reasoning |
| 16 | **Claude 4.1 Opus** | Anthropic | $15.00 | $75.00 | Premium Anthropic |
| 17 | **o1-pro** | OpenAI | $150.00 | $600.00 | Extreme difficulty |

---

## IC-ML Project Usage (October 2025)

### Current Configuration

| Use Case | Model | Cost per Run | Notes |
|----------|-------|--------------|-------|
| **Health Quiz** | gpt4o_mini | $0.00025 | 740 tokens avg |
| **Product Classification** | gpt4o_mini | $0.0015 | Per product |
| **Taxonomy Generation** | gpt4o | $0.56 | Full 87-element taxonomy |

### NEW Configuration (October 22, 2025)

| Use Case | Model | Cost per Run | Savings |
|----------|-------|--------------|---------|
| **Health Quiz** | **gpt5_mini** | $0.00042 | -68% (but better reasoning) |
| **Product Classification** | gpt4o_mini | $0.0015 | No change |
| **Taxonomy Generation** | **gpt5** | $0.40 | **+29% savings** |

**Note**: GPT-5 mini costs more per token but provides reasoning capabilities. Consider GPT-5 nano ($0.00008/quiz) for pure cost optimization.

---

## Prompt Caching Economics

### Cache Discount Rates

| Provider | Model | Normal Input | Cached Input | Discount |
|----------|-------|--------------|--------------|----------|
| OpenAI | GPT-4o-mini | $0.15 | $0.075 | 50% |
| OpenAI | GPT-5 nano | $0.05 | $0.005 | **90%** |
| OpenAI | GPT-5 mini | $0.25 | $0.025 | **90%** |
| OpenAI | GPT-5 | $1.25 | $0.125 | **90%** |
| Anthropic | All Claude models | Varies | 0.1× base | **90%** |

### Caching ROI Example (Health Quiz)

**Without caching:**
- 420 input tokens × $0.00015 = $0.000063 per quiz

**With caching (GPT-4o-mini, 400 cached tokens):**
- Cached: 400 × $0.000075 = $0.000030
- New: 20 × $0.00015 = $0.000003
- **Total: $0.000033** (47% savings)

**With caching (GPT-5, 400 cached tokens):**
- Cached: 400 × $0.000125 = $0.000050
- New: 20 × $0.00125 = $0.000025
- **Total: $0.000075** (90% savings on cached portion)

**At 100 quizzes/day for 30 days:**
- Without caching: $0.000063 × 3000 = $0.19
- With GPT-4o-mini caching: $0.099 (save $0.09/month)
- With GPT-5 caching: $0.225 (with reasoning capability)

---

## Cost Optimization Recommendations

### Immediate Actions

1. ✅ **Switch to GPT-5 for taxonomy** - 29% savings + 90% cache potential
2. ✅ **Switch to GPT-5 mini for health quiz** - Add reasoning capability
3. 📋 **Implement prompt caching** - 47-90% savings on repeated content

### Future Considerations

1. **Test GPT-5 nano for classification** - 67% cheaper than GPT-4o-mini
2. **Test o4-mini for complex reasoning** - Cheaper than o3-mini
3. **Monitor GPT-4.1 series** - Await confirmed pricing

### Model Selection Guide

| Task Type | Recommended Model | Alternative |
|-----------|------------------|-------------|
| Simple classification | GPT-5 nano | GPT-4o-mini |
| Health recommendations | **GPT-5 mini** | GPT-4o-mini |
| Complex reasoning | o4-mini | o3-mini |
| Taxonomy generation | **GPT-5** | GPT-4o |
| Maximum quality | Claude 4.5 Sonnet | GPT-5 |
| Extreme difficulty | o1-pro | Claude 4.1 Opus |

---

## Additional Resources

- OpenAI Pricing: https://openai.com/api/pricing/
- Anthropic Pricing: https://docs.anthropic.com/en/docs/about-claude/pricing
- OpenAI Prompt Caching: https://platform.openai.com/docs/guides/prompt-caching
- Anthropic Prompt Caching: https://docs.anthropic.com/claude/docs/prompt-caching

---

**Version History:**
- October 22, 2025: Initial pricing reference with all OpenAI GPT-5/o-series models
