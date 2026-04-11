"""
端到端验证第4组（通货销售 + 回本）：

13. POST /api/v1/sales 卖出步骤7中的通货第1件, actual_price=150
14. GET /api/v1/batches/{步骤6的id} → payback_rate=0.50, status=selling
15. POST /api/v1/sales 卖出第2件, actual_price=200
16. GET /api/v1/batches/{id} → payback_rate≈1.17, status=paid_back

使用 TestClient 避免外部服务器依赖。
"""
import sys
import time
sys.path.append(".")

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from database import SessionLocal
from models import DictMaterial, Item, Batch

client = TestClient(app)

def get_material_id(name: str, db: Session) -> int:
    """根据材质名称获取ID"""
    material = db.query(DictMaterial).filter(DictMaterial.name == name).first()
    if not material:
        raise ValueError(f"材质「{name}」不存在")
    return material.id

def main():
    print("=== 端到端验证第4组：通货销售 + 回本 ===")

    with SessionLocal() as db:
        # 获取银材质ID
        silver_id = get_material_id("银", db)
        print(f"[OK] 获取银材质ID: {silver_id}")

    # ── 步骤6：创建批次（银材质，3件，总成本300，均摊）──
    print("\n--- 步骤6：创建批次 ---")
    batch_code = f"VALID{int(time.time())}"
    batch_payload = {
        "batch_code": batch_code,
        "material_id": silver_id,
        "quantity": 3,
        "total_cost": 300.0,
        "cost_alloc_method": "equal",
        "notes": "验证用批次"
    }
    resp = client.post("/api/v1/batches", json=batch_payload)
    if resp.status_code != 201:
        print(f"[FAIL] 步骤6失败，状态码: {resp.status_code}")
        print(resp.json())
        sys.exit(1)
    data = resp.json()
    if data["code"] != 0:
        print(f"[FAIL] 步骤6失败，code: {data['code']}, message: {data['message']}")
        sys.exit(1)
    batch = data["data"]
    batch_id = batch["id"]
    batch_code = batch["batch_code"]
    print(f"[OK] 步骤6通过：批次创建成功，ID: {batch_id}, 批次号: {batch_code}")
    print(f"     总成本: {batch['total_cost']}, 数量: {batch['quantity']}")

    # ── 步骤7：入库3件通货，每件 batch_id=批次ID, selling_price=120, spec中weight=10 ──
    print("\n--- 步骤7：入库3件通货 ---")
    item_ids = []
    for i in range(3):
        item_payload = {
            "batch_id": batch_id,
            "material_id": silver_id,
            "selling_price": 120.0,
            "name": f"验证通货-银饰{i+1}",
            "counter": 2,
            "tag_ids": [],
            "spec": {
                "weight": 10.0  # 克重10克
            }
        }
        resp = client.post("/api/v1/items", json=item_payload)
        if resp.status_code != 201:
            print(f"[FAIL] 货品{i+1}入库失败，状态码: {resp.status_code}")
            print(resp.json())
            sys.exit(1)
        data = resp.json()
        if data["code"] != 0:
            print(f"[FAIL] 货品{i+1}入库失败: {data['message']}")
            sys.exit(1)
        item = data["data"]
        item_ids.append(item["id"])
        print(f"[OK] 货品{i+1}入库成功，ID: {item['id']}, SKU: {item['sku_code']}")

    # ── 步骤8：调用成本分摊（可选，但建议）──
    print("\n--- 步骤8：成本分摊 ---")
    resp = client.post(f"/api/v1/batches/{batch_id}/allocate")
    if resp.status_code != 200:
        print(f"[FAIL] 成本分摊失败，状态码: {resp.status_code}")
        print(resp.json())
        sys.exit(1)
    data = resp.json()
    if data["code"] != 0:
        print(f"[FAIL] 成本分摊失败: {data['message']}")
        sys.exit(1)
    print(f"[OK] 成本分摊成功，每件 allocated_cost = 100.00")

    # ── 步骤13：销售第1件通货，actual_price=150 ──
    print("\n--- 步骤13：销售第1件通货 (actual_price=150) ---")
    first_item_id = item_ids[0]
    sale1_payload = {
        "item_id": first_item_id,
        "actual_price": 150.0,
        "channel": "store",
        "sale_date": "2026-04-11",
        "note": "验证销售1"
    }
    resp = client.post("/api/v1/sales", json=sale1_payload)
    if resp.status_code != 201:
        print(f"[FAIL] 步骤13失败，状态码: {resp.status_code}")
        print(resp.json())
        sys.exit(1)
    data = resp.json()
    if data["code"] != 0:
        print(f"[FAIL] 步骤13失败: {data['message']}")
        sys.exit(1)
    sale1 = data["data"]
    print(f"[OK] 步骤13通过：销售成功，销售单号: {sale1['sale_no']}")
    print(f"     成交价: {sale1['actual_price']}")

    # ── 步骤14：验证批次回本率=0.50, status=selling ──
    print("\n--- 步骤14：验证批次回本率=0.50, status=selling ---")
    resp = client.get(f"/api/v1/batches/{batch_id}")
    if resp.status_code != 200:
        print(f"[FAIL] 获取批次失败，状态码: {resp.status_code}")
        sys.exit(1)
    data = resp.json()
    if data["code"] != 0:
        print(f"[FAIL] 获取批次失败: {data['message']}")
        sys.exit(1)
    batch_info = data["data"]
    payback_rate = batch_info["payback_rate"]
    status = batch_info["status"]
    expected_rate = 0.50
    if abs(payback_rate - expected_rate) < 0.001:
        print(f"[OK] 回本率正确: {payback_rate} ≈ {expected_rate}")
    else:
        print(f"[FAIL] 回本率错误: 期望 {expected_rate}, 实际 {payback_rate}")
        sys.exit(1)
    if status == "selling":
        print(f"[OK] 批次状态正确: {status}")
    else:
        print(f"[FAIL] 批次状态错误: 期望 selling, 实际 {status}")
        sys.exit(1)

    # ── 步骤15：销售第2件通货，actual_price=200 ──
    print("\n--- 步骤15：销售第2件通货 (actual_price=200) ---")
    second_item_id = item_ids[1]
    sale2_payload = {
        "item_id": second_item_id,
        "actual_price": 200.0,
        "channel": "store",
        "sale_date": "2026-04-11",
        "note": "验证销售2"
    }
    resp = client.post("/api/v1/sales", json=sale2_payload)
    if resp.status_code != 201:
        print(f"[FAIL] 步骤15失败，状态码: {resp.status_code}")
        print(resp.json())
        sys.exit(1)
    data = resp.json()
    if data["code"] != 0:
        print(f"[FAIL] 步骤15失败: {data['message']}")
        sys.exit(1)
    sale2 = data["data"]
    print(f"[OK] 步骤15通过：销售成功，销售单号: {sale2['sale_no']}")
    print(f"     成交价: {sale2['actual_price']}")

    # ── 步骤16：验证批次回本率≈1.17, status=paid_back ──
    print("\n--- 步骤16：验证批次回本率≈1.17, status=paid_back ---")
    resp = client.get(f"/api/v1/batches/{batch_id}")
    if resp.status_code != 200:
        print(f"[FAIL] 获取批次失败，状态码: {resp.status_code}")
        sys.exit(1)
    data = resp.json()
    if data["code"] != 0:
        print(f"[FAIL] 获取批次失败: {data['message']}")
        sys.exit(1)
    batch_info = data["data"]
    payback_rate = batch_info["payback_rate"]
    status = batch_info["status"]
    expected_rate = 1.1667  # (150+200)/300 ≈ 1.166666...
    tolerance = 0.001
    if abs(payback_rate - expected_rate) < tolerance:
        print(f"[OK] 回本率正确: {payback_rate} ≈ {expected_rate}")
    else:
        print(f"[FAIL] 回本率错误: 期望约 {expected_rate}, 实际 {payback_rate}")
        sys.exit(1)
    if status == "paid_back":
        print(f"[OK] 批次状态正确: {status}")
    else:
        print(f"[FAIL] 批次状态错误: 期望 paid_back, 实际 {status}")
        sys.exit(1)

    print("\n" + "="*60)
    print("[SUCCESS] 所有4个验证步骤通过！")
    print("="*60)

if __name__ == "__main__":
    main()