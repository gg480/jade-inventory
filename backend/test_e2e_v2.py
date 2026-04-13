#!/usr/bin/env python3
"""
Comprehensive E2E API Test Suite for Jade Inventory Management System.

Tests the full business flow:
  1. Login (JWT auth)
  2. Dashboard summary
  3. Create supplier
  4. Create customer
  5. Get materials (dicts)
  6. Create high-value item (single item, no batch)
  7. List items (verify creation)
  8. Create sale (single item sale)
  9. List sales (verify sale record)
  10. Create batch (batch goods)
  11. Add items to batch (x3)
  12. Allocate batch cost
  13. Get batch detail (verify allocation)

All tests use the `requests` library with detailed output and error handling.
"""

import json
import os
import subprocess
import sys
import time
import traceback
from datetime import date, timedelta

import requests

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000/api/v1")
LOGIN_PASSWORD = "admin123"
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8000"))

# Unique test identifiers to avoid collisions on re-runs
TEST_RUN_ID = f"{date.today().strftime('%m%d')}T{int(time.time()) % 100000}"  # e.g. "0612T83721"
SUPPLIER_NAME = f"E2E供应商{TEST_RUN_ID}"
CUSTOMER_NAME = f"E2E客户{TEST_RUN_ID}"
HIGH_VALUE_ITEM_NAME = f"E2E高货A-{TEST_RUN_ID}"
BATCH_CODE = f"E2E-BATCH-{TEST_RUN_ID}"


# ── Helpers ────────────────────────────────────────────────────────────────────
class TestResult:
    """Holds the outcome of a single test step."""
    def __init__(self, step: int, name: str):
        self.step = step
        self.name = name
        self.passed = False
        self.status_code = None
        self.error = None
        self.response_body = None
        self.request_info = None
        self.duration_ms = 0

    def __str__(self):
        icon = "PASS" if self.passed else "FAIL"
        status = f"HTTP {self.status_code}" if self.status_code else "N/A"
        detail = ""
        if self.error:
            detail = f" | Error: {self.error}"
        return f"  [{icon}] Step {self.step}: {self.name} ({status}, {self.duration_ms}ms){detail}"


results: list[TestResult] = []
token: str = ""
headers_auth: dict = {}

# Collected IDs from previous steps
first_material_id: int = None
created_item_id: int = None
created_customer_id: int = None
created_batch_id: int = None
batch_item_ids: list = []


def api(method: str, path: str, **kwargs) -> requests.Response:
    """Make an API request with optional auth, return Response."""
    url = f"{BASE_URL}{path}"
    if headers_auth:
        kwargs.setdefault("headers", {}).update(headers_auth)
    return requests.request(method, url, **kwargs)


def run_step(step: int, name: str, test_fn):
    """Execute a test step and record the result."""
    print(f"\n{'='*70}")
    print(f"  Step {step}: {name}")
    print(f"{'='*70}")
    result = TestResult(step, name)
    try:
        import time
        t0 = time.time()
        test_fn(result)
        result.duration_ms = int((time.time() - t0) * 1000)
    except Exception as e:
        result.passed = False
        result.error = f"{type(e).__name__}: {e}"
        result.duration_ms = 0
        traceback.print_exc()

    results.append(result)
    print(f"\n  >>> Result: {'PASS' if result.passed else 'FAIL'} "
          f"(HTTP {result.status_code}, {result.duration_ms}ms)")
    if result.response_body:
        # Truncate very large responses
        body_str = json.dumps(result.response_body, ensure_ascii=False, indent=2)
        if len(body_str) > 1500:
            body_str = body_str[:1500] + "\n  ... (truncated)"
        print(f"  >>> Response body:\n{body_str}")
    return result


