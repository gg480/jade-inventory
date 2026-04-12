"""
批次管理路由 — 通货批次创建、列表、编辑、成本分摊。

批次（Batch）代表整手进货的通货（如一手水晶手串），记录总进价、数量、分摊算法。
批次创建后，货品（Item）可通过 batch_id 关联到该批次，成本分摊算法在货品录入完成后触发。
"""

import datetime
import math
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from database import get_db
from models import Batch, DictMaterial, DictType, Supplier, Item, SaleRecord, SysConfig
from schemas import (
    ApiResponse,
    BatchCreate,
    BatchUpdate,
    BatchOut,
    BatchListOut,
    BatchDetailOut,
    PaginationMeta,
    BatchAllocResult,
    ItemListItem,
)

router = APIRouter(prefix="/batches", tags=["批次管理"])

# 允许的成本分摊算法
_ALLOWED_ALLOC_METHODS = {"equal", "by_weight", "by_price"}


# ──────────────────────────────────────────────
# 内部工具函数
# ──────────────────────────────────────────────

def _load_options():
    """批次的预加载配置，避免 N+1 查询。"""
    return [
        selectinload(Batch.material),
        selectinload(Batch.type),
        selectinload(Batch.supplier),
    ]


def _get_batch_or_404(batch_id: int, db: Session) -> Batch:
    """按 ID 获取批次，不存在则抛 404。"""
    batch = (
        db.query(Batch)
        .options(*_load_options())
        .filter(Batch.id == batch_id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")
    return batch


def _get_config_value(db: Session, key: str, default: float = 0.0) -> float:
    """从 sys_config 读取浮点型配置值，不存在时返回默认值。"""
    config = db.query(SysConfig).filter(SysConfig.key == key).first()
    if not config:
        return default
    try:
        return float(config.value)
    except (ValueError, TypeError):
        return default


def _compute_batch_stats(batch: Batch, db: Session) -> dict:
    """
    计算批次的统计指标：
    - items_count: 关联货品数量（未删除）
    - sold_count: 已售货品数量
    - revenue: 已售货品的实际成交价总和
    - profit: 利润 = revenue - total_cost（注意：分母是批次总进价）
    - payback_rate: 回本进度 = revenue / total_cost（0‑1）
    - status: 批次状态（new / selling / paid_back / cleared）
    """
    # 关联货品（未删除）
    items_query = db.query(Item).filter(
        Item.batch_id == batch.id,
        Item.is_deleted == False
    )
    items_count = items_query.count()

    # 已售货品（通过 sale_records 关联）
    sold_subquery = (
        db.query(SaleRecord.item_id)
        .join(Item, SaleRecord.item_id == Item.id)
        .filter(Item.batch_id == batch.id, Item.is_deleted == False)
        .subquery()
    )
    sold_count = db.query(func.count()).select_from(sold_subquery).scalar() or 0

    # 已售回款
    revenue_result = (
        db.query(func.sum(SaleRecord.actual_price))
        .join(Item, SaleRecord.item_id == Item.id)
        .filter(Item.batch_id == batch.id, Item.is_deleted == False)
        .scalar()
    )
    revenue = float(revenue_result) if revenue_result else 0.0

    # 利润与回本进度
    profit = revenue - batch.total_cost
    payback_rate = revenue / batch.total_cost if batch.total_cost > 0 else 0.0

    # 批次状态（基于回本进度和销售情况）
    if sold_count == 0:
        status = "new"  # 未售
    elif payback_rate >= 1.0:
        if sold_count >= batch.quantity:
            status = "cleared"  # 清仓完
        else:
            status = "paid_back"  # 已回本
    else:
        status = "selling"  # 销售中

    return {
        "items_count": items_count,
        "sold_count": sold_count,
        "revenue": round(revenue, 2),
        "profit": round(profit, 2),
        "payback_rate": round(payback_rate, 4),
        "status": status,
    }


def _to_batch_out(batch: Batch, db: Session) -> BatchOut:
    """将 ORM Batch 对象转换为 BatchOut（含统计字段）。"""
    stats = _compute_batch_stats(batch, db)
    return BatchOut(
        id=batch.id,
        batch_code=batch.batch_code,
        material_id=batch.material_id,
        material_name=batch.material.name,
        type_id=batch.type_id,
        type_name=batch.type.name if batch.type else None,
        quantity=batch.quantity,
        total_cost=batch.total_cost,
        cost_alloc_method=batch.cost_alloc_method,
        supplier_id=batch.supplier_id,
        supplier_name=batch.supplier.name if batch.supplier else None,
        purchase_date=batch.purchase_date,
        notes=batch.notes,
        created_at=batch.created_at,
        items_count=stats["items_count"],
        sold_count=stats["sold_count"],
        revenue=stats["revenue"],
        profit=stats["profit"],
        payback_rate=stats["payback_rate"],
        status=stats["status"],
    )


# ──────────────────────────────────────────────
# 端点
# ──────────────────────────────────────────────

@router.get(
    "",
    response_model=ApiResponse[BatchListOut],
    summary="批次列表",
    description="分页查询批次；支持按材质筛选。",
)
def list_batches(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    size: int = Query(20, ge=1, le=100, description="每页条数"),
    material_id: Optional[int] = Query(None, description="按材质 ID 筛选"),
    db: Session = Depends(get_db),
) -> ApiResponse[BatchListOut]:
    # 构建基础过滤条件
    filters = []
    if material_id is not None:
        filters.append(Batch.material_id == material_id)

    # 先单独计总数
    total = db.query(Batch).filter(*filters).count()
    pages = math.ceil(total / size) if total > 0 else 1

    # 带预加载的分页数据查询
    batches_orm = (
        db.query(Batch)
        .options(*_load_options())
        .filter(*filters)
        .order_by(Batch.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    # 为每条记录计算统计并转换为 BatchOut
    items = [_to_batch_out(b, db) for b in batches_orm]

    return ApiResponse(
        data=BatchListOut(
            items=items,
            pagination=PaginationMeta(total=total, page=page, size=size),
        )
    )


@router.get(
    "/{batch_id}",
    response_model=ApiResponse[BatchDetailOut],
    summary="批次详情",
    description="获取批次详细信息，包含关联货品列表和回本状态。",
)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[BatchDetailOut]:
    # 获取批次信息
    batch = _get_batch_or_404(batch_id, db)
    batch_out = _to_batch_out(batch, db)

    # 获取关联货品列表（未删除）
    items = (
        db.query(Item)
        .filter(Item.batch_id == batch.id, Item.is_deleted == False)
        .options(
            selectinload(Item.material),
            selectinload(Item.type),
            selectinload(Item.tags),
            selectinload(Item.images),
        )
        .order_by(Item.id)
        .all()
    )

    # 转换为 ItemListItem
    item_list = []
    for item in items:
        # 计算在库天数
        age_days = None
        if item.purchase_date:
            from datetime import date
            age_days = (date.today() - item.purchase_date).days

        # 获取封面图
        cover_image = None
        for img in item.images:
            if img.is_cover:
                cover_image = img.filename
                break

        # 使用 model_validate 从 ORM 对象转换，然后更新额外字段
        item_data = ItemListItem.model_validate(item)
        # 更新需要额外计算的字段
        item_data.age_days = age_days
        item_data.cover_image = cover_image
        item_data.batch_code = batch.batch_code
        item_data.material_name = item.material.name
        item_data.type_name = item.type.name if item.type else None

        item_list.append(item_data)

    # 创建详情响应
    detail = BatchDetailOut(
        **batch_out.model_dump(),
        items=item_list,
    )

    return ApiResponse(data=detail)


@router.post(
    "",
    response_model=ApiResponse[BatchOut],
    status_code=status.HTTP_201_CREATED,
    summary="创建批次",
    description="创建通货批次，batch_code 必须全局唯一，cost_alloc_method 只能是 equal / by_weight / by_price。",
)
def create_batch(
    body: BatchCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[BatchOut]:
    # 1. batch_code 唯一性校验
    existing = db.query(Batch).filter(Batch.batch_code == body.batch_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"批次编号「{body.batch_code}」已存在")

    # 2. 成本分摊算法合法性校验
    if body.cost_alloc_method not in _ALLOWED_ALLOC_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"不合法的成本分摊算法「{body.cost_alloc_method}」，允许值：{sorted(_ALLOWED_ALLOC_METHODS)}",
        )

    # 3. 校验材质存在
    if not db.get(DictMaterial, body.material_id):
        raise HTTPException(status_code=404, detail="材质不存在")

    # 4. 校验器型存在（如果提供了）
    if body.type_id is not None and not db.get(DictType, body.type_id):
        raise HTTPException(status_code=404, detail="器型不存在")

    # 5. 校验供货商存在（如果提供了）
    if body.supplier_id is not None and not db.get(Supplier, body.supplier_id):
        raise HTTPException(status_code=404, detail="供货商不存在")

    # 6. 创建批次
    batch = Batch(
        batch_code=body.batch_code,
        material_id=body.material_id,
        type_id=body.type_id,
        quantity=body.quantity,
        total_cost=body.total_cost,
        cost_alloc_method=body.cost_alloc_method,
        supplier_id=body.supplier_id,
        purchase_date=body.purchase_date,
        notes=body.notes,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # 重新加载关联
    batch = _get_batch_or_404(batch.id, db)
    return ApiResponse(data=_to_batch_out(batch, db))


@router.put(
    "/{batch_id}",
    response_model=ApiResponse[BatchOut],
    summary="编辑批次",
    description="部分更新批次信息，只传需要修改的字段。",
)
def update_batch(
    batch_id: int,
    body: BatchUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[BatchOut]:
    batch = _get_batch_or_404(batch_id, db)

    # 1. batch_code 唯一性校验（如果提供了新值）
    if body.batch_code is not None and body.batch_code != batch.batch_code:
        existing = db.query(Batch).filter(Batch.batch_code == body.batch_code).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"批次编号「{body.batch_code}」已存在")

    # 2. 成本分摊算法合法性校验（如果提供了）
    if body.cost_alloc_method is not None and body.cost_alloc_method not in _ALLOWED_ALLOC_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"不合法的成本分摊算法「{body.cost_alloc_method}」，允许值：{sorted(_ALLOWED_ALLOC_METHODS)}",
        )

    # 3. 校验材质存在（如果提供了）
    if body.material_id is not None and not db.get(DictMaterial, body.material_id):
        raise HTTPException(status_code=404, detail="材质不存在")

    # 4. 校验器型存在（如果提供了）
    if body.type_id is not None and not db.get(DictType, body.type_id):
        raise HTTPException(status_code=404, detail="器型不存在")

    # 5. 校验供货商存在（如果提供了）
    if body.supplier_id is not None and not db.get(Supplier, body.supplier_id):
        raise HTTPException(status_code=404, detail="供货商不存在")

    # 逐字段更新（None 表示未传，跳过）
    if body.batch_code is not None:
        batch.batch_code = body.batch_code
    if body.material_id is not None:
        batch.material_id = body.material_id
    if body.type_id is not None:
        batch.type_id = body.type_id
    if body.quantity is not None:
        batch.quantity = body.quantity
    if body.total_cost is not None:
        batch.total_cost = body.total_cost
    if body.cost_alloc_method is not None:
        batch.cost_alloc_method = body.cost_alloc_method
    if body.supplier_id is not None:
        batch.supplier_id = body.supplier_id
    if body.purchase_date is not None:
        batch.purchase_date = body.purchase_date
    if body.notes is not None:
        batch.notes = body.notes

    db.commit()
    batch = _get_batch_or_404(batch_id, db)
    return ApiResponse(data=_to_batch_out(batch, db))


@router.post(
    "/{batch_id}/allocate",
    response_model=ApiResponse[BatchAllocResult],
    summary="触发批次成本分摊",
    description="""批次下所有货品录入完成后触发成本分摊。
    校验货品数量与批次 quantity 一致。
    根据 cost_alloc_method 计算每件分摊成本，保留两位小数，余数加到最后一件。
    算法：
    - equal: 每件 = total_cost / quantity
    - by_weight: 每件 = (该件weight / 总weight) × total_cost
    - by_price: 每件 = (该件selling_price / 总selling_price) × total_cost
    """,
)
def allocate_batch_cost(
    batch_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[BatchAllocResult]:
    # 1. 获取批次
    batch = _get_batch_or_404(batch_id, db)

    # 2. 获取该批次下所有未删除的货品
    items = (
        db.query(Item)
        .filter(Item.batch_id == batch.id, Item.is_deleted == False)
        .options(selectinload(Item.spec))
        .order_by(Item.id)
        .all()
    )

    # 3. 校验数量
    if len(items) != batch.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"批次「{batch.batch_code}」下货品数量({len(items)})与批次数量({batch.quantity})不一致，请先录完货品",
        )

    # 4. 读取定价配置
    operating_cost_rate = _get_config_value(db, "operating_cost_rate", 0.05)
    markup_rate = _get_config_value(db, "markup_rate", 0.30)

    # 5. 根据算法计算分摊成本
    method = batch.cost_alloc_method
    total_cost = batch.total_cost

    if method == "equal":
        # 均摊
        cost_per_item = total_cost / batch.quantity
        allocated = [cost_per_item] * batch.quantity
    elif method == "by_weight":
        # 按克重分摊，需要每件都有 weight
        weights = []
        for item in items:
            if not item.spec or item.spec.weight is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"货品「{item.sku_code}」缺少克重信息，无法按克重分摊",
                )
            weights.append(item.spec.weight)
        total_weight = sum(weights)
        if total_weight <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"总克重必须大于0，当前总克重={total_weight}",
            )
        allocated = [(w / total_weight) * total_cost for w in weights]
    elif method == "by_price":
        # 按售价比例分摊，需要每件都有 selling_price
        prices = [item.selling_price for item in items]
        total_price = sum(prices)
        if total_price <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"总售价必须大于0，当前总售价={total_price}",
            )
        allocated = [(p / total_price) * total_cost for p in prices]
    else:
        # 理论上不会发生，因为创建时已经校验过
        raise HTTPException(status_code=400, detail=f"未知的分摊算法「{method}」")

    # 6. 保留两位小数，处理余数（确保总和等于 total_cost）
    # 将每个成本乘以100，取整，分配余数
    cents = [int(round(c * 100)) for c in allocated]
    total_cents = sum(cents)
    target_cents = int(round(total_cost * 100))

    # 调整余数：将差值加到最后一个货品
    diff = target_cents - total_cents
    if diff != 0:
        cents[-1] += diff

    # 转换回元
    allocated_cents = [c / 100.0 for c in cents]

    # 7. 更新货品的 allocated_cost 字段并计算定价
    result_items = []
    for idx, item in enumerate(items):
        cost = allocated_cents[idx]
        item.allocated_cost = cost

        # 计算底价和零售价
        floor_price = cost * (1 + operating_cost_rate)
        item.floor_price = round(floor_price, 2)

        # 如果售价为0或空，则基于底价计算
        if not item.selling_price or item.selling_price <= 0:
            item.selling_price = round(floor_price * (1 + markup_rate), 2)

        result_items.append({
            "sku_code": item.sku_code,
            "allocated_cost": round(cost, 2),
            "floor_price": item.floor_price,
        })

    db.commit()

    # 8. 返回分摊结果
    return ApiResponse(data=BatchAllocResult(items=result_items))