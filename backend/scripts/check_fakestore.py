#!/usr/bin/env python3
"""
Check FakeStoreAPI connectivity through the backend (port 8000).
Run with: python scripts/check_fakestore.py
Ensure the backend is running: uvicorn app.main:app --reload (from backend dir).
"""

import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:8000"


def get(url: str) -> tuple[bool, dict | str]:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode()
            return True, json.loads(data) if data else {}
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()
            return False, json.loads(body) if body else str(e)
        except Exception:
            return False, str(e)
    except OSError as e:
        return False, "Backend not reachable (is it running on port 8000?): " + str(e)
    except Exception as e:
        return False, str(e)


def main():
    print("Checking FakeStoreAPI through backend ({}).".format(BASE))
    print("Ensure backend is running: cd backend && uvicorn app.main:app --reload\n")

    # 1. GET /api/fakestore/products
    ok, out = get(f"{BASE}/api/fakestore/products")
    if ok and out.get("ok") and "products" in out:
        count = out.get("count", 0)
        print("[PASS] GET /api/fakestore/products  -> {} products".format(count))
    else:
        print("[FAIL] GET /api/fakestore/products  -> {}".format(out))
        sys.exit(1)

    # 2. GET /api/fakestore/products/1
    ok, out = get(f"{BASE}/api/fakestore/products/1")
    if ok and out.get("ok") and "product" in out:
        title = out["product"].get("title", "?")[:40]
        print("[PASS] GET /api/fakestore/products/1 -> product: {}...".format(title))
    else:
        print("[FAIL] GET /api/fakestore/products/1 -> {}".format(out))
        sys.exit(1)

    # 3. GET /api/fakestore/categories
    ok, out = get(f"{BASE}/api/fakestore/categories")
    if ok and out.get("ok") and "categories" in out:
        cats = out["categories"]
        print("[PASS] GET /api/fakestore/categories -> {} categories: {}".format(len(cats), cats))
    else:
        print("[FAIL] GET /api/fakestore/categories -> {}".format(out))
        sys.exit(1)

    # 4. GET /api/fakestore/products/category/electronics
    ok, out = get(f"{BASE}/api/fakestore/products/category/electronics")
    if ok and out.get("ok") and "products" in out:
        count = out.get("count", 0)
        print("[PASS] GET /api/fakestore/products/category/electronics -> {} products".format(count))
    else:
        print("[FAIL] GET /api/fakestore/products/category/electronics -> {}".format(out))
        sys.exit(1)

    print("\nAll FakeStoreAPI endpoints OK through backend.")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
