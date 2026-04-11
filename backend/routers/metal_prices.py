"""
贵金属市价管理路由 — 市价查询、更新、历史记录。

市价表（metal_prices）记录各材质（贵金属）的克重单价历史。
每次调价插入新记录，不覆盖旧数据。
"""

import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database import get_db
from models import MetalPrice, DictMaterial, Item, ItemSpec
from schemas import (
    ApiResponse,
    MetalPriceUpdate,
    MetalPriceOut,
    RepriceRequest,
    RepricePreview,
)

router = APIRouter(prefix="/metal-prices", tags=["贵金属市价"])


@router.get(
    "",
    response_model=ApiResponse[List[MetalPriceOut]],
    summary="获取当前市价",
    description="返回每种贵金属材质的最新市价记录（按 material 分组取最新记录）。",
)
def get_current_prices(
    db: Session = Depends(get_db),
) -> ApiResponse[List[MetalPriceOut]]:
    """
    获取当前市价：对每个 material_id 取最新的 effective_date 记录。
    返回列表，每个条目包含材质名称。
    """
    # 子查询：每个 material_id 的最大 effective_date
    subq = (
        db.query(
            MetalPrice.material_id,
            func.max(MetalPrice.effective_date).label("max_date")
        )
        .group_by(MetalPrice.material_id)
        .subquery()
    )
    # 主查询：关联子查询获取最新记录
    prices = (
        db.query(MetalPrice, DictMaterial.name.label("material_name"))
        .join(DictMaterial, MetalPrice.material_id == DictMaterial.id)
        .join(subq,
              (MetalPrice.material_id == subq.c.material_id) &
              (MetalPrice.effective_date == subq.c.max_date))
        .order_by(DictMaterial.name)
        .all()
    )

    result = []
    for mp, material_name in prices:
        out = MetalPriceOut(
            id=mp.id,
            material_id=mp.material_id,
            material_name=material_name,
            price_per_gram=mp.price_per_gram,
            effective_date=mp.effective_date,
            created_at=mp.created_at,
        )
        result.append(out)

    return ApiResponse(data=result)


