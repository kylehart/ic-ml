#!/usr/bin/env python3
"""
Test script to simulate Formbricks webhook calls to the web service.
Use this to test webhook processing with real payloads without needing to submit forms.
"""
import requests
import json

# Railway production URL
WEBHOOK_URL = "https://ic-ml-production.up.railway.app/api/v1/webhook/formbricks"

# Sample payload from actual Formbricks submission (from Railway logs)
# This is Kyle's submission: "Energy & Vitality", "Men's Health"
test_payload = {
    "event": "responseFinished",
    "data": {
        "id": "cmh14h0az0no8ad0163nsndjm",
        "createdAt": "2025-10-21T22:14:48.012Z",
        "updatedAt": "2025-10-21T22:15:54.776Z",
        "surveyId": "cmf5homcz0p1kww010hzezjjp",
        "data": {
            "y4t3q9ctov2dn6qdon1kdbrq": "kyle.hart@getbetter.care",
            "dc185mu0h2xzutpzfgq8eyjy": "I'm looking for something to improve mental clarity and attention",
            "ty1zv10pffpxh2a2bymi2wz7": [
                "Energy & Vitality",
                "Men's Health"
            ],
            "iht7n48iwkoc1jc8ubnzrqi7": 3,
            "ud6nnuhrgf9trqwe8j3kibii": "stimulants such as nicotine and caffeine",
            "yru7w3e402yk8vpf1dfbw0tr": "56-65",
            "pr4jtzy9epmquvwdksj9tctb": "i excercise for energy"
        }
    }
}

def test_webhook(payload, description="Test"):
    """Send a webhook payload and print the response."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{'='*60}")

    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            print("✅ Webhook processed successfully!")
            result = response.json()
            if "response_id" in result:
                print(f"\n🔗 View results at:")
                print(f"   https://ic-ml-production.up.railway.app/results/{result['response_id']}")
        else:
            print(f"❌ Webhook failed with status {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print()

if __name__ == "__main__":
    print("🧪 Formbricks Webhook Test Script")
    print("="*60)

    # Test 1: Kyle's actual submission
    test_webhook(test_payload, "Kyle's submission (Energy & Vitality, Men's Health)")

    # Test 2: Simplified payload with single area
    test_payload_single = test_payload.copy()
    test_payload_single["data"] = test_payload["data"].copy()
    test_payload_single["data"]["data"] = test_payload["data"]["data"].copy()
    test_payload_single["data"]["id"] = "test-single-area-123"
    test_payload_single["data"]["data"]["ty1zv10pffpxh2a2bymi2wz7"] = ["Digestive Health"]
    test_payload_single["data"]["data"]["y4t3q9ctov2dn6qdon1kdbrq"] = "test-single@example.com"

    test_webhook(test_payload_single, "Test submission (single area: Digestive Health)")

    print("\n✅ All tests completed!")
    print("\nNote: Results are stored in memory and expire after 24 hours.")
    print("Check your email for the results, or use the /results/{token} URL above.")
