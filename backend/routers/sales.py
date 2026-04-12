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
from models import BundleSale, Item, SaleRecord
from schemas import (
    ApiResponse,
    PaginationMeta,
    SaleCreate,
    SaleRecordListOut,
    SaleRecordOut,
    BundleSaleCreate,
    BundleSaleOut,
)

router = APIRouter(prefix="/sales", tags=["销售记录"])

# 合法销售渠道值
_VALID_CHANNELS = {"store", "wechat", "ecommerce"}


# ──────────────────────────────────────────────
# 内部工具函数
# ──────────────────────────────────────────────

def _load_options():
    """SaleRecord 预加载：item → material, customer（避免 N+1）。"""
    return [
        selectinload(SaleRecord.item).selectinload(Item.material),
        selectinload(SaleRecord.customer),
    ]


def _to_sale_out(record: SaleRecord) -> SaleRecordOut:
    """将 ORM SaleRecord 转为响应体，计算毛利。"""
    item = record.item
    # 使用 allocated_cost 计算毛利（对于通货）或 cost_price（对于高货）
    cost = item.allocated_cost if item.allocated_cost is not None else item.cost_price
    if cost is None:
        cost = 0.0
    gross_profit = record.actual_price - cost
    return SaleRecordOut(
        id=record.id,
        sale_no=record.sale_no,
        item_id=record.item_id,
        item_sku=item.sku_code,
        item_name=item.name,
        actual_price=record.actual_price,
        channel=record.channel,
        sale_date=record.sale_date,
        customer_id=record.customer_id,
        customer_name=record.customer.name if record.customer else None,
        bundle_id=record.bundle_id,
        note=record.note,
        created_at=record.created_at,
        cost=round(cost, 2),
        gross_profit=round(gross_profit, 2),
    )


def _generate_bundle_no(sale_date: datetime.date, db: Session) -> str:
    """生成套装销售编号：b20250410001 格式。"""
    date_prefix = sale_date.strftime("%Y%m%d")
    pattern = f"b{date_prefix}%"
    last_no = db.query(BundleSale.bundle_no).filter(
        BundleSale.bundle_no.like(pattern)
    ).order_by(BundleSale.bundle_no.desc()).first()
    if last_no:
        seq_str = last_no[0][len(f"b{date_prefix}"):]
        last_seq = int(seq_str) if seq_str.isdigit() else 0
        next_seq = last_seq + 1
    else:
        next_seq = 1
    if next_seq > 9999:
        raise HTTPException(status_code=500, detail="当日套装编号已超过9999上限")
    return f"b{date_prefix}{next_seq:03d}"


def _to_bundle_out(bundle: BundleSale) -> BundleSaleOut:
    """将 ORM BundleSale 转为响应体，包含销售记录列表及毛利计算。"""
    sale_records_out = []
    for record in bundle.sale_records:
        item = record.item
        # 使用 allocated_cost 计算毛利（对于通货）或 cost_price（对于高货）
        cost = item.allocated_cost if item.allocated_cost is not None else item.cost_price
        if cost is None:
            cost = 0.0
        gross_profit = record.actual_price - cost
        sale_out = SaleRecordOut(
            id=record.id,
            sale_no=record.sale_no,
            item_id=record.item_id,
            item_sku=item.sku_code,
            item_name=item.name,
            actual_price=record.actual_price,
            channel=record.channel,
            sale_date=record.sale_date,
            customer_id=record.customer_id,
            customer_name=record.customer.name if record.customer else None,
            bundle_id=record.bundle_id,
            note=record.note,
            created_at=record.created_at,
            cost=round(cost, 2),
            gross_profit=round(gross_profit, 2),
        )
        sale_records_out.append(sale_out)

    return BundleSaleOut(
        id=bundle.id,
        bundle_no=bundle.bundle_no,
        total_price=bundle.total_price,
        alloc_method=bundle.alloc_method,
        sale_date=bundle.sale_date,
        channel=bundle.channel,
        customer_id=bundle.customer_id,
        customer_name=bundle.customer.name if bundle.customer else None,
        note=bundle.note,
        created_at=bundle.created_at,
        sale_records=sale_records_out,
    )


# ──────────────────────────────────────────────
# 端点
# ──────────────────────────────────────────────

