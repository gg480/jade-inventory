"""
端到端验证第3组（高货+销售）：

10. POST /api/v1/items 入库1件翡翠吊坠 cost_price=5000, selling_price=12000
11. POST /api/v1/sales item=步骤10的id, actual_price=10000, channel=store → sold
12. POST /api/v1/sales 同一件 → 应返回400

使用 TestClient 避免外部服务器依赖。
"""
import sys
sys.path.append(".")

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from database import SessionLocal
from models import DictMaterial, DictType

client = TestClient(app)

def get_material_id(name: str, db: Session) -> int:
    """根据材质名称获取ID"""
    material = db.query(DictMaterial).filter(DictMaterial.name == name).first()
    if not material:
        raise ValueError(f"材质「{name}」不存在")
    return material.id

def get_type_id(name: str, db: Session) -> int:
    """根据器型名称获取ID"""
    type_obj = db.query(DictType).filter(DictType.name == name).first()
    if not type_obj:
        raise ValueError(f"器型「{name}」不存在")
    return type_obj.id

def main():
    print("=== 端到端验证第3组：高货 + 单件销售 ===")

    with SessionLocal() as db:
        # 获取翡翠材质ID
        jade_id = get_material_id("翡翠", db)
        print(f"[OK] 获取翡翠材质ID: {jade_id}")

        # 获取吊坠器型ID
        pendant_type_id = get_type_id("吊坠", db)
        print(f"[OK] 获取吊坠器型ID: {pendant_type_id}")

    # ── 步骤10：入库高货翡翠吊坠 ──
    print("\n--- 步骤10：入库高货翡翠吊坠 ---")
    payload = {
        "material_id": jade_id,
        "type_id": pendant_type_id,
        "cost_price": 5000.0,
        "selling_price": 12000.0,
        "name": "验证用翡翠吊坠",
        "origin": "缅甸",
        "counter": 1,
        "tag_ids": []
    }
    resp = client.post("/api/v1/items", json=payload)
    if resp.status_code != 201:
        print(f"[FAIL] 步骤10失败，状态码: {resp.status_code}")
        print(resp.json())
        sys.exit(1)
    data = resp.json()
    if data["code"] != 0:
        print(f"[FAIL] 步骤10失败，code: {data['code']}, message: {data['message']}")
        sys.exit(1)
    item = data["data"]
    item_id = item["id"]
    print(f"[OK] 步骤10通过：高货入库成功，ID: {item_id}, SKU: {item['sku_code']}")
    print(f"     进价: {item['cost_price']}, 售价: {item['selling_price']}")

    # ── 步骤11：销售该货品 ──
    print("\n--- 步骤11：销售该货品 ---")
    sale_payload = {
        "item_id": item_id,
        "actual_price": 10000.0,
        "channel": "store",
        "sale_date": "2026-04-11",
        "note": "验证销售"
    }
    resp = client.post("/api/v1/sales", json=sale_payload)
    if resp.status_code != 201:
        print(f"[FAIL] 步骤11失败，状态码: {resp.status_code}")
        print(resp.json())
        sys.exit(1)
    data = resp.json()
    if data["code"] != 0:
        print(f"[FAIL] 步骤11失败，code: {data['code']}, message: {data['message']}")
        sys.exit(1)
    sale_record = data["data"]
    sale_no = sale_record["sale_no"]
    print(f"[OK] 步骤11通过：销售成功，销售单号: {sale_no}")
    print(f"     成交价: {sale_record['actual_price']}, 渠道: {sale_record['channel']}")

    # 验证货品状态已更新为 sold
    resp = client.get(f"/api/v1/items/{item_id}")
    if resp.status_code != 200:
        print(f"[FAIL] 无法获取货品详情，状态码: {resp.status_code}")
        sys.exit(1)
    item_data = resp.json()
    if item_data["code"] != 0:
        print(f"[FAIL] 获取货品详情失败: {item_data['message']}")
        sys.exit(1)
    item_status = item_data["data"]["status"]
    if item_status != "sold":
        print(f"[FAIL] 货品状态应为 sold，实际为 {item_status}")
        sys.exit(1)
    print(f"[OK] 货品状态已更新为 sold")

    # ── 步骤12：尝试重复销售同一件货品，应返回400 ──
    print("\n--- 步骤12：尝试重复销售同一件货品 ---")
    resp = client.post("/api/v1/sales", json=sale_payload)  # 使用相同的payload
    if resp.status_code == 400:
        data = resp.json()
        print(f"[OK] 步骤12通过：重复销售被拒绝，状态码 400")
        error_msg = data.get('detail', str(data))
        print(f"     错误信息: {error_msg}")
    else:
        print(f"[FAIL] 步骤12失败：预期状态码 400，实际得到 {resp.status_code}")
        print(resp.json())
        sys.exit(1)

    print("\n" + "="*60)
    print("[SUCCESS] 所有3个验证步骤通过！")
    print("="*60)

if __name__ == "__main__":
    main()