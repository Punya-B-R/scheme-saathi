"""
Automated API tests using FastAPI TestClient (no live server needed).
Run from backend directory: python test_api.py
"""

import sys
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def run_tests() -> bool:
    all_passed = True

    # Test 1: Root
    print("\n1. Root endpoint GET /")
    try:
        response = client.get("/")
        if response.status_code != 200:
            fail(f"status_code={response.status_code}")
            all_passed = False
        else:
            data = response.json()
            if "Scheme Saathi" not in (data.get("app") or ""):
                fail(f"app not in response: {data}")
                all_passed = False
            else:
                ok(f"status=200, app={data.get('app')}")
    except Exception as e:
        fail(str(e))
        all_passed = False

    # Test 2: Health
    print("\n2. Health check GET /health")
    try:
        response = client.get("/health")
        if response.status_code != 200:
            fail(f"status_code={response.status_code}")
            all_passed = False
        else:
            data = response.json()
            if data.get("status") not in ("healthy", "degraded"):
                fail(f"unexpected status: {data.get('status')}")
                all_passed = False
            elif data.get("total_schemes", -1) < 0:
                fail("total_schemes missing")
                all_passed = False
            else:
                ok(f"status={data.get('status')}, total_schemes={data.get('total_schemes')}")
    except Exception as e:
        fail(str(e))
        all_passed = False

    # Test 3: Chat - simple
    print("\n3. Chat - simple (POST /chat)")
    try:
        payload = {"message": "Hello", "conversation_history": []}
        response = client.post("/chat", json=payload)
        if response.status_code != 200:
            fail(f"status_code={response.status_code}, body={response.text[:200]}")
            all_passed = False
        else:
            data = response.json()
            if "message" not in data:
                fail("message missing")
                all_passed = False
            elif not isinstance(data.get("schemes"), list):
                fail("schemes not a list")
                all_passed = False
            else:
                ok(f"message length={len(data.get('message', ''))}, schemes={len(data.get('schemes', []))}")
    except Exception as e:
        fail(str(e))
        all_passed = False

    # Test 4: Chat - with context
    print("\n4. Chat - with context (POST /chat)")
    try:
        payload = {
            "message": "I'm a farmer in Bihar",
            "conversation_history": [],
        }
        response = client.post("/chat", json=payload)
        if response.status_code != 200:
            fail(f"status_code={response.status_code}")
            all_passed = False
        else:
            data = response.json()
            if "message" not in data or "schemes" not in data:
                fail("message or schemes missing")
                all_passed = False
            else:
                n = len(data.get("schemes", []))
                ok(f"status=200, schemes returned={n}")
    except Exception as e:
        fail(str(e))
        all_passed = False

    # Test 5: List schemes
    print("\n5. List schemes GET /schemes?limit=10")
    try:
        response = client.get("/schemes?limit=10")
        if response.status_code != 200:
            fail(f"status_code={response.status_code}")
            all_passed = False
        else:
            data = response.json()
            total = data.get("total", 0)
            schemes = data.get("schemes", [])
            if total != len(schemes):
                fail(f"total={total} != len(schemes)={len(schemes)}")
                all_passed = False
            elif len(schemes) > 10:
                fail(f"expected at most 10 schemes, got {len(schemes)}")
                all_passed = False
            else:
                ok(f"total={total}, len(schemes)={len(schemes)}")
    except Exception as e:
        fail(str(e))
        all_passed = False

    # Test 6: Filter by category
    print("\n6. List schemes by category GET /schemes?category=...&limit=5")
    try:
        response = client.get("/schemes?limit=5")
        if response.status_code != 200:
            fail(f"status_code={response.status_code}")
            all_passed = False
        else:
            schemes = response.json().get("schemes", [])
            cat = None
            if schemes:
                cat = schemes[0].get("category") or "Agriculture"
            else:
                cat = "Agriculture"
            r2 = client.get(f"/schemes?category={cat}&limit=5")
            if r2.status_code != 200:
                fail(f"filter status_code={r2.status_code}")
                all_passed = False
            else:
                data2 = r2.json()
                for s in data2.get("schemes", []):
                    if (s.get("category") or "").lower() != cat.lower():
                        fail(f"scheme category mismatch: {s.get('category')}")
                        all_passed = False
                        break
                else:
                    ok(f"category filter OK for category={cat}")
    except Exception as e:
        fail(str(e))
        all_passed = False

    # Test 7: Get specific scheme
    print("\n7. Get scheme by ID GET /schemes/{scheme_id}")
    try:
        r = client.get("/schemes?limit=1")
        if r.status_code != 200:
            fail("could not get scheme list")
            all_passed = False
        else:
            schemes = r.json().get("schemes", [])
            if not schemes:
                ok("skip (no schemes in DB)")
            else:
                scheme_id = schemes[0].get("scheme_id")
                if not scheme_id:
                    ok("skip (no scheme_id in first scheme)")
                else:
                    response = client.get(f"/schemes/{scheme_id}")
                    if response.status_code != 200:
                        fail(f"status_code={response.status_code}")
                        all_passed = False
                    else:
                        data = response.json()
                        if data.get("scheme_id") != scheme_id:
                            fail(f"scheme_id mismatch")
                            all_passed = False
                        else:
                            ok(f"scheme_id={scheme_id}")
    except Exception as e:
        fail(str(e))
        all_passed = False

    # Test 8: Non-existent scheme
    print("\n8. Get non-existent scheme (expect 404)")
    try:
        response = client.get("/schemes/INVALID-ID-999")
        if response.status_code != 404:
            fail(f"expected 404, got {response.status_code}")
            all_passed = False
        else:
            ok("404 as expected")
    except Exception as e:
        fail(str(e))
        all_passed = False

    return all_passed


if __name__ == "__main__":
    print("=" * 60)
    print("API ENDPOINT TESTS (TestClient)")
    print("=" * 60)
    passed = run_tests()
    print("\n" + "=" * 60)
    if passed:
        print("All tests passed.")
        sys.exit(0)
    else:
        print("Some tests failed.")
        sys.exit(1)
