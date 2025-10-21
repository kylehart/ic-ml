#!/usr/bin/env python3
"""
Extract question IDs and choice IDs from Formbricks survey structure.

Usage:
    1. Get your Formbricks API key from Settings
    2. Set environment variable: export FORMBRICKS_API_KEY=your-key-here
    3. Run: python3 extract_formbricks_ids.py

This will fetch your survey structure and generate Python code with all the correct mappings.
"""

import os
import sys
import json
import requests

# Your survey ID (from form URL)
SURVEY_ID = "cmf5homcz0p1kww010hzezjjp"
API_BASE_URL = "https://app.formbricks.com/api/v1/management"

def fetch_survey_structure(api_key: str, survey_id: str) -> dict:
    """Fetch survey structure from Formbricks API."""
    url = f"{API_BASE_URL}/surveys/{survey_id}"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    print(f"🔍 Fetching survey structure from: {url}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        sys.exit(1)

    print(f"✅ Successfully fetched survey structure")
    return response.json()


def extract_question_ids(survey: dict) -> dict:
    """Extract all question IDs with their headlines."""
    questions = {}

    for q in survey.get("questions", []):
        question_id = q.get("id")
        headline = q.get("headline", {}).get("default", "Unknown")
        question_type = q.get("type")

        questions[question_id] = {
            "headline": headline,
            "type": question_type,
            "choices": None
        }

        # Extract choices for multiple choice questions
        if "choices" in q:
            choices = {}
            for choice in q["choices"]:
                choice_id = choice.get("id")
                label = choice.get("label", {}).get("default", "Unknown")
                choices[choice_id] = label
            questions[question_id]["choices"] = choices

    return questions


def generate_python_mappings(questions: dict) -> str:
    """Generate Python code with all the correct mappings."""

    code = "# Auto-generated Formbricks ID mappings\n\n"
    code += "# Question IDs\n"

    for qid, info in questions.items():
        var_name = info['headline'].upper().replace(" ", "_").replace("?", "").replace("'", "")
        var_name = ''.join(c for c in var_name if c.isalnum() or c == '_')
        code += f'{var_name}_QUESTION_ID = "{qid}"  # {info["type"]}\n'

    code += "\n# Choice ID Mappings\n\n"

    for qid, info in questions.items():
        if info["choices"]:
            var_name = info['headline'].upper().replace(" ", "_").replace("?", "").replace("'", "")
            var_name = ''.join(c for c in var_name if c.isalnum() or c == '_')
            code += f"{var_name}_CHOICES = {{\n"
            for choice_id, label in info["choices"].items():
                code += f'    "{choice_id}": "{label}",\n'
            code += "}\n\n"

    return code


def print_summary(questions: dict):
    """Print a human-readable summary."""
    print("\n" + "="*80)
    print("📋 SURVEY STRUCTURE SUMMARY")
    print("="*80 + "\n")

    for qid, info in questions.items():
        print(f"Question: {info['headline']}")
        print(f"  Type: {info['type']}")
        print(f"  ID: {qid}")

        if info["choices"]:
            print(f"  Choices:")
            for choice_id, label in info["choices"].items():
                print(f"    - {label}: {choice_id}")
        print()


def main():
    api_key = os.getenv("FORMBRICKS_API_KEY")

    if not api_key:
        print("❌ Error: FORMBRICKS_API_KEY environment variable not set")
        print("\nTo get your API key:")
        print("1. Go to Formbricks → Settings")
        print("2. Generate a 'Management API Key'")
        print("3. Run: export FORMBRICKS_API_KEY=your-key-here")
        print("4. Run this script again")
        sys.exit(1)

    # Fetch survey structure
    survey = fetch_survey_structure(api_key, SURVEY_ID)

    # Save raw JSON
    with open("formbricks_survey_structure.json", "w") as f:
        json.dump(survey, f, indent=2)
    print(f"💾 Saved raw structure to: formbricks_survey_structure.json")

    # Extract question IDs
    questions = extract_question_ids(survey)

    # Print summary
    print_summary(questions)

    # Generate Python code
    python_code = generate_python_mappings(questions)

    with open("formbricks_mappings.py", "w") as f:
        f.write(python_code)
    print("💾 Saved Python mappings to: formbricks_mappings.py")

    print("\n✅ Done! Now you can:")
    print("1. Review formbricks_survey_structure.json for the complete structure")
    print("2. Copy mappings from formbricks_mappings.py to src/web_service.py")
    print("3. Update both locations (lines 367-402 and lines 1090-1118)")


if __name__ == "__main__":
    main()