def check(result: TestResult, response: requests.Response, expected_status_codes=None):
    """Check HTTP status and record response. Sets result.passed accordingly."""
    if expected_status_codes is None:
        expected_status_codes = [200, 201]
    result.status_code = response.status_code
    try:
        result.response_body = response.json()
    except Exception:
        result.response_body = response.text

    if response.status_code in expected_status_codes:
        # Also check that the API's internal code is 0 (success)
        body = result.response_body
        if isinstance(body, dict) and body.get("code", 0) != 0 and response.status_code in [200, 201]:
            result.passed = False
            result.error = f"API returned code={body.get('code')}, message={body.get('message')}"
        else:
            result.passed = True
    else:
        result.passed = False
        body = result.response_body
        msg = body.get("message", body.get("detail", response.text)) if isinstance(body, dict) else str(body)
        result.error = msg
    return result.passed


# ── Test Steps ─────────────────────────────────────────────────────────────────

def test_step_1_login(result: TestResult):
    """POST /auth/login — Get JWT token."""
    payload = {"password": LOGIN_PASSWORD}
    print(f"  POST /auth/login  body={json.dumps(payload, ensure_ascii=False)}")
    resp = api("POST", "/auth/login", json=payload)
    check(result, resp, expected_status_codes=[200])

    if result.passed:
        data = result.response_body.get("data", {})
        global token
        token = data.get("token")
        if not token:
            result.passed = False
            result.error = "No token in response data"
            return
        global headers_auth
        headers_auth = {"Authorization": f"Bearer {token}"}
        print(f"  Token received: {token[:20]}...")
        must_change = data.get("must_change_password", False)
        if must_change:
            print(f"  WARNING: must_change_password=True (default password in use)")
    else:
        print(f"  Login failed! Cannot proceed with authenticated tests.")


def test_step_2_dashboard(result: TestResult):
    """GET /dashboard/summary — Get dashboard overview."""
    print(f"  GET /dashboard/summary  (Bearer token)")
    resp = api("GET", "/dashboard/summary")
    check(result, resp, expected_status_codes=[200])

    if result.passed:
        data = result.response_body.get("data", {})
        print(f"  Dashboard: total_items={data.get('total_items')}, "
              f"stock_value={data.get('total_stock_value')}, "
              f"month_revenue={data.get('month_revenue')}, "
              f"month_profit={data.get('month_profit')}, "
              f"month_sold={data.get('month_sold_count')}")


def test_step_3_create_supplier(result: TestResult):
    """POST /suppliers — Create a test supplier."""
    payload = {"name": SUPPLIER_NAME, "contact": "13800138000"}
    print(f"  POST /suppliers  body={json.dumps(payload, ensure_ascii=False)}")
    resp = api("POST", "/suppliers", json=payload)
    check(result, resp, expected_status_codes=[201])

    if result.passed:
        data = result.response_body.get("data", {})
        print(f"  Supplier created: id={data.get('id')}, name={data.get('name')}")
    else:
        # Might already exist from a previous run
        msg = result.error or ""
        if "已存在" in msg:
            print(f"  INFO: Supplier already exists (from previous test run). Treating as PASS.")
            result.passed = True
            result.error = None


def test_step_4_create_customer(result: TestResult):
    """POST /customers — Create a test customer."""
    global created_customer_id
    payload = {"name": CUSTOMER_NAME, "phone": "13900139000"}
    print(f"  POST /customers  body={json.dumps(payload, ensure_ascii=False)}")
    resp = api("POST", "/customers", json=payload)
    check(result, resp, expected_status_codes=[201])

    if result.passed:
        data = result.response_body.get("data", {})
        created_customer_id = data.get("id")
        print(f"  Customer created: id={created_customer_id}, code={data.get('customer_code')}")
    else:
        msg = result.error or ""
        if "已存在" in msg:
            print(f"  INFO: Customer already exists (from previous test run). Trying to find it...")
            # Try to find the existing customer
            resp2 = api("GET", "/customers", params={"name": CUSTOMER_NAME})
            if resp2.status_code == 200:
                items = resp2.json().get("data", {}).get("items", [])
                if items:
                    created_customer_id = items[0]["id"]
                    print(f"  Found existing customer: id={created_customer_id}")
                    result.passed = True
                    result.error = None


