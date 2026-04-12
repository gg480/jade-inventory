"""
端到端验证第5组（套装销售）：

17. POST /api/v1/items 入库2件新货：吊坠selling_price=1000, 链子selling_price=200
18. POST /api/v1/sales/bundle item_ids=[两件id], total_price=900, alloc_method=by_ratio
    确认吊坠成交750, 链子成交150, 两件均 status=sold

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
    print("=== 端到端验证第5组：套装销售 ===")

    with SessionLocal() as db:
        # 获取翡翠材质ID
        jade_id = get_material_id("翡翠", db)
        print(f"[OK] 获取翡翠材质ID: {jade_id}")

        # 获取吊坠器型ID
        pendant_type_id = get_type_id("吊坠", db)
        print(f"[OK] 获取吊坠器型ID: {pendant_type_id}")

        # 获取项链器型ID（链子用）
        necklace_type_id = get_type_id("项链", db)
        print(f"[OK] 获取项链器型ID: {necklace_type_id}")

    # ── 步骤17：入库2件新货 ──
    print("\n--- 步骤17：入库2件新货 ---")

    # 吊坠（高货）
    print("1. 吊坠入库 (selling_price=1000)")
    pendant_payload = {
        "material_id": jade_id,
        "type_id": pendant_type_id,
        "cost_price": 500.0,
        "selling_price": 1000.0,
        "name": "验证用翡翠吊坠",
        "origin": "缅甸",
        "counter": 3,
        "tag_ids": []
    }
    resp = client.post("/api/v1/items", json=pendant_payload)
    if resp.status_code != 201:
        print(f"[FAIL] 吊坠入库失败，状态码: {resp.status_code}")
        print(resp.json())
        sys.exit(1)
    pendant_data = resp.json()
    if pendant_data["code"] != 0:
        print(f"[FAIL] 吊坠入库失败: {pendant_data['message']}")
        sys.exit(1)
    pendant_id = pendant_data["data"]["id"]
    pendant_sku = pendant_data["data"]["sku_code"]
    print(f"[OK] 吊坠入库成功，ID: {pendant_id}, SKU: {pendant_sku}")

    # 链子（高货，使用项链器型）
    print("2. 链子入库 (selling_price=200)")
    chain_payload = {
        "material_id": jade_id,
        "type_id": necklace_type_id,
        "cost_price": 100.0,
        "selling_price": 200.0,
        "name": "验证用银链",
        "counter": 3,
        "tag_ids": []
    }
    resp = client.post("/api/v1/items", json=chain_payload)
    if resp.status_code != 201:
        print(f"[FAIL] 链子入库失败，状态码: {resp.status_code}")
        print(resp.json())
        sys.exit(1)
    chain_data = resp.json()
    if chain_data["code"] != 0:
        print(f"[FAIL] 链子入库失败: {chain_data['message']}")
        sys.exit(1)
    chain_id = chain_data["data"]["id"]
    chain_sku = chain_data["data"]["sku_code"]
    print(f"[OK] 链子入库成功，ID: {chain_id}, SKU: {chain_sku}")

    # ── 步骤18：套装销售 ──
    print("\n--- 步骤18：套装销售 (total_price=900, alloc_method=by_ratio) ---")
    bundle_payload = {
        "item_ids": [pendant_id, chain_id],
        "total_price": 900.0,
        "alloc_method": "by_ratio",
        "channel": "store",
        "sale_date": "2026-04-11",
        "note": "验证套装销售"
    }
    resp = client.post("/api/v1/sales/bundle", json=bundle_payload)
    if resp.status_code != 201:
        print(f"[FAIL] 套装销售失败，状态码: {resp.status_code}")
        print(resp.json())
        sys.exit(1)
    bundle_data = resp.json()
    if bundle_data["code"] != 0:
        print(f"[FAIL] 套装销售失败: {bundle_data['message']}")
        sys.exit(1)
    bundle = bundle_data["data"]
    print(f"[OK] 套装销售成功，套装编号: {bundle['bundle_no']}")

    # 验证价格分摊
    print("\n--- 验证价格分摊 ---")
    # 理论计算：吊坠占比 1000/(1000+200)=5/6≈0.8333，链子占比 200/(1000+200)=1/6≈0.1667
    # 吊坠成交价 = 900 * 5/6 = 750，链子成交价 = 900 * 1/6 = 150

    pendant_record = None
    chain_record = None
    for sale in bundle["sale_records"]:
        if sale["item_id"] == pendant_id:
            pendant_record = sale
        elif sale["item_id"] == chain_id:
            chain_record = sale

    if not pendant_record or not chain_record:
        print(f"[FAIL] 未找到对应的销售记录")
        sys.exit(1)

    # 验证吊坠成交价 ≈ 750
    expected_pendant_price = 750.0
    actual_pendant_price = pendant_record["actual_price"]
    if abs(actual_pendant_price - expected_pendant_price) < 0.01:
        print(f"[OK] 吊坠成交价正确: {actual_pendant_price:.2f} ≈ {expected_pendant_price:.2f}")
    else:
        print(f"[FAIL] 吊坠成交价错误: 期望 {expected_pendant_price:.2f}, 实际 {actual_pendant_price:.2f}")
        sys.exit(1)

    # 验证链子成交价 ≈ 150
    expected_chain_price = 150.0
    actual_chain_price = chain_record["actual_price"]
    if abs(actual_chain_price - expected_chain_price) < 0.01:
        print(f"[OK] 链子成交价正确: {actual_chain_price:.2f} ≈ {expected_chain_price:.2f}")
    else:
        print(f"[FAIL] 链子成交价错误: 期望 {expected_chain_price:.2f}, 实际 {actual_chain_price:.2f}")
        sys.exit(1)

    # 验证两件货品状态均为 sold
    print("\n--- 验证货品状态 ---")
    for item_id in [pendant_id, chain_id]:
        resp = client.get(f"/api/v1/items/{item_id}")
        if resp.status_code != 200:
            print(f"[FAIL] 无法获取货品 {item_id} 详情")
            sys.exit(1)
        item_data = resp.json()
        if item_data["code"] != 0:
            print(f"[FAIL] 获取货品详情失败: {item_data['message']}")
            sys.exit(1)
        status = item_data["data"]["status"]
        if status == "sold":
            print(f"[OK] 货品 {item_id} 状态正确: sold")
        else:
            print(f"[FAIL] 货品 {item_id} 状态错误: 期望 sold, 实际 {status}")
            sys.exit(1)

    print("\n" + "="*60)
    print("[SUCCESS] 所有2个验证步骤通过！")
    print("="*60)

if __name__ == "__main__":
    main()