@router.put(
    "/{material_id}",
    response_model=ApiResponse[MetalPriceOut],
    summary="更新市价",
    description="为指定材质插入一条新的市价记录（effective_date 默认为当天）。",
)
def update_price(
    material_id: int,
    body: MetalPriceUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[MetalPriceOut]:
    """
    更新（实为插入）市价记录。
    校验材质是否存在且为贵金属（可选）。
    """
    # 校验材质是否存在
    material = db.get(DictMaterial, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="材质不存在")

    # 确保 material_id 与请求体一致（路径参数优先）
    if body.material_id != material_id:
        raise HTTPException(
            status_code=400,
            detail="请求体中的 material_id 与路径参数不一致"
        )

    # 创建新记录
    new_price = MetalPrice(
        material_id=material_id,
        price_per_gram=body.price_per_gram,
        effective_date=datetime.date.today(),
    )
    db.add(new_price)
    db.commit()
    db.refresh(new_price)

    # 构建响应
    out = MetalPriceOut(
        id=new_price.id,
        material_id=new_price.material_id,
        material_name=material.name,
        price_per_gram=new_price.price_per_gram,
        effective_date=new_price.effective_date,
        created_at=new_price.created_at,
    )
    return ApiResponse(data=out)


@router.get(
    "/history",
    response_model=ApiResponse[List[MetalPriceOut]],
    summary="获取历史记录",
    description="返回市价历史记录，支持按 material_id 筛选，默认返回最近20条。",
)
def get_price_history(
    material_id: Optional[int] = Query(None, description="按材质ID筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回条数，默认20"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[MetalPriceOut]]:
    """
    获取历史记录，按 effective_date 降序排列。
    """
    q = (
        db.query(MetalPrice, DictMaterial.name.label("material_name"))
        .join(DictMaterial, MetalPrice.material_id == DictMaterial.id)
    )
    if material_id is not None:
        q = q.filter(MetalPrice.material_id == material_id)

    records = (
        q.order_by(desc(MetalPrice.effective_date), desc(MetalPrice.id))
        .limit(limit)
        .all()
    )

    result = []
    for mp, material_name in records:
        out = MetalPriceOut(
            id=mp.id,
            material_id=mp.material_id,
            material_name=material_name,
            price_per_gram=mp.price_per_gram,
            effective_date=mp.effective_date,
            created_at=mp.created_at,
        )
        result.append(out)

    return ApiResponse(data=result)


@router.post(
    "/reprice",
    response_model=ApiResponse[RepricePreview],
    summary="预览批量调价",
    description="根据新的贵金属市价计算在库货品的新零售价，返回预览结果（不实际修改）。",
)
def preview_reprice(
    body: RepriceRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[RepricePreview]:
    """
    批量调价预览：
    1. 获取该材质当前市价（最新记录）
    2. 查询在库货品（status='in_stock'）及其规格（重量）
    3. 计算每件货品的工费 = 原售价 - 重量 × 旧单价
    4. 计算新售价 = 重量 × 新单价 + 工费
    5. 返回受影响货品列表（sku_code, name, old_price, new_price）
    """
    # 1. 获取当前市价（最新记录）
    latest_price = (
        db.query(MetalPrice.price_per_gram)
        .filter(MetalPrice.material_id == body.material_id)
        .order_by(desc(MetalPrice.effective_date), desc(MetalPrice.id))
        .first()
    )
    if not latest_price:
        raise HTTPException(
            status_code=404,
            detail="该材质暂无市价记录，请先更新市价",
        )
    old_price_per_gram = latest_price.price_per_gram

    # 2. 查询在库货品及其规格
    items = (
        db.query(Item, ItemSpec)
        .join(ItemSpec, Item.id == ItemSpec.item_id, isouter=True)
        .filter(
            Item.material_id == body.material_id,
            Item.status == "in_stock",
            Item.is_deleted == False,
        )
        .all()
    )

    affected = []
    for item, spec in items:
        # 获取重量（如果规格不存在，重量为0）
        weight = spec.weight if spec and spec.weight else 0.0
        if weight <= 0:
            # 无重量记录的货品无法调价，跳过
            continue

        # 3. 计算工费
        labor_cost = item.selling_price - (weight * old_price_per_gram)
        # 4. 计算新售价
        new_selling_price = weight * body.new_price_per_gram + labor_cost
        # 确保新售价非负
        new_selling_price = max(new_selling_price, 0.0)

        affected.append({
            "sku_code": item.sku_code,
            "name": item.name,
            "old_price": item.selling_price,
            "new_price": new_selling_price,
        })

    return ApiResponse(data=RepricePreview(affected_items=affected))


@router.post(
    "/reprice/confirm",
    response_model=ApiResponse[RepricePreview],
    summary="确认批量调价",
    description="根据预览结果执行实际调价，更新在库货品的零售价。",
)
def confirm_reprice(
    body: RepriceRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[RepricePreview]:
    """
    确认批量调价：
    1. 执行与预览相同的计算逻辑
    2. 更新每件货品的 selling_price 字段
    3. 返回实际修改的货品列表
    """
    # 1. 获取当前市价（最新记录）
    latest_price = (
        db.query(MetalPrice.price_per_gram)
        .filter(MetalPrice.material_id == body.material_id)
        .order_by(desc(MetalPrice.effective_date), desc(MetalPrice.id))
        .first()
    )
    if not latest_price:
        raise HTTPException(
            status_code=404,
            detail="该材质暂无市价记录，请先更新市价",
        )
    old_price_per_gram = latest_price.price_per_gram

    # 2. 查询在库货品及其规格
    items = (
        db.query(Item, ItemSpec)
        .join(ItemSpec, Item.id == ItemSpec.item_id, isouter=True)
        .filter(
            Item.material_id == body.material_id,
            Item.status == "in_stock",
            Item.is_deleted == False,
        )
        .all()
    )

    affected = []
    for item, spec in items:
        weight = spec.weight if spec and spec.weight else 0.0
        if weight <= 0:
            continue

        old_selling_price = item.selling_price
        labor_cost = old_selling_price - (weight * old_price_per_gram)
        new_selling_price = weight * body.new_price_per_gram + labor_cost
        new_selling_price = max(new_selling_price, 0.0)

        # 更新货品售价
        item.selling_price = new_selling_price
        affected.append({
            "sku_code": item.sku_code,
            "name": item.name,
            "old_price": old_selling_price,
            "new_price": new_selling_price,
        })

    # 批量提交更新
    db.commit()

    return ApiResponse(data=RepricePreview(affected_items=affected))