def test_step_5_get_materials(result: TestResult):
    """GET /dicts/materials — Get material dictionary list."""
    global first_material_id
    print(f"  GET /dicts/materials")
    resp = api("GET", "/dicts/materials")
    check(result, resp, expected_status_codes=[200])

    if result.passed:
        data = result.response_body.get("data", [])
        print(f"  Materials count: {len(data)}")
        if data:
            first_material_id = data[0]["id"]
            print(f"  First material: id={first_material_id}, name={data[0].get('name')}")
            # Print all for reference
            for m in data:
                print(f"    - id={m['id']}, name={m['name']}, sub_type={m.get('sub_type')}, active={m.get('is_active')}")
        else:
            result.passed = False
            result.error = "No materials found in dictionary — cannot proceed with item creation"


def test_step_6_create_high_value_item(result: TestResult):
    """POST /items — Create a single high-value item (no batch)."""
    global created_item_id
    if not first_material_id:
        result.passed = False
        result.error = "No material_id available (Step 5 failed)"
        return

    payload = {
        "material_id": first_material_id,
        "cost_price": 1000,
        "selling_price": 2000,
        "name": HIGH_VALUE_ITEM_NAME,
    }
    print(f"  POST /items  body={json.dumps(payload, ensure_ascii=False)}")
    resp = api("POST", "/items", json=payload)
    check(result, resp, expected_status_codes=[201])

    if result.passed:
        data = result.response_body.get("data", {})
        created_item_id = data.get("id")
        print(f"  Item created: id={created_item_id}, sku={data.get('sku_code')}, "
              f"cost={data.get('cost_price')}, selling={data.get('selling_price')}, "
              f"allocated_cost={data.get('allocated_cost')}, status={data.get('status')}")

        # Validate: for high-value item (no batch), allocated_cost should equal cost_price
        if data.get("allocated_cost") != data.get("cost_price"):
            print(f"  WARNING: allocated_cost ({data.get('allocated_cost')}) != cost_price ({data.get('cost_price')})")
            print(f"  For high-value items, allocated_cost should equal cost_price")
    else:
        msg = result.error or ""
        if "SKU" in msg and "已存在" in msg:
            print(f"  INFO: SKU already exists (from previous run). Trying to find item...")
            resp2 = api("GET", "/items", params={"keyword": HIGH_VALUE_ITEM_NAME})
            if resp2.status_code == 200:
                items = resp2.json().get("data", {}).get("items", [])
                for item in items:
                    if item.get("name") == HIGH_VALUE_ITEM_NAME and item.get("status") == "in_stock":
                        created_item_id = item["id"]
                        print(f"  Found existing item: id={created_item_id}, sku={item.get('sku_code')}")
                        result.passed = True
                        result.error = None
                        break


def test_step_7_list_items(result: TestResult):
    """GET /items — List items and verify the high-value item was created."""
    print(f"  GET /items?page=1&size=5")
    resp = api("GET", "/items", params={"page": 1, "size": 5})
    check(result, resp, expected_status_codes=[200])

    if result.passed:
        data = result.response_body.get("data", {})
        items = data.get("items", [])
        pagination = data.get("pagination", {})
        print(f"  Items returned: {len(items)}, total={pagination.get('total')}, pages={pagination.get('pages')}")

        # Check if our created item is in the list
        found = False
        for item in items:
            if item.get("id") == created_item_id:
                found = True
                print(f"  Found our item: id={item['id']}, sku={item.get('sku_code')}, name={item.get('name')}")
                print(f"    cost={item.get('cost_price')}, selling={item.get('selling_price')}, "
                      f"status={item.get('status')}")
                break

        if not found:
            print(f"  WARNING: Created item (id={created_item_id}) not in first page. "
                  f"It may be on a later page or the list is sorted by created_at desc.")


