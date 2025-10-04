"""Quick API Test - Simple validation of all endpoints"""

import requests

BASE_URL = "http://localhost:8000"
passed = 0
failed = 0

def test(method, endpoint, desc):
    global passed, failed
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            r = requests.get(url, timeout=3)
        elif method == "POST":
            r = requests.post(url, json={}, timeout=3)

        if r.status_code < 500:
            passed += 1
            print(f"[OK] {desc}")
            return True
        else:
            failed += 1
            print(f"[FAIL] {desc} - Status {r.status_code}")
            return False
    except Exception as e:
        failed += 1
        print(f"[ERROR] {desc} - {str(e)[:50]}")
        return False

print("="*60)
print("Quick API Test")
print("="*60)

# Health
test("GET", "/docs", "API Documentation")

# Images
test("GET", "/api/images", "List Images")
test("GET", "/api/images/1", "Get Image (may 404 if no data)")

# Annotations
test("GET", "/api/annotations/1", "Get Annotations")

# Review
test("GET", "/api/review/queue", "Review Queue")

# Export
test("GET", "/api/export/formats", "Export Formats")
test("GET", "/api/export/statistics", "Export Statistics")
test("GET", "/api/export/coco?split=all", "Export COCO")

# Templates
test("GET", "/api/templates", "List Templates")

# SAM
test("GET", "/api/sam/status", "SAM Status")

print("="*60)
print(f"Results: {passed} passed, {failed} failed")
print("="*60)