@router.get(
    "",
    response_model=ApiResponse[SaleRecordListOut],
    summary="销售记录列表",
    description="分页查询销售记录；支持按渠道、成交日期范围和客户ID筛选。",
)
def list_sales(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    size: int = Query(20, ge=1, le=100, description="每页条数"),
    channel: Optional[str] = Query(None, description="渠道筛选：store / wechat / ecommerce"),
    start_date: Optional[datetime.date] = Query(None, description="成交日期起（含），格式 YYYY-MM-DD"),
    end_date: Optional[datetime.date] = Query(None, description="成交日期止（含），格式 YYYY-MM-DD"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    db: Session = Depends(get_db),
) -> ApiResponse[SaleRecordListOut]:
    filters = []
    if channel is not None:
        filters.append(SaleRecord.channel == channel)
    if start_date is not None:
        filters.append(SaleRecord.sale_date >= start_date)
    if end_date is not None:
        filters.append(SaleRecord.sale_date <= end_date)
    if customer_id is not None:
        filters.append(SaleRecord.customer_id == customer_id)

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
            pagination=PaginationMeta(total=total, page=page, size=size, pages=pages),
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
    body: SaleCreate,
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

    # 3. 校验货品在库（非 in_stock 状态不可销售）
    if item.status != "in_stock":
        raise HTTPException(status_code=400, detail=f"货品状态为「{item.status}」，不可销售")

    # 4. 生成销售单号 s20250410001 格式
    date_prefix = body.sale_date.strftime("%Y%m%d")
    pattern = f"s{date_prefix}%"
    last_no = db.query(SaleRecord.sale_no).filter(
        SaleRecord.sale_no.like(pattern)
    ).order_by(SaleRecord.sale_no.desc()).first()
    if last_no:
        # 支持动态位数：先去掉日期前缀，取剩余数字部分
        seq_str = last_no[0][len(f"s{date_prefix}"):]
        last_seq = int(seq_str) if seq_str.isdigit() else 0
        next_seq = last_seq + 1
    else:
        next_seq = 1
    if next_seq > 9999:
        raise HTTPException(status_code=500, detail="当日销售编号已超过9999上限")
    sale_no = f"s{date_prefix}{next_seq:03d}"

    # 5. 在同一事务中创建销售记录 + 更新货品状态
    record = SaleRecord(
        sale_no=sale_no,
        item_id=body.item_id,
        actual_price=body.actual_price,
        channel=body.channel,
        sale_date=body.sale_date,
        customer_id=body.customer_id,
        note=body.note,
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


@router.post(
    "/bundle",
    response_model=ApiResponse[BundleSaleOut],
    status_code=status.HTTP_201_CREATED,
    summary="创建套装销售记录",
    description=(
        "一次交易包含多件货品，按比例分摊总价。"
        "所有货品状态同时改为 sold。整个操作在单一事务中完成。"
    ),
)
def create_bundle_sale(
    body: BundleSaleCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[BundleSaleOut]:
    # 1. 校验分摊方法
    valid_methods = {"by_ratio", "chain_at_cost"}
    if body.alloc_method not in valid_methods:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的分摊方法「{body.alloc_method}」，允许值：{sorted(valid_methods)}",
        )

    # chain_at_cost 必须提供 chain_items 标记
    if body.alloc_method == "chain_at_cost" and body.chain_items is None:
        raise HTTPException(
            status_code=400,
            detail="chain_at_cost 分摊方法必须提供 chain_items 字段，标记哪些货品是链子类",
        )

    # 2. 校验渠道合法性
    if body.channel not in _VALID_CHANNELS:
        raise HTTPException(
            status_code=400,
            detail=f"不合法的销售渠道「{body.channel}」，允许值：{sorted(_VALID_CHANNELS)}",
        )

    # 3. 校验所有货品存在、未删除、在库
    items = (
        db.query(Item)
        .filter(Item.id.in_(body.item_ids), Item.is_deleted == False)
        .all()
    )
    if len(items) != len(body.item_ids):
        # 找出缺失的 ID
        found_ids = {item.id for item in items}
        missing_ids = [iid for iid in body.item_ids if iid not in found_ids]
        raise HTTPException(
            status_code=404,
            detail=f"部分货品不存在或已删除：{missing_ids}",
        )

    # 检查状态
    not_in_stock = [item for item in items if item.status != "in_stock"]
    if not_in_stock:
        bad_ids = [item.id for item in not_in_stock]
        raise HTTPException(
            status_code=400,
            detail=f"货品 {bad_ids} 状态不是 in_stock，不可销售",
        )

    # 4. 生成套装编号
    bundle_no = _generate_bundle_no(body.sale_date, db)

    # 5. 计算分摊价格
    allocated_prices = []

    if body.alloc_method == "by_ratio":
        # ── by_ratio: 按零售价比例分摊 ──
        total_selling_price = sum(item.selling_price for item in items)
        if total_selling_price == 0:
            raise HTTPException(
                status_code=400,
                detail="所有货品零售价总和为0，无法按比例分摊",
            )
        for item in items:
            ratio = item.selling_price / total_selling_price
            allocated_price = round(body.total_price * ratio, 2)
            allocated_prices.append(allocated_price)

    elif body.alloc_method == "chain_at_cost":
        # ── chain_at_cost: 链子按 selling_price，剩余给主件 ──
        chain_flags = body.chain_items
        if len(chain_flags) != len(items):
            raise HTTPException(
                status_code=400,
                detail=f"chain_items 长度({len(chain_flags)})与 item_ids 长度({len(items)})不一致",
            )

        # 链子类货品的 selling_price 总和
        chain_cost = sum(
            item.selling_price for item, is_chain in zip(items, chain_flags) if is_chain
        )

        # 校验总价 >= 链子类 selling_price 总和
        if body.total_price < chain_cost:
            raise HTTPException(
                status_code=400,
                detail=f"套装总价({body.total_price})小于链子类零售价总和({chain_cost})，无法分摊",
            )

        # 如果没有标记为链子的，第一件为主件，其余为链子
        if not any(chain_flags):
            chain_flags = [False] + [True] * (len(chain_flags) - 1)
            chain_cost = sum(
                item.selling_price for item, is_chain in zip(items, chain_flags) if is_chain
            )
            if body.total_price < chain_cost:
                raise HTTPException(
                    status_code=400,
                    detail=f"套装总价({body.total_price})小于链子类零售价总和({chain_cost})，无法分摊",
                )

        # 主件 = 总价 - 链子类 selling_price 总和（精度由主件吸收）
        main_price = round(body.total_price - chain_cost, 2)

        for item, is_chain in zip(items, chain_flags):
            if is_chain:
                allocated_prices.append(item.selling_price)
            else:
                allocated_prices.append(main_price)

    # 6. 在同一事务中创建套装记录 + 各件销售记录 + 更新货品状态
    bundle = BundleSale(
        bundle_no=bundle_no,
        total_price=body.total_price,
        alloc_method=body.alloc_method,
        sale_date=body.sale_date,
        channel=body.channel,
        customer_id=body.customer_id,
        note=body.note,
    )
    db.add(bundle)
    db.flush()  # 获取 bundle.id 用于后续 sale_record

    # 为每件货品创建销售记录
    sale_records = []
    # 生成连续的销售编号
    date_prefix = body.sale_date.strftime("%Y%m%d")
    pattern = f"s{date_prefix}%"
    last_no = db.query(SaleRecord.sale_no).filter(
        SaleRecord.sale_no.like(pattern)
    ).order_by(SaleRecord.sale_no.desc()).first()
    if last_no:
        seq_str = last_no[0][len(f"s{date_prefix}"):]
        last_seq = int(seq_str) if seq_str.isdigit() else 0
        next_seq = last_seq + 1
    else:
        next_seq = 1

    # 为套装中的每件货品生成销售编号
    for idx, (item, allocated_price) in enumerate(zip(items, allocated_prices)):
        seq = next_seq + idx
        sale_no = f"s{date_prefix}{seq:03d}"

        record = SaleRecord(
            sale_no=sale_no,
            item_id=item.id,
            actual_price=allocated_price,
            channel=body.channel,
            sale_date=body.sale_date,
            customer_id=body.customer_id,
            bundle_id=bundle.id,
            note=body.note + f" (套装销售 {bundle_no})" if body.note else f"套装销售 {bundle_no}",
        )
        db.add(record)
        sale_records.append(record)
        # 更新货品状态
        item.status = "sold"

    db.commit()

    # 7. 重新查询以带入预加载的关联数据
    bundle = (
        db.query(BundleSale)
        .options(
            selectinload(BundleSale.customer),
            selectinload(BundleSale.sale_records).selectinload(SaleRecord.item).selectinload(Item.material),
        )
        .filter(BundleSale.id == bundle.id)
        .one()
    )
    return ApiResponse(data=_to_bundle_out(bundle))
