"""
货品功能验证脚本 — 模拟用户操作序列：
1. POST 入库一件高货：material_id=翡翠id, cost_price=5000, selling_price=12000
2. POST 入库3件通货关联之前创建的批次，每件 selling_price=120, spec 中 weight=10
3. POST /api/v1/batches/{批次id}/allocate
4. GET /api/v1/items 确认列表返回4件货品
"""
import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, init_db
from models import DictMaterial, Batch, Item, ItemSpec
from sqlalchemy.orm import Session
from sqlalchemy import func
import json

client = TestClient(app)

def get_material_id(name: str, db: Session) -> int:
    """根据材质名称获取ID"""
    material = db.query(DictMaterial).filter(DictMaterial.name == name).first()
    if not material:
        raise ValueError(f"材质「{name}」不存在")
    return material.id

def create_batch_if_not_exists(db: Session):
    """如果还没有批次，创建一个用于测试的批次"""
    batch = db.query(Batch).first()
    if batch:
        return batch

    # 获取水晶材质ID
    crystal_id = get_material_id("水晶", db)

    from datetime import date
    batch = Batch(
        batch_code="TEST001",
        material_id=crystal_id,
        quantity=3,
        total_cost=300.0,
        cost_alloc_method="equal",
        purchase_date=date.today()
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch

def test_high_value_item():
    """测试高货入库"""
    print("=== 1. 高货入库测试 ===")

    # 获取翡翠材质ID
    with SessionLocal() as db:
        jade_id = get_material_id("翡翠", db)

    # 构造请求体
    payload = {
        "material_id": jade_id,
        "cost_price": 5000.0,
        "selling_price": 12000.0,
        "name": "测试翡翠手镯",
        "origin": "缅甸",
        "counter": 1,
        "tag_ids": []
    }

    resp = client.post("/api/v1/items", json=payload)
    print(f"响应状态码: {resp.status_code}")
    print(f"响应内容: {resp.text}")

    if resp.status_code == 201:
        data = resp.json()
        assert data["code"] == 0
        item = data["data"]
        assert item["allocated_cost"] == 5000.0  # 高货 allocated_cost 应等于 cost_price
        assert item["status"] == "in_stock"
        print(f"[OK] 高货入库成功，SKU: {item['sku_code']}")
        return item["id"]
    else:
        print(f"[FAIL] 高货入库失败: {resp.text}")
        return None

def test_batch_items():
    """测试通货入库（关联批次）"""
    print("\n=== 2. 通货入库测试 ===")

    with SessionLocal() as db:
        # 获取批次
        batch = create_batch_if_not_exists(db)
        batch_id = batch.id
        # 获取水晶材质ID
        crystal_id = get_material_id("水晶", db)

    item_ids = []
    for i in range(3):
        payload = {
            "batch_id": batch_id,
            "material_id": crystal_id,
            "selling_price": 120.0,
            "name": f"测试水晶手串{i+1}",
            "spec": {
                "weight": 10.0
            },
            "tag_ids": []
        }

        resp = client.post("/api/v1/items", json=payload)
        print(f"通货{i+1} 响应状态码: {resp.status_code}")

        if resp.status_code == 201:
            data = resp.json()
            item = data["data"]
            item_ids.append(item["id"])
            print(f"[OK] 通货{i+1} 入库成功，SKU: {item['sku_code']}")
        else:
            print(f"[FAIL] 通货{i+1} 入库失败: {resp.text}")

    return item_ids, batch_id

def test_batch_allocate(batch_id: int):
    """测试批次成本分摊"""
    print(f"\n=== 3. 批次成本分摊测试 (批次ID: {batch_id}) ===")

    resp = client.post(f"/api/v1/batches/{batch_id}/allocate")
    print(f"响应状态码: {resp.status_code}")
    print(f"响应内容: {resp.text}")

    if resp.status_code == 200:
        data = resp.json()
        assert data["code"] == 0
        items = data["data"]["items"]
        print(f"[OK] 成本分摊成功，共 {len(items)} 件")
        for item in items:
            print(f"  - {item['sku_code']}: 分摊成本 {item['allocated_cost']}, 底价 {item['floor_price']}")
    else:
        print(f"[FAIL] 成本分摊失败: {resp.text}")

def test_list_items():
    """测试货品列表"""
    print("\n=== 4. 货品列表查询 ===")

    resp = client.get("/api/v1/items")
    print(f"响应状态码: {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        assert data["code"] == 0
        items = data["data"]["items"]
        pagination = data["data"]["pagination"]
        print(f"[OK] 列表查询成功，共 {pagination['total']} 件货品")

        # 打印货品摘要
        for item in items:
            cost = item.get("allocated_cost") or item.get("cost_price")
            print(f"  - {item['sku_code']}: {item['material_name']}, 成本 {cost}, 售价 {item['selling_price']}, 状态 {item['status']}")

        return pagination["total"]
    else:
        print(f"[FAIL] 列表查询失败: {resp.text}")
        return 0

def cleanup_test_data():
    """清理测试数据（可选）"""
    print("\n=== 清理测试数据 ===")
    with SessionLocal() as db:
        # 删除测试批次及其货品
        batch = db.query(Batch).filter(Batch.batch_code == "TEST001").first()
        if batch:
            # 删除关联货品
            items = db.query(Item).filter(Item.batch_id == batch.id).all()
            for item in items:
                # 删除规格
                if item.spec:
                    db.delete(item.spec)
                db.delete(item)
            db.delete(batch)
            db.commit()
            print("[OK] 测试批次及货品已删除")

        # 删除高货测试数据（通过名称匹配）
        test_items = db.query(Item).filter(Item.name.like("测试%")).all()
        for item in test_items:
            if item.spec:
                db.delete(item.spec)
            db.delete(item)
        db.commit()
        print(f"[OK] 删除 {len(test_items)} 件测试货品")

if __name__ == "__main__":
    print("开始货品功能验证...")

    # 初始化数据库（如果未初始化）
    try:
        init_db()
        print("数据库已初始化")
    except Exception as e:
        print(f"数据库初始化可能已存在: {e}")

    # 执行测试
    high_item_id = test_high_value_item()
    batch_item_ids, batch_id = test_batch_items()
    test_batch_allocate(batch_id)
    total_items = test_list_items()

    # 验证总数
    expected_total = 1 + len(batch_item_ids)  # 高货 + 通货
    if total_items >= expected_total:
        print(f"\n[OK] 验证通过：列表返回 {total_items} 件货品，期望至少 {expected_total} 件")
    else:
        print(f"\n[FAIL] 验证失败：列表返回 {total_items} 件货品，期望至少 {expected_total} 件")

    # 询问是否清理测试数据
    # cleanup_test_data()

    print("\n=== 测试完成 ===")