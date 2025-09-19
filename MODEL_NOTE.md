# Important Note on Model Selection

The working model name for this project is:
```python
model="anthropic/claude-3-opus-20240229"
```

Previous attempts that failed:
- anthropic/claude-3-sonnet-20241022 (not found)
- anthropic/claude-2 (not found)
- anthropic/claude-sonnet-4-20250514 (not found)

The model name format is critical:
1. Must include provider prefix: "anthropic/"
2. Must use specific model version with date
3. Current working version is opus-20240229

If the model becomes unavailable in the future, check Anthropic's documentation for the latest available model version.