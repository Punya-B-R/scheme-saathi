#!/usr/bin/env python3
"""
Scheme Saathi backend health check script.
Run from the backend directory: python check_backend.py [--api] [--base-url URL]
- Without --api: checks data, config, and services only (no server needed).
- With --api: also hits the running server (default http://127.0.0.1:8000).

Note: First run may take 1-2 minutes while ChromaDB indexes schemes.
"""

import argparse
import sys
from pathlib import Path

# Ensure backend root is on path
BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def check_config() -> bool:
    print("\n1. Config")
    try:
        from app.config import settings
        ok(f"Settings loaded (app: {settings.APP_NAME})")
        ok(f"Schemes path: {settings.get_schemes_path(BACKEND_ROOT)}")
        ok(f"Chroma path: {settings.get_chroma_path(BACKEND_ROOT)}")
        return True
    except Exception as e:
        fail(f"Config: {e}")
        return False


def check_data_loader() -> bool:
    print("\n2. Data loader")
    try:
        from app.config import settings
        from app.utils.data_loader import get_schemes_list, get_metadata

        path = settings.get_schemes_path(BACKEND_ROOT)
        if not path.exists():
            fail(f"File not found: {path}")
            return False
        ok(f"Data file exists: {path.name}")

        schemes = get_schemes_list(path)
        meta = get_metadata(path)
        ok(f"Schemes loaded: {len(schemes)}")
        if meta:
            ok(f"Metadata: total_schemes={meta.get('total_schemes', '?')}, keys={list(meta.keys())[:4]}")

        if not schemes:
            fail("No schemes in file")
            return False
        s = schemes[0]
        for key in ("scheme_id", "scheme_name", "category", "brief_description"):
            if key not in s:
                fail(f"Missing key in scheme: {key}")
                return False
        ok("Scheme structure OK (scheme_id, scheme_name, category, brief_description)")
        return True
    except Exception as e:
        fail(f"Data loader: {e}")
        return False


def check_services() -> bool:
    print("\n3. Services (RAG + Gemini)")
    try:
        from app.services.rag_service import rag_service
        from app.services.gemini_service import gemini_service

        total = rag_service.get_total_schemes()
        ok(f"RAGService loaded ({total} schemes)")

        results = rag_service.search_schemes("farmer loan", top_k=3)
        ok(f"RAG search works (got {len(results)} results for 'farmer loan')")

        if getattr(gemini_service, "generate_reply", None):
            ok("GeminiService available")
        else:
            fail("GeminiService.generate_reply missing")
            return False
        return True
    except Exception as e:
        fail(f"Services: {e}")
        return False


def check_api(base_url: str) -> bool:
    print(f"\n4. API (GET/POST @ {base_url})")
    try:
        import httpx
    except ImportError:
        fail("httpx not installed (pip install httpx)")
        return False

    base = base_url.rstrip("/")
    all_ok = True

    # Health
    try:
        r = httpx.get(f"{base}/health", timeout=10.0)
        if r.status_code != 200:
            fail(f"GET /health -> {r.status_code}")
            all_ok = False
        else:
            data = r.json()
            ok(f"GET /health -> {r.status_code} (total_schemes={data.get('total_schemes', '?')})")
    except Exception as e:
        fail(f"GET /health: {e}")
        all_ok = False

    # Categories
    try:
        r = httpx.get(f"{base}/schemes/categories", timeout=10.0)
        if r.status_code != 200:
            fail(f"GET /schemes/categories -> {r.status_code}")
            all_ok = False
        else:
            data = r.json()
            cats = data.get("categories", [])
            ok(f"GET /schemes/categories -> {len(cats)} categories")
    except Exception as e:
        fail(f"GET /schemes/categories: {e}")
        all_ok = False

    # Search
    try:
        r = httpx.post(
            f"{base}/search",
            json={"query": "scholarship for students", "top_k": 5},
            timeout=15.0,
        )
        if r.status_code != 200:
            fail(f"POST /search -> {r.status_code}")
            all_ok = False
        else:
            data = r.json()
            n = data.get("total_matches", 0)
            ok(f"POST /search -> {r.status_code} ({n} matches)")
    except Exception as e:
        fail(f"POST /search: {e}")
        all_ok = False

    # Chat
    try:
        r = httpx.post(
            f"{base}/chat",
            json={"message": "What schemes are there for farmers?"},
            timeout=30.0,
        )
        if r.status_code != 200:
            fail(f"POST /chat -> {r.status_code} ({r.text[:80] if r.text else ''})")
            all_ok = False
        else:
            data = r.json()
            reply_len = len(data.get("reply", ""))
            suggested = len(data.get("suggested_schemes", []))
            ok(f"POST /chat -> {r.status_code} (reply len={reply_len}, suggested={suggested})")
    except Exception as e:
        fail(f"POST /chat: {e}")
        all_ok = False

    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Scheme Saathi backend health check")
    parser.add_argument(
        "--api",
        action="store_true",
        help="Also test running API (server must be up)",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL when using --api (default: http://127.0.0.1:8000)",
    )
    args = parser.parse_args()

    print("Scheme Saathi backend check")
    print("=" * 50)

    results = []
    results.append(("Config", check_config()))
    results.append(("Data loader", check_data_loader()))
    results.append(("Services", check_services()))

    if args.api:
        results.append(("API", check_api(args.base_url)))
    else:
        print("\n4. API")
        print("  (skipped; run with --api to test server, e.g. uvicorn app.main:app --port 8000)")

    print("\n" + "=" * 50)
    passed = sum(1 for _, v in results if v)
    total = len(results)
    if passed == total:
        print(f"All {total} checks passed.")
        sys.exit(0)
    else:
        print(f"Passed: {passed}/{total}. Failed: {[n for n, v in results if not v]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
