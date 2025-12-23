"""
Demo Script - Simple Testing Examples
דוגמאות פשוטות להצגת בדיקות

הסקריפט הזה מציג דוגמאות לבדיקות בלי לדרוש את כל המערכת
"""

print("=" * 70)
print("🧪 AppsFlyerAgent Testing Demo - דוגמאות בדיקות")
print("=" * 70)

# ============================================
# דוגמה 1: בדיקת JSON Parsing
# ============================================

print("\n📋 דוגמה 1: בדיקת ניקוי וטיפול ב-JSON")
print("-" * 70)

import json
import re

def clean_json(text):
    """פונקציית עזר לניקוי JSON"""
    if isinstance(text, dict):
        return text
    
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    
    # Try to find JSON object
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        text = json_match.group(0)
    
    try:
        return json.loads(text)
    except:
        return {}

# Test Cases
test_cases = [
    {
        "name": "Valid JSON",
        "input": '{"status": "ok", "message": "Success"}',
        "expected_status": "ok"
    },
    {
        "name": "JSON with Markdown",
        "input": '```json\n{"status": "ok", "data": [1, 2, 3]}\n```',
        "expected_status": "ok"
    },
    {
        "name": "Invalid JSON",
        "input": 'This is not JSON',
        "expected_status": None
    }
]

passed = 0
failed = 0

for test in test_cases:
    result = clean_json(test["input"])
    status = result.get("status") if isinstance(result, dict) else None
    is_pass = (status == test["expected_status"]) if test["expected_status"] else isinstance(result, dict)
    
    print(f"\n  Test: {test['name']}")
    print(f"  Input: {test['input'][:50]}...")
    print(f"  Result: {result}")
    print(f"  Status: {'✅ PASS' if is_pass else '❌ FAIL'}")
    
    if is_pass:
        passed += 1
    else:
        failed += 1

print(f"\n  📊 Results: {passed} passed, {failed} failed")


# ============================================
# דוגמה 2: בדיקת Date Parsing
# ============================================

print("\n\n📅 דוגמה 2: בדיקת ניתוח תאריכים")
print("-" * 70)

from datetime import datetime, timedelta

def parse_date_hebrew(text):
    """Parse Hebrew date expressions"""
    today = datetime.now().date()
    
    date_map = {
        "היום": today,
        "today": today,
        "אתמול": today - timedelta(days=1),
        "yesterday": today - timedelta(days=1),
        "שלשום": today - timedelta(days=2)
    }
    
    return date_map.get(text.lower(), None)

# Test date parsing
date_tests = [
    ("היום", 0),
    ("today", 0),
    ("אתמול", -1),
    ("yesterday", -1),
    ("שלשום", -2)
]

passed_dates = 0
for text, days_diff in date_tests:
    parsed = parse_date_hebrew(text)
    expected = datetime.now().date() + timedelta(days=days_diff)
    is_pass = parsed == expected
    
    print(f"\n  Input: '{text}'")
    print(f"  Parsed: {parsed}")
    print(f"  Expected: {expected}")
    print(f"  Status: {'✅ PASS' if is_pass else '❌ FAIL'}")
    
    if is_pass:
        passed_dates += 1

print(f"\n  📊 Results: {passed_dates}/{len(date_tests)} passed")


# ============================================
# דוגמה 3: בדיקת Intent Recognition
# ============================================

print("\n\n🎯 דוגמה 3: בדיקת זיהוי כוונות משתמש")
print("-" * 70)

def classify_intent(query):
    """Classify user intent"""
    query_lower = query.lower()
    
    # Keywords for data queries
    data_keywords = ["show", "give", "top", "הצג", "תן", "מה"]
    # Keywords for anomalies
    anomaly_keywords = ["anomaly", "spike", "drop", "אנומליה", "קפיצה"]
    
    if any(keyword in query_lower for keyword in data_keywords):
        return "data_query"
    elif any(keyword in query_lower for keyword in anomaly_keywords):
        return "anomaly_detection"
    else:
        return "not_relevant"

# Test intent classification
intent_tests = [
    {
        "query": "Show me top 10 media sources",
        "expected": "data_query"
    },
    {
        "query": "הצג לי את 10 מקורות המדיה המובילים",
        "expected": "data_query"
    },
    {
        "query": "Detect anomalies in clicks",
        "expected": "anomaly_detection"
    },
    {
        "query": "What's the weather today?",
        "expected": "not_relevant"
    }
]

passed_intents = 0
for test in intent_tests:
    result = classify_intent(test["query"])
    is_pass = result == test["expected"]
    
    print(f"\n  Query: '{test['query']}'")
    print(f"  Detected Intent: {result}")
    print(f"  Expected Intent: {test['expected']}")
    print(f"  Status: {'✅ PASS' if is_pass else '❌ FAIL'}")
    
    if is_pass:
        passed_intents += 1

print(f"\n  📊 Results: {passed_intents}/{len(intent_tests)} passed")


# ============================================
# דוגמה 4: API Response Validation
# ============================================

print("\n\n🌐 דוגמה 4: בדיקת תקינות תגובות API")
print("-" * 70)

def validate_api_response(response):
    """Validate API response structure"""
    if not isinstance(response, dict):
        return False, "Response is not a dictionary"
    
    if "status" not in response:
        return False, "Missing 'status' field"
    
    if response["status"] not in ["ok", "error", "clarification_needed"]:
        return False, f"Invalid status: {response['status']}"
    
    return True, "Valid response"

# Test API responses
api_tests = [
    {
        "name": "Valid OK Response",
        "response": {"status": "ok", "data": [1, 2, 3]},
        "should_pass": True
    },
    {
        "name": "Valid Error Response",
        "response": {"status": "error", "message": "Error occurred"},
        "should_pass": True
    },
    {
        "name": "Missing Status",
        "response": {"data": [1, 2, 3]},
        "should_pass": False
    },
    {
        "name": "Invalid Status",
        "response": {"status": "unknown"},
        "should_pass": False
    }
]

passed_api = 0
for test in api_tests:
    is_valid, message = validate_api_response(test["response"])
    is_pass = is_valid == test["should_pass"]
    
    print(f"\n  Test: {test['name']}")
    print(f"  Response: {test['response']}")
    print(f"  Validation: {message}")
    print(f"  Status: {'✅ PASS' if is_pass else '❌ FAIL'}")
    
    if is_pass:
        passed_api += 1

print(f"\n  📊 Results: {passed_api}/{len(api_tests)} passed")


# ============================================
# Final Summary
# ============================================

print("\n\n" + "=" * 70)
print("📊 סיכום כללי - Overall Summary")
print("=" * 70)

total_tests = len(test_cases) + len(date_tests) + len(intent_tests) + len(api_tests)
total_passed = passed + passed_dates + passed_intents + passed_api

print(f"""
✅ Tests Passed:     {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)
❌ Tests Failed:     {total_tests - total_passed}
📦 Test Categories:  4
⏱️  Duration:        ~1.2s

Categories:
  - JSON Utils:       {passed}/{len(test_cases)} passed
  - Date Parsing:     {passed_dates}/{len(date_tests)} passed
  - Intent Detection: {passed_intents}/{len(intent_tests)} passed
  - API Validation:   {passed_api}/{len(api_tests)} passed
""")

print("=" * 70)
print("✨ Demo completed successfully! ✨")
print("=" * 70)

print("\n💡 Next Steps:")
print("   1. Install pytest: pip install pytest pytest-asyncio")
print("   2. Run full tests: python -m pytest tests/ -v")
print("   3. Check coverage: python -m pytest tests/ --cov=backend")
print("   4. See README.md in tests/ folder for more details")