def test_step_8_create_sale(result: TestResult):
    """POST /sales — Create a single-item sale."""
    global created_item_id
    if not created_item_id:
        result.passed = False
        result.error = "No item_id available (Step 6 failed)"
        return

    payload = {
        "item_id": created_item_id,
        "actual_price": 1800,
        "channel": "store",
        "sale_date": str(date.today()),
        "customer_id": created_customer_id,
        "note": "E2E测试销售",
    }
    print(f"  POST /sales  body={json.dumps(payload, ensure_ascii=False)}")
    resp = api("POST", "/sales", json=payload)
    check(result, resp, expected_status_codes=[201])

    if result.passed:
        data = result.response_body.get("data", {})
        print(f"  Sale created: id={data.get('id')}, sale_no={data.get('sale_no')}, "
              f"actual_price={data.get('actual_price')}, channel={data.get('channel')}")
        print(f"    cost={data.get('cost')}, gross_profit={data.get('gross_profit')}")
        print(f"    customer_name={data.get('customer_name')}, item_name={data.get('item_name')}")

        # Validate profit calculation
        expected_profit = 1800 - 1000  # actual_price - cost_price
        if data.get("gross_profit") != expected_profit:
            print(f"  WARNING: gross_profit={data.get('gross_profit')} != expected={expected_profit}")
    else:
        msg = result.error or ""
        if "不可销售" in msg or "已售" in msg:
            print(f"  INFO: Item already sold (from previous run). Trying to find the sale record...")
            resp2 = api("GET", "/sales", params={"item_id": created_item_id} if False else {})
            # Just list recent sales
            resp2 = api("GET", "/sales", params={"page": 1, "size": 5})
            if resp2.status_code == 200:
                items = resp2.json().get("data", {}).get("items", [])
                for sale in items:
                    if sale.get("item_id") == created_item_id:
                        print(f"  Found existing sale: id={sale['id']}, sale_no={sale.get('sale_no')}")
                        result.passed = True
                        result.error = None
                        break


def test_step_9_list_sales(result: TestResult):
    """GET /sales — List sales and verify the sale record exists."""
    print(f"  GET /sales?page=1&size=10")
    resp = api("GET", "/sales", params={"page": 1, "size": 10})
    check(result, resp, expected_status_codes=[200])

    if result.passed:
        data = result.response_body.get("data", {})
        items = data.get("items", [])
        pagination = data.get("pagination", {})
        print(f"  Sales returned: {len(items)}, total={pagination.get('total')}, pages={pagination.get('pages')}")

        # Check for errors in each sale record
        for sale in items:
            sale_no = sale.get("sale_no", "?")
            profit = sale.get("gross_profit")
            cost = sale.get("cost")
            actual = sale.get("actual_price")
            item_sku = sale.get("item_sku", "?")

            # Validate: gross_profit should equal actual_price - cost
            if cost is not None and profit is not None:
                expected_profit = round(actual - cost, 2)
                if abs(profit - expected_profit) > 0.01:
                    print(f"  BUG DETECTED: Sale {sale_no} gross_profit={profit} "
                          f"!= actual_price({actual}) - cost({cost}) = {expected_profit}")
                    result.error = f"Profit calculation error in sale {sale_no}"

            print(f"    Sale: no={sale_no}, item={item_sku}, price={actual}, "
                  f"cost={cost}, profit={profit}, channel={sale.get('channel')}")

        # Check for our specific sale
        found = False
        for sale in items:
            if sale.get("item_id") == created_item_id:
                found = True
                break
        if not found:
            print(f"  NOTE: Our sale (item_id={created_item_id}) not in first page.")


