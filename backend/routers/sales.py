"""
销售记录路由 — 出库登记与销售列表查询。

POST /sales 是核心业务操作，创建销售记录与更新货品状态在同一事务中完成，
保证数据一致性：不会出现"有销售记录但货品仍显示在库"的情况。
"""

import datetime
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Item, SaleRecord
from schemas import (
    ApiResponse,
    Pagination,
    SaleRecordCreate,
    SaleRecordListOut,
    SaleRecordOut,
)

router = APIRouter(prefix="/sales", tags=["销售记录"])

# 合法销售渠道值
_VALID_CHANNELS = {"store", "wechat", "ecommerce"}


# ──────────────────────────────────────────────
# 内部工具函数
# ──────────────────────────────────────────────

def _load_options():
    """SaleRecord 预加载：item → material（避免 N+1）。"""
    return [
        selectinload(SaleRecord.item).selectinload(Item.material),
    ]


def _to_sale_out(record: SaleRecord) -> SaleRecordOut:
    """将 ORM SaleRecord 转为响应体，计算毛利和毛利率。"""
    item = record.item
    gross_profit = record.actual_price - item.cost_price
    # 避免除零（actual_price 已由 Pydantic 校验 gt=0，此处仅防御性处理）
    gross_margin = gross_profit / record.actual_price if record.actual_price else 0.0
    return SaleRecordOut(
        id=record.id,
        item_id=record.item_id,
        sku_code=item.sku_code,
        material_name=item.material.name,
        actual_price=record.actual_price,
        channel=record.channel,
        sale_date=record.sale_date,
        customer_note=record.customer_note,
        created_at=record.created_at,
        cost_price=item.cost_price,
        gross_profit=round(gross_profit, 2),
        gross_margin=round(gross_margin, 4),
    )


# ──────────────────────────────────────────────
# 端点
# ──────────────────────────────────────────────

@router.get(
    "",
    response_model=ApiResponse[SaleRecordListOut],
    summary="销售记录列表",
    description="分页查询销售记录；支持按渠道和成交日期范围筛选。",
)
def list_sales(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    size: int = Query(20, ge=1, le=100, description="每页条数"),
    channel: Optional[str] = Query(None, description="渠道筛选：store / wechat / ecommerce"),
    start_date: Optional[datetime.date] = Query(None, description="成交日期起（含），格式 YYYY-MM-DD"),
    end_date: Optional[datetime.date] = Query(None, description="成交日期止（含），格式 YYYY-MM-DD"),
    db: Session = Depends(get_db),
) -> ApiResponse[SaleRecordListOut]:
    filters = []
    if channel is not None:
        filters.append(SaleRecord.channel == channel)
    if start_date is not None:
        filters.append(SaleRecord.sale_date >= start_date)
    if end_date is not None:
        filters.append(SaleRecord.sale_date <= end_date)

    # 计总数（不带 selectinload）
    total = db.query(SaleRecord).filter(*filters).count()
    pages = math.ceil(total / size) if total > 0 else 1

    records = (
        db.query(SaleRecord)
        .options(*_load_options())
        .filter(*filters)
        .order_by(SaleRecord.sale_date.desc(), SaleRecord.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return ApiResponse(
        data=SaleRecordListOut(
            items=[_to_sale_out(r) for r in records],
            pagination=Pagination(total=total, page=page, size=size, pages=pages),
        )
    )


@router.post(
    "",
    response_model=ApiResponse[SaleRecordOut],
    status_code=status.HTTP_201_CREATED,
    summary="创建销售记录（出库）",
    description=(
        "登记一笔销售，同时将货品状态改为 sold。"
        "已售货品不可重复出库。整个操作在单一事务中完成。"
    ),
)
def create_sale(
    body: SaleRecordCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[SaleRecordOut]:
    # 1. 校验渠道合法性
    if body.channel not in _VALID_CHANNELS:
        raise HTTPException(
            status_code=400,
            detail=f"不合法的销售渠道「{body.channel}」，允许值：{sorted(_VALID_CHANNELS)}",
        )

    # 2. 校验货品存在且未删除
    item = (
        db.query(Item)
        .options(selectinload(Item.material))
        .filter(Item.id == body.item_id, Item.is_deleted == False)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="货品不存在或已删除")

    # 3. 校验货品未售出（幂等保护）
    if item.status == "sold":
        raise HTTPException(status_code=400, detail="该货品已售出，不可重复出库")

    # 4. 在同一事务中创建销售记录 + 更新货品状态
    record = SaleRecord(
        item_id=body.item_id,
        actual_price=body.actual_price,
        channel=body.channel,
        sale_date=body.sale_date,
        customer_note=body.customer_note,
    )
    db.add(record)
    item.status = "sold"   # 联动更新，与 db.add(record) 同一 session

    db.commit()            # 单次 commit，两个操作原子提交
    db.refresh(record)

    # 5. 重新查询以带入预加载的关联数据（item.material）
    record = (
        db.query(SaleRecord)
        .options(*_load_options())
        .filter(SaleRecord.id == record.id)
        .one()
    )
    return ApiResponse(data=_to_sale_out(record))
