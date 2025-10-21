# Formbricks API Integration Guide

## Overview

This document explains how to automatically extract question IDs and choice IDs from your Formbricks survey using the Management API.

## Why This Matters

Our webhook integration and prefill URL generation require exact question IDs and choice IDs. If these don't match what's in Formbricks, we get bugs like:
- Wrong fields being prefilled
- Empty values
- Wrong dropdown options selected

## The Solution: Automatic ID Extraction

### Step 1: Get Your Formbricks API Key

1. Go to **Formbricks → Settings**
2. Navigate to **API Keys** section
3. Click **Create Management API Key**
4. Copy the key (starts with `mak_...`)

### Step 2: Run the Extraction Script

```bash
cd /Users/kylehart/Documents/dev/repos/all/ic-ml

# Set your API key
export FORMBRICKS_API_KEY=mak_your_key_here

# Install requests if needed
pip install requests

# Run the script
python3 extract_formbricks_ids.py
```

### Step 3: Review the Output

The script creates three files:

**1. `formbricks_survey_structure.json`**
- Complete JSON structure from Formbricks
- Shows the full tree: survey → questions → choices
- Useful for debugging and understanding the structure

**2. `formbricks_mappings.py`**
- Python code with all ID mappings
- Ready to copy into `src/web_service.py`
- Includes both question IDs and choice ID dictionaries

**3. Console output**
- Human-readable summary
- Shows each question with its ID
- Lists all choices with their IDs

### Step 4: Update web_service.py

Copy the mappings from `formbricks_mappings.py` to **two locations** in `src/web_service.py`:

**Location 1: Webhook Handler (lines 367-402)**
```python
# Exact question ID mapping for this Formbricks form
EMAIL_QUESTION_ID = "..." # Copy from generated file
HEALTH_ISSUE_QUESTION_ID = "..."
# ... etc

# Map primary area choice IDs to readable names
PRIMARY_AREA_CHOICES = {
    # Copy from generated file
}
```

**Location 2: Prefill URL Generator (lines 1090-1118)**
```python
# Formbricks question IDs
EMAIL_QUESTION_ID = "..." # Same IDs as Location 1

# Reverse mappings for choice IDs
AREA_TO_CHOICE_ID = {
    # This is the REVERSE of PRIMARY_AREA_CHOICES
    # "Display Name": "choice_id"
}
```

## Survey Structure (Tree Representation)

```
Survey (cmf5homcz0p1kww010hzezjjp)
│
├── Question 1: Email
│   ├── id: d9klpkum9vi8x9vkunhu63fn
│   └── type: openText
│
├── Question 2: Health concern description
│   ├── id: dc185mu0h2xzutpzfgq8eyjy
│   └── type: openText
│
├── Question 3: Primary health area
│   ├── id: ty1zv10pffpxh2a2bymi2wz7
│   ├── type: multipleChoiceSingle
│   └── choices:
│       ├── Choice: "Digestive Health"
│       │   └── id: k7ly7nx8lvgwedl1yctb215y
│       ├── Choice: "Immune Support"
│       │   └── id: xugvsda3meo6onr84icgen6j
│       └── ... more choices
│
├── Question 4: Severity (1-10)
│   ├── id: iht7n48iwkoc1jc8ubnzrqi7
│   └── type: rating
│
└── ... more questions
```

## API Endpoint Reference

**Base URL:** `https://app.formbricks.com/api/v1/management`

**Get Survey by ID:**
```
GET /surveys/{surveyId}
Headers:
  x-api-key: your-api-key
```

**Response Structure:**
```json
{
  "id": "survey-id",
  "name": "Survey Name",
  "questions": [
    {
      "id": "question-id",
      "type": "openText|multipleChoiceSingle|rating|...",
      "headline": { "default": "Question text" },
      "choices": [  // Only for multiple choice questions
        {
          "id": "choice-id",
          "label": { "default": "Choice text" }
        }
      ]
    }
  ]
}
```

## Maintenance

**When to re-run the extraction:**
- After adding/removing questions in Formbricks
- After changing question text (IDs might change)
- After adding/removing dropdown choices
- After duplicating or reordering questions

**Best practice:**
- Run extraction script whenever you modify the Formbricks form
- Keep `formbricks_survey_structure.json` in version control
- Add a comment in web_service.py with the date IDs were last updated

## Troubleshooting

**"FORMBRICKS_API_KEY environment variable not set"**
- Make sure you exported the key: `export FORMBRICKS_API_KEY=mak_...`
- Check it's set: `echo $FORMBRICKS_API_KEY`

**"Error: 401 Unauthorized"**
- Your API key is invalid or expired
- Generate a new key in Formbricks Settings

**"Error: 404 Not Found"**
- Survey ID in the script doesn't match your form
- Update `SURVEY_ID` variable in `extract_formbricks_ids.py`

**Choice IDs still wrong after update**
- Make sure you updated BOTH locations in web_service.py
- Remember Location 2 needs REVERSE mapping (display name → choice ID)

## Future Enhancements

Possible improvements:
- Auto-generate the reverse mappings (don't require manual flip)
- Run as pre-commit hook to validate IDs
- Add to deployment pipeline
- Create a web UI to browse survey structure