def test_step_10_create_batch(result: TestResult):
    """POST /batches — Create a batch (batch goods)."""
    global created_batch_id
    if not first_material_id:
        result.passed = False
        result.error = "No material_id available (Step 5 failed)"
        return

    payload = {
        "batch_code": BATCH_CODE,
        "material_id": first_material_id,
        "quantity": 3,
        "total_cost": 3000,
        "cost_alloc_method": "equal",
    }
    print(f"  POST /batches  body={json.dumps(payload, ensure_ascii=False)}")
    resp = api("POST", "/batches", json=payload)
    check(result, resp, expected_status_codes=[201])

    if result.passed:
        data = result.response_body.get("data", {})
        created_batch_id = data.get("id")
        print(f"  Batch created: id={created_batch_id}, code={data.get('batch_code')}, "
              f"material={data.get('material_name')}, qty={data.get('quantity')}, "
              f"total_cost={data.get('total_cost')}, status={data.get('status')}")
        print(f"    items_count={data.get('items_count')}, sold_count={data.get('sold_count')}, "
              f"revenue={data.get('revenue')}, profit={data.get('profit')}")
    else:
        msg = result.error or ""
        if "已存在" in msg:
            print(f"  INFO: Batch already exists (from previous run). Trying to find it...")
            resp2 = api("GET", "/batches", params={"page": 1, "size": 50})
            if resp2.status_code == 200:
                items = resp2.json().get("data", {}).get("items", [])
                for batch in items:
                    if batch.get("batch_code") == BATCH_CODE:
                        created_batch_id = batch["id"]
                        print(f"  Found existing batch: id={created_batch_id}")
                        result.passed = True
                        result.error = None
                        break


def test_step_11_add_items_to_batch(result: TestResult):
    """POST /items x3 — Add 3 items to the batch."""
    global batch_item_ids
    if not created_batch_id or not first_material_id:
        result.passed = False
        result.error = f"No batch_id or material_id (batch_id={created_batch_id}, material_id={first_material_id})"
        return

    batch_item_ids = []
    all_passed = True

    for i in range(3):
        payload = {
            "material_id": first_material_id,
            "batch_id": created_batch_id,
            "selling_price": 1500 + i * 100,  # 1500, 1600, 1700
            "name": f"E2E通货件{i+1}-{TEST_RUN_ID}",
        }
        # IMPORTANT: For batch items, cost_price must NOT be provided
        print(f"  POST /items  [{i+1}/3] body={json.dumps(payload, ensure_ascii=False)}")
        resp = api("POST", "/items", json=payload)

        if resp.status_code == 201:
            data = resp.json().get("data", {})
            batch_item_ids.append(data.get("id"))
            print(f"    Created: id={data.get('id')}, sku={data.get('sku_code')}, "
                  f"selling={data.get('selling_price')}, cost_price={data.get('cost_price')}, "
                  f"allocated_cost={data.get('allocated_cost')}, status={data.get('status')}")

            # Validate: batch item should have cost_price=None, allocated_cost=None
            if data.get("cost_price") is not None:
                print(f"    WARNING: Batch item has cost_price={data.get('cost_price')} (expected None)")
            if data.get("allocated_cost") is not None:
                print(f"    WARNING: Batch item has allocated_cost={data.get('allocated_cost')} (expected None before allocation)")
        else:
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            msg = body.get("message", str(body)) if isinstance(body, dict) else str(body)
            print(f"    FAILED: HTTP {resp.status_code} — {msg}")
            all_passed = False

            # Check if it's a duplicate SKU
            if "SKU" in msg and "已存在" in msg:
                print(f"    INFO: SKU exists (previous run). Searching for existing batch items...")
                resp2 = api("GET", "/items", params={"batch_id": created_batch_id, "size": 10})
                if resp2.status_code == 200:
                    existing = resp2.json().get("data", {}).get("items", [])
                    batch_item_ids = [item["id"] for item in existing]
                    if len(batch_item_ids) == 3:
                        print(f"    Found 3 existing batch items: {batch_item_ids}")
                        all_passed = True
                    else:
                        print(f"    Found {len(batch_item_ids)} existing batch items (need 3)")
                break

    result.status_code = 201 if all_passed else 400
    result.passed = all_passed and len(batch_item_ids) >= 3
    if not result.passed:
        result.error = f"Could not create 3 batch items (got {len(batch_item_ids)})"
    result.response_body = {"batch_item_ids": batch_item_ids}


