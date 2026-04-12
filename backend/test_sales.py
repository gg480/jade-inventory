"""
销售功能验证脚本 — 模拟用户操作序列：
1. POST /api/v1/sales 卖出高货，actual_price=10000, channel=store
   确认货品 status=sold
2. 再次 POST 同一件 → 应返回400
3. POST /api/v1/sales 卖出一件通货，actual_price=150
   GET /api/v1/batches/{id} 确认 payback_rate > 0
4. 入库2件新货（吊坠sell=1000, 链子sell=200）
   POST /api/v1/sales/bundle item_ids=[两件id], total_price=900, alloc_method=by_ratio
   确认吊坠成交750 链子成交150 两件均sold
"""
import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, init_db
from models import DictMaterial, Batch, Item, ItemSpec, DictType
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
from datetime import date, datetime, timedelta

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

def create_high_value_item(db: Session, material_name: str = "翡翠") -> int:
    """创建一件高货用于测试"""
    material_id = get_material_id(material_name, db)

    payload = {
        "material_id": material_id,
        "cost_price": 8000.0,  # 进价8000
        "selling_price": 15000.0,  # 标价15000
        "name": "测试高货-翡翠手镯",
        "origin": "缅甸",
        "counter": 1,
        "tag_ids": []
    }

    resp = client.post("/api/v1/items", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == 0
    item = data["data"]
    print(f"[OK] 高货创建成功: {item['sku_code']} (ID: {item['id']})")
    return item["id"]

def create_batch_with_item(db: Session, material_name: str = "水晶") -> tuple[int, int]:
    """创建一个批次并添加一件通货用于测试（使用ORM）"""
    material_id = get_material_id(material_name, db)

    # 创建批次
    batch = Batch(
        batch_code=f"TEST_SALE_{datetime.now().strftime('%H%M%S')}",
        material_id=material_id,
        quantity=1,
        total_cost=500.0,  # 批次总进价500
        cost_alloc_method="equal",
        purchase_date=date.today()
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    batch_id = batch.id
    print(f"[OK] 批次创建成功: {batch.batch_code} (ID: {batch_id})")

    # 创建通货货品
    # 首先需要生成SKU，但为了简化，我们让数据库自动生成或使用简单逻辑
    # 实际上，SKU应在入库时生成，但这里我们直接创建Item对象
    # 注意：实际应用中，Item的SKU应由系统生成，这里我们手动设置一个
    sku_code = f"TEST{datetime.now().strftime('%H%M%S')}"

    item = Item(
        sku_code=sku_code,
        name="测试通货-水晶手串",
        batch_id=batch_id,
        material_id=material_id,
        selling_price=200.0,  # 标价200
        status="in_stock",
        purchase_date=date.today()
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # 创建规格
    spec = ItemSpec(
        item_id=item.id,
        weight=15.0
    )
    db.add(spec)
    db.commit()

    print(f"[OK] 通货创建成功: {item.sku_code} (ID: {item.id})")

    # 触发成本分摊（通过API，因为分摊逻辑在端点中）
    resp = client.post(f"/api/v1/batches/{batch_id}/allocate")
    print(f"成本分摊响应状态码: {resp.status_code}")
    print(f"成本分摊响应内容: {resp.text}")
    assert resp.status_code == 200
    print(f"[OK] 批次成本分摊完成")

    return batch_id, item.id

def create_two_items_for_bundle(db: Session) -> tuple[int, int]:
    """创建两件新货品用于套装销售测试（吊坠和链子）"""
    # 获取翡翠材质ID
    material_id = get_material_id("翡翠", db)

    # 获取吊坠器型ID
    pendant_type_id = get_type_id("吊坠", db)

    # 创建吊坠（高货）
    pendant_payload = {
        "material_id": material_id,
        "type_id": pendant_type_id,
        "cost_price": 500.0,
        "selling_price": 1000.0,  # 标价1000
        "name": "测试吊坠-翡翠观音",
        "origin": "缅甸",
        "counter": 2,
        "tag_ids": []
    }

    resp = client.post("/api/v1/items", json=pendant_payload)
    assert resp.status_code == 201
    pendant_data = resp.json()
    pendant_id = pendant_data["data"]["id"]
    print(f"[OK] 吊坠创建成功 (ID: {pendant_id})")

    # 创建链子（高货）
    chain_payload = {
        "material_id": material_id,
        "cost_price": 100.0,  # 进价100
        "selling_price": 200.0,  # 标价200
        "name": "测试链子-银链",
        "counter": 2,
        "tag_ids": []
    }

    resp = client.post("/api/v1/items", json=chain_payload)
    assert resp.status_code == 201
    chain_data = resp.json()
    chain_id = chain_data["data"]["id"]
    print(f"[OK] 链子创建成功 (ID: {chain_id})")

    return pendant_id, chain_id

def test_scenario1_sell_high_value_item():
    """测试场景1：高货单件销售"""
    print("\n=== 1. 高货单件销售测试 ===")

    with SessionLocal() as db:
        # 创建高货
        high_item_id = create_high_value_item(db, "翡翠")

    # 销售请求
    sale_date = date.today().isoformat()
    sale_payload = {
        "item_id": high_item_id,
        "actual_price": 10000.0,  # 实际成交价10000
        "channel": "store",
        "sale_date": sale_date,
        "note": "测试高货销售"
    }

    resp = client.post("/api/v1/sales", json=sale_payload)
    print(f"销售响应状态码: {resp.status_code}")
    print(f"响应内容: {resp.text}")

    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == 0
    sale_record = data["data"]
    assert sale_record["actual_price"] == 10000.0
    assert sale_record["channel"] == "store"
    print(f"[OK] 高货销售成功，销售单号: {sale_record['sale_no']}")

    # 验证货品状态变为 sold
    resp = client.get(f"/api/v1/items/{high_item_id}")
    assert resp.status_code == 200
    item_data = resp.json()
    assert item_data["code"] == 0
    item = item_data["data"]
    assert item["status"] == "sold"
    print(f"[OK] 货品状态已更新为 sold")

    return high_item_id, sale_record["id"]

def test_scenario2_resell_same_item(high_item_id: int):
    """测试场景2：重复销售同一货品应失败"""
    print("\n=== 2. 重复销售测试 ===")

    sale_date = date.today().isoformat()
    sale_payload = {
        "item_id": high_item_id,
        "actual_price": 12000.0,
        "channel": "store",
        "sale_date": sale_date,
        "note": "重复销售测试"
    }

    resp = client.post("/api/v1/sales", json=sale_payload)
    print(f"重复销售响应状态码: {resp.status_code}")
    print(f"响应内容: {resp.text}")

    assert resp.status_code == 400
    data = resp.json()
    assert data["code"] == 400
    print(f"[OK] 重复销售正确返回400错误: {data['message']}")

    # 验证货品状态仍为 sold（不应改变）
    resp = client.get(f"/api/v1/items/{high_item_id}")
    assert resp.status_code == 200
    item_data = resp.json()
    assert item_data["code"] == 0
    item = item_data["data"]
    assert item["status"] == "sold"
    print(f"[OK] 货品状态保持 sold 未改变")

def test_scenario3_sell_batch_item():
    """测试场景3：通货销售及批次回本率验证"""
    print("\n=== 3. 通货销售及批次回本率测试 ===")

    with SessionLocal() as db:
        # 创建批次和通货
        batch_id, batch_item_id = create_batch_with_item(db, "水晶")

    # 销售请求
    sale_date = date.today().isoformat()
    sale_payload = {
        "item_id": batch_item_id,
        "actual_price": 150.0,  # 实际成交价150
        "channel": "wechat",
        "sale_date": sale_date,
        "note": "测试通货销售"
    }

    resp = client.post("/api/v1/sales", json=sale_payload)
    print(f"通货销售响应状态码: {resp.status_code}")

    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == 0
    sale_record = data["data"]
    print(f"[OK] 通货销售成功，销售单号: {sale_record['sale_no']}")

    # 验证货品状态变为 sold
    resp = client.get(f"/api/v1/items/{batch_item_id}")
    assert resp.status_code == 200
    item_data = resp.json()
    assert item_data["code"] == 0
    item = item_data["data"]
    assert item["status"] == "sold"
    print(f"[OK] 通货状态已更新为 sold")

    # 验证批次回本率 > 0
    resp = client.get(f"/api/v1/batches/{batch_id}")
    assert resp.status_code == 200
    batch_data = resp.json()
    assert batch_data["code"] == 0
    batch = batch_data["data"]
    payback_rate = batch["payback_rate"]
    assert payback_rate > 0
    print(f"[OK] 批次回本率: {payback_rate:.2%} > 0")

    return batch_id, batch_item_id

def test_scenario4_bundle_sale():
    """测试场景4：套装销售价格分摊验证"""
    print("\n=== 4. 套装销售价格分摊测试 ===")

    with SessionLocal() as db:
        # 创建两件货品
        pendant_id, chain_id = create_two_items_for_bundle(db)

    # 套装销售请求
    sale_date = date.today().isoformat()
    bundle_payload = {
        "item_ids": [pendant_id, chain_id],
        "total_price": 900.0,  # 套装总价900
        "alloc_method": "by_ratio",
        "channel": "store",
        "sale_date": sale_date,
        "note": "测试套装销售"
    }

    resp = client.post("/api/v1/sales/bundle", json=bundle_payload)
    print(f"套装销售响应状态码: {resp.status_code}")
    print(f"响应内容: {resp.text}")

    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == 0
    bundle = data["data"]
    assert bundle["total_price"] == 900.0
    assert bundle["alloc_method"] == "by_ratio"
    assert len(bundle["sale_records"]) == 2
    print(f"[OK] 套装销售成功，套装编号: {bundle['bundle_no']}")

    # 验证价格分摊：吊坠成交750，链子成交150
    # 理论计算：吊坠占比 1000/(1000+200)=5/6≈0.8333，链子占比 200/(1000+200)=1/6≈0.1667
    # 吊坠成交价 = 900 * 5/6 = 750，链子成交价 = 900 * 1/6 = 150
    pendant_record = None
    chain_record = None

    for record in bundle["sale_records"]:
        if record["item_id"] == pendant_id:
            pendant_record = record
        elif record["item_id"] == chain_id:
            chain_record = record

    assert pendant_record is not None
    assert chain_record is not None

    # 允许浮点数精度误差
    assert abs(pendant_record["actual_price"] - 750.0) < 0.01
    assert abs(chain_record["actual_price"] - 150.0) < 0.01

    print(f"[OK] 价格分摊正确：吊坠成交价 {pendant_record['actual_price']:.2f} ≈ 750.00")
    print(f"[OK] 价格分摊正确：链子成交价 {chain_record['actual_price']:.2f} ≈ 150.00")

    # 验证两件货品状态均为 sold
    for item_id in [pendant_id, chain_id]:
        resp = client.get(f"/api/v1/items/{item_id}")
        assert resp.status_code == 200
        item_data = resp.json()
        assert item_data["code"] == 0
        item = item_data["data"]
        assert item["status"] == "sold"

    print(f"[OK] 两件货品状态均已更新为 sold")

    return pendant_id, chain_id, bundle["id"]

def cleanup_test_data():
    """清理测试数据（可选）"""
    print("\n=== 清理测试数据 ===")
    with SessionLocal() as db:
        # 删除测试批次（名称以TEST_SALE_开头）
        test_batches = db.query(Batch).filter(Batch.batch_code.like("TEST_SALE_%")).all()
        for batch in test_batches:
            # 删除关联货品
            items = db.query(Item).filter(Item.batch_id == batch.id).all()
            for item in items:
                if item.spec:
                    db.delete(item.spec)
                db.delete(item)
            db.delete(batch)

        # 删除测试货品（通过名称匹配）
        test_items = db.query(Item).filter(Item.name.like("测试%")).all()
        for item in test_items:
            if item.spec:
                db.delete(item.spec)
            db.delete(item)

        db.commit()
        print(f"[OK] 清理完成：删除 {len(test_batches)} 个批次和 {len(test_items)} 件货品")

if __name__ == "__main__":
    print("开始销售功能验证...")

    # 初始化数据库（如果未初始化）
    try:
        init_db()
        print("数据库已初始化")
    except Exception as e:
        print(f"数据库初始化可能已存在: {e}")

    try:
        # 执行测试场景
        high_item_id, sale_id = test_scenario1_sell_high_value_item()
        test_scenario2_resell_same_item(high_item_id)
        batch_id, batch_item_id = test_scenario3_sell_batch_item()
        pendant_id, chain_id, bundle_id = test_scenario4_bundle_sale()

        print("\n" + "="*50)
        print("[SUCCESS] 所有销售功能验证通过！")
        print("="*50)

    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 询问是否清理测试数据
    # cleanup_test_data()

    print("\n=== 测试完成 ===")