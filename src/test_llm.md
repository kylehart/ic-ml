# LiteLLM Test Implementation

A basic test program to verify LiteLLM integration with Anthropic's Claude.

## Configuration
- Model: `anthropic/claude-3-5-sonnet-20241022`
- API key: Loaded from `.env` file
- Client tracking metadata:
  - client: "rogue_herbalist"
  - business: "get_better_care"

## Components
- `dotenv`: Environment variable management
- `litellm.completion`: Main interface for LLM calls
- System prompt: Herbalist assistant role
- Test query: Basic herbal classification capability check

## Key Findings
- Successful API connection
- Model responds appropriately to herbal domain questions
- Metadata properly configured for usage tracking

## Code Location
`src/test_llm.py`

## Note
This is a minimal test implementation focused on verifying:
1. API connectivity
2. Model access
3. Environment setup
4. Usage tracking