def test_step_12_allocate_batch_cost(result: TestResult):
    """POST /batches/{id}/allocate — Allocate batch cost to items."""
    if not created_batch_id:
        result.passed = False
        result.error = "No batch_id available"
        return

    path = f"/batches/{created_batch_id}/allocate"
    print(f"  POST {path}")
    resp = api("POST", path)
    check(result, resp, expected_status_codes=[200])

    if result.passed:
        data = result.response_body.get("data", {})
        items = data.get("items", [])
        print(f"  Allocation result: {len(items)} items")
        total_allocated = 0
        for item in items:
            sku = item.get("sku_code", "?")
            alloc_cost = item.get("allocated_cost", 0)
            floor_price = item.get("floor_price", 0)
            total_allocated += alloc_cost
            print(f"    {sku}: allocated_cost={alloc_cost}, floor_price={floor_price}")

        # Validate: equal allocation of 3000/3 = 1000 per item
        expected_per_item = round(3000 / 3, 2)
        print(f"  Total allocated: {round(total_allocated, 2)} (expected: 3000)")
        if abs(total_allocated - 3000) > 0.02:
            print(f"  BUG? Total allocated {total_allocated} != batch total_cost 3000")
            result.error = f"Allocation total mismatch: {total_allocated} != 3000"

        for item in items:
            if abs(item.get("allocated_cost", 0) - expected_per_item) > 0.02:
                print(f"  NOTE: allocated_cost={item.get('allocated_cost')} vs expected={expected_per_item}")
                break


def test_step_13_get_batch_detail(result: TestResult):
    """GET /batches/{id} — Get batch detail and verify allocation."""
    if not created_batch_id:
        result.passed = False
        result.error = "No batch_id available"
        return

    path = f"/batches/{created_batch_id}"
    print(f"  GET {path}")
    resp = api("GET", path)
    check(result, resp, expected_status_codes=[200])

    if result.passed:
        data = result.response_body.get("data", {})
        print(f"  Batch: code={data.get('batch_code')}, material={data.get('material_name')}")
        print(f"    quantity={data.get('quantity')}, total_cost={data.get('total_cost')}, "
              f"method={data.get('cost_alloc_method')}")
        print(f"    items_count={data.get('items_count')}, sold_count={data.get('sold_count')}, "
              f"revenue={data.get('revenue')}, profit={data.get('profit')}, "
              f"payback_rate={data.get('payback_rate')}, status={data.get('status')}")

        # Check associated items
        batch_items = data.get("items", [])
        print(f"  Associated items: {len(batch_items)}")
        total_alloc = 0
        for item in batch_items:
            alloc = item.get("allocated_cost") or 0
            total_alloc += alloc
            print(f"    id={item.get('id')}, sku={item.get('sku_code')}, "
                  f"selling={item.get('selling_price')}, "
                  f"allocated_cost={alloc}, status={item.get('status')}")

            # Verify each item now has allocated_cost set
            if item.get("allocated_cost") is None:
                print(f"  BUG: Item {item.get('id')} has no allocated_cost after allocation!")

        print(f"  Sum of allocated_cost: {round(total_alloc, 2)} (expected: 3000)")

        # Verify batch stats consistency
        if data.get("items_count") != 3:
            print(f"  WARNING: items_count={data.get('items_count')} != expected 3")
        if data.get("status") != "new":
            print(f"  NOTE: batch status={data.get('status')} (expected 'new' for no sales)")


# ── Additional Edge Case Tests ────────────────────────────────────────────────

def test_step_14_auth_guard(result: TestResult):
    """Test that unauthenticated requests are rejected.
    
    NOTE: The dashboard endpoints currently do NOT require authentication.
    This is a potential security concern — all business endpoints should be behind auth.
    """
    print(f"  GET /dashboard/summary  (NO token)")
    resp = requests.get(f"{BASE_URL}/dashboard/summary")
    result.status_code = resp.status_code
    result.response_body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}

    if resp.status_code in [401, 403]:
        result.passed = True
        print(f"  Correctly rejected: HTTP {resp.status_code}")
    elif resp.status_code == 200:
        # Dashboard does NOT enforce auth — this is a BUG/SECURITY ISSUE
        result.passed = False
        result.error = "SECURITY: /dashboard/summary does not require authentication (returned 200 without token)"
        print(f"  BUG DETECTED: Dashboard endpoint accessible without auth! HTTP {resp.status_code}")
    else:
        result.passed = False
        result.error = f"Expected 401/403, got {resp.status_code}"


def test_step_15_invalid_login(result: TestResult):
    """Test login with wrong password."""
    payload = {"password": "wrong_password"}
    print(f"  POST /auth/login  body={json.dumps(payload)}")
    resp = api("POST", "/auth/login", json=payload)
    if resp.status_code == 401:
        result.passed = True
        result.status_code = 401
        result.response_body = resp.json()
        print(f"  Correctly rejected invalid password: {resp.json().get('message')}")
    else:
        result.passed = False
        result.status_code = resp.status_code
        result.error = f"Expected 401 for wrong password, got {resp.status_code}"


def test_step_16_create_item_missing_cost(result: TestResult):
    """Test that creating a high-value item without cost_price fails."""
    if not first_material_id:
        result.passed = False
        result.error = "No material_id available"
        return

    payload = {
        "material_id": first_material_id,
        "selling_price": 2000,
        "name": "E2E缺少进价测试",
    }
    print(f"  POST /items  body={json.dumps(payload, ensure_ascii=False)}")
    print(f"  (Expecting 400: high-value item requires cost_price)")
    resp = api("POST", "/items", json=payload)
    if resp.status_code == 400:
        result.passed = True
        result.status_code = 400
        result.response_body = resp.json()
        print(f"  Correctly rejected: {resp.json().get('message')}")
    else:
        result.passed = False
        result.status_code = resp.status_code
        result.error = f"Expected 400, got {resp.status_code}"


def test_step_17_sell_already_sold(result: TestResult):
    """Test that selling an already-sold item fails."""
    if not created_item_id:
        result.passed = False
        result.error = "No item_id available"
        return

    payload = {
        "item_id": created_item_id,
        "actual_price": 1500,
        "channel": "store",
        "sale_date": str(date.today()),
    }
    print(f"  POST /sales  body={json.dumps(payload, ensure_ascii=False)}")
    print(f"  (Expecting 400: item already sold)")
    resp = api("POST", "/sales", json=payload)
    if resp.status_code == 400:
        result.passed = True
        result.status_code = 400
        result.response_body = resp.json()
        print(f"  Correctly rejected: {resp.json().get('message')}")
    else:
        result.passed = False
        result.status_code = resp.status_code
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        result.response_body = body
        result.error = f"Expected 400 for selling sold item, got {resp.status_code}"


def test_step_18_health_check(result: TestResult):
    """GET /api/health — System health check."""
    print(f"  GET /api/health")
    resp = requests.get(f"http://127.0.0.1:{SERVER_PORT}/api/health")
    check(result, resp, expected_status_codes=[200])
    if result.passed:
        print(f"  Health: {result.response_body}")


# ── Main Runner ────────────────────────────────────────────────────────────────

def _start_server():
    """Start the uvicorn server as a subprocess, return the process handle."""
    env = os.environ.copy()
    env["JWT_SECRET"] = "test-secret-key-for-e2e-testing-12345"
    env["DEFAULT_ADMIN_PASSWORD"] = "admin123"

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(SERVER_PORT)],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )

    # Wait for server to be ready
    for _ in range(30):
        try:
            r = requests.get(f"http://127.0.0.1:{SERVER_PORT}/api/health", timeout=2)
            if r.status_code == 200:
                print(f"  Server ready (PID {proc.pid})")
                return proc
        except requests.ConnectionError:
            pass
        time.sleep(0.5)

    # Failed to start
    print(f"  Server failed to start. Output:")
    print(proc.stdout.read().decode(errors="replace"))
    proc.terminate()
    proc.wait()
    return None


def _stop_server(proc):
    """Terminate the server subprocess."""
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        print(f"  Server stopped (PID {proc.pid})")


def main():
    global BASE_URL
    print("=" * 70)
    print("  Jade Inventory E2E Test Suite")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Date: {date.today().isoformat()}")
    print("=" * 70)

    # ── Server lifecycle management ──
    server_proc = None
    server_was_external = False

    # Check if server is already running
    print("\n  Checking server connectivity...")
    try:
        resp = requests.get(f"http://127.0.0.1:{SERVER_PORT}/api/health", timeout=3)
        print(f"  External server detected: {resp.status_code}")
        server_was_external = True
    except (requests.ConnectionError, requests.Timeout):
        print("  No external server found. Starting embedded server...")
        server_proc = _start_server()
        if not server_proc:
            print("  FATAL: Could not start server.")
            sys.exit(1)

    # ── Run main flow tests ──
    run_step(1,  "Login (JWT Auth)", test_step_1_login)
    run_step(2,  "Get Dashboard Summary", test_step_2_dashboard)
    run_step(3,  "Create Supplier", test_step_3_create_supplier)
    run_step(4,  "Create Customer", test_step_4_create_customer)
    run_step(5,  "Get Materials (Dicts)", test_step_5_get_materials)
    run_step(6,  "Create High-Value Item", test_step_6_create_high_value_item)
    run_step(7,  "List Items (Verify)", test_step_7_list_items)
    run_step(8,  "Create Sale", test_step_8_create_sale)
    run_step(9,  "List Sales (Verify)", test_step_9_list_sales)
    run_step(10, "Create Batch", test_step_10_create_batch)
    run_step(11, "Add Items to Batch (x3)", test_step_11_add_items_to_batch)
    run_step(12, "Allocate Batch Cost", test_step_12_allocate_batch_cost)
    run_step(13, "Get Batch Detail (Verify)", test_step_13_get_batch_detail)

    # ── Run edge case tests ──
    run_step(14, "Auth Guard (No Token)", test_step_14_auth_guard)
    run_step(15, "Invalid Login", test_step_15_invalid_login)
    run_step(16, "Create Item Missing Cost", test_step_16_create_item_missing_cost)
    run_step(17, "Sell Already-Sold Item", test_step_17_sell_already_sold)
    run_step(18, "Health Check", test_step_18_health_check)

    # ── Summary ──
    print("\n")
    print("=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)

    for r in results:
        print(str(r))

    print(f"\n  Total: {total} | Passed: {passed} | Failed: {failed}")
    print("=" * 70)

    if failed > 0:
        print("\n  FAILED TESTS DETAIL:")
        for r in results:
            if not r.passed:
                print(f"\n  Step {r.step} [{r.name}]:")
                print(f"    Error: {r.error}")
                if r.response_body:
                    body_str = json.dumps(r.response_body, ensure_ascii=False, indent=2)
                    print(f"    Response: {body_str[:500]}")

    # Print bugs discovered
    bugs_found = []
    for r in results:
        if r.passed and r.error and ("BUG" in r.error or "WARNING" in str(r.response_body or "")):
            bugs_found.append(f"Step {r.step}: {r.error}")
        # Also check for warnings in the output
        if r.error and "calculation error" in r.error.lower():
            bugs_found.append(f"Step {r.step}: {r.error}")

    if bugs_found:
        print("\n" + "=" * 70)
        print("  POTENTIAL BUGS / ISSUES DISCOVERED:")
        print("=" * 70)
        for bug in bugs_found:
            print(f"  - {bug}")

    # Return exit code
    exit_code = 0 if failed == 0 else 1

    # Cleanup: stop embedded server
    if server_proc and not server_was_external:
        _stop_server(server_proc)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
