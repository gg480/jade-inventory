"""
看板统计路由 — 利润分析、销售趋势、压货预警、概览数据。

所有统计查询均使用 SQLAlchemy ORM 聚合（func.sum / func.count / func.strftime），
不执行原生 SQL，保持可移植性。
"""

import datetime
import math
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Batch, DictMaterial, Item, SaleRecord
from schemas import (
    ApiResponse,
    BatchProfitItem,
    DashboardSummary,
    ProfitByCategory,
    ProfitByChannel,
    SalesTrendItem,
    StockAgingItem,
    StockAgingResponse,
)
from config import ALERT_DAYS

router = APIRouter(prefix="/dashboard", tags=["看板统计"])

# 压货默认阈值（天），使用 config.ALERT_DAYS
_DEFAULT_AGING_DAYS = ALERT_DAYS


# ──────────────────────────────────────────────
# 内部工具
# ──────────────────────────────────────────────

def _month_start(months_back: int = 0) -> datetime.date:
    """返回距今 months_back 个月前的月初日期（用于趋势查询）。"""
    today = datetime.date.today()
    year, month = today.year, today.month
    month -= months_back
    while month <= 0:
        month += 12
        year -= 1
    return datetime.date(year, month, 1)


def _safe_margin(gross_profit: float, total_revenue: float) -> float:
    """安全计算毛利率，避免除零。"""
    return round(gross_profit / total_revenue, 4) if total_revenue else 0.0


def _item_age(item: Item, today: datetime.date) -> int:
    """计算货品在库天数：优先用 purchase_date，无则用 created_at。"""
    ref = item.purchase_date or item.created_at.date()
    return (today - ref).days


def _cover_filename(item: Item) -> Optional[str]:
    for img in item.images:
        if img.is_cover:
            return img.filename
    return item.images[0].filename if item.images else None


def _compute_batch_stats(batch: Batch, db: Session) -> dict:
    """
    计算批次的统计指标（复用 batches.py 中的逻辑）。

    返回：
    - items_count: 关联货品数量（未删除）
    - sold_count: 已售货品数量
    - revenue: 已售货品的实际成交价总和
    - profit: 利润 = revenue - total_cost
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


# ──────────────────────────────────────────────
# 1. 按材质利润统计
# ──────────────────────────────────────────────

@router.get(
    "/profit/by-category",
    response_model=ApiResponse[List[ProfitByCategory]],
    summary="按材质利润统计",
    description="统计各材质的销售额、成本、毛利和毛利率；支持日期范围筛选。",
)
def profit_by_category(
    start_date: Optional[datetime.date] = Query(None, description="成交日期起（含）"),
    end_date: Optional[datetime.date] = Query(None, description="成交日期止（含）"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[ProfitByCategory]]:
    # 构建日期过滤条件
    date_filters = []
    if start_date:
        date_filters.append(SaleRecord.sale_date >= start_date)
    if end_date:
        date_filters.append(SaleRecord.sale_date <= end_date)

    rows = (
        db.query(
            DictMaterial.id.label("material_id"),
            DictMaterial.name.label("material_name"),
            func.count(SaleRecord.id).label("sales_count"),
            func.sum(SaleRecord.actual_price).label("total_revenue"),
            func.sum(Item.cost_price).label("total_cost"),
        )
        .join(Item, SaleRecord.item_id == Item.id)
        .join(DictMaterial, Item.material_id == DictMaterial.id)
        .filter(*date_filters)
        .group_by(DictMaterial.id, DictMaterial.name)
        .order_by(func.sum(SaleRecord.actual_price).desc())
        .all()
    )

    result = []
    for row in rows:
        revenue = float(row.total_revenue or 0)
        cost = float(row.total_cost or 0)
        gp = round(revenue - cost, 2)
        result.append(
            ProfitByCategory(
                material_id=row.material_id,
                material_name=row.material_name,
                sales_count=row.sales_count,
                revenue=round(revenue, 2),
                cost=round(cost, 2),
                profit=gp,
                profit_margin=_safe_margin(gp, revenue),
            )
        )
    return ApiResponse(data=result)


# ──────────────────────────────────────────────
# 2. 按渠道利润统计
# ──────────────────────────────────────────────

@router.get(
    "/profit/by-channel",
    response_model=ApiResponse[List[ProfitByChannel]],
    summary="按渠道利润统计",
    description="统计 store / wechat / ecommerce 各渠道的销售额、成本和毛利。",
)
def profit_by_channel(
    start_date: Optional[datetime.date] = Query(None, description="成交日期起（含）"),
    end_date: Optional[datetime.date] = Query(None, description="成交日期止（含）"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[ProfitByChannel]]:
    date_filters = []
    if start_date:
        date_filters.append(SaleRecord.sale_date >= start_date)
    if end_date:
        date_filters.append(SaleRecord.sale_date <= end_date)

    rows = (
        db.query(
            SaleRecord.channel,
            func.count(SaleRecord.id).label("sales_count"),
            func.sum(SaleRecord.actual_price).label("total_revenue"),
            func.sum(Item.cost_price).label("total_cost"),
        )
        .join(Item, SaleRecord.item_id == Item.id)
        .filter(*date_filters)
        .group_by(SaleRecord.channel)
        .order_by(func.sum(SaleRecord.actual_price).desc())
        .all()
    )

    result = []
    for row in rows:
        revenue = float(row.total_revenue or 0)
        cost = float(row.total_cost or 0)
        gp = round(revenue - cost, 2)
        result.append(
            ProfitByChannel(
                channel=row.channel,
                sales_count=row.sales_count,
                revenue=round(revenue, 2),
                cost=round(cost, 2),
                profit=gp,
                profit_margin=_safe_margin(gp, revenue),
            )
        )
    return ApiResponse(data=result)


# ──────────────────────────────────────────────
# 3. 按月销售趋势
# ──────────────────────────────────────────────

@router.get(
    "/trend",
    response_model=ApiResponse[List[SalesTrendItem]],
    summary="按月销售趋势",
    description="返回最近 N 个月的月度销售额、销量和毛利；可按材质筛选。",
)
def sales_trend(
    months: int = Query(12, ge=1, le=60, description="统计最近几个月，默认 12"),
    material_id: Optional[int] = Query(None, description="按材质 ID 筛选"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[SalesTrendItem]]:
    # 计算起始月份的第一天
    start_date = _month_start(months_back=months - 1)

    filters = [SaleRecord.sale_date >= start_date]
    if material_id is not None:
        filters.append(Item.material_id == material_id)

    # SQLite strftime 格式化年月
    year_month_expr = func.strftime("%Y-%m", SaleRecord.sale_date).label("year_month")

    rows = (
        db.query(
            year_month_expr,
            func.count(SaleRecord.id).label("sales_count"),
            func.sum(SaleRecord.actual_price).label("total_revenue"),
            func.sum(SaleRecord.actual_price - Item.cost_price).label("gross_profit"),
        )
        .join(Item, SaleRecord.item_id == Item.id)
        .filter(*filters)
        .group_by(year_month_expr)
        .order_by(year_month_expr)
        .all()
    )

    # 补齐没有销售的月份（前端图表需要连续数据点）
    trend_map = {
        row.year_month: SalesTrendItem(
            year_month=row.year_month,
            sales_count=row.sales_count,
            revenue=round(float(row.total_revenue or 0), 2),
            profit=round(float(row.gross_profit or 0), 2),
        )
        for row in rows
    }

    result = []
    for i in range(months):
        d = _month_start(months_back=months - 1 - i)
        ym = d.strftime("%Y-%m")
        result.append(
            trend_map.get(
                ym,
                SalesTrendItem(year_month=ym, sales_count=0, revenue=0.0, profit=0.0),
            )
        )
    return ApiResponse(data=result)


# ──────────────────────────────────────────────
# 4. 压货预警
# ──────────────────────────────────────────────

@router.get(
    "/stock-aging",
    response_model=ApiResponse[StockAgingResponse],
    summary="压货预警",
    description="列出在库超过指定天数的货品，按库龄降序排列，显示占用资金和柜台号。",
)
def stock_aging(
    min_days: int = Query(_DEFAULT_AGING_DAYS, ge=0, description="在库天数阈值，默认 90 天"),
    db: Session = Depends(get_db),
) -> ApiResponse[StockAgingResponse]:
    today = datetime.date.today()

    # 查询所有在库货品
    items = (
        db.query(Item)
        .options(
            selectinload(Item.material),
            selectinload(Item.item_type),
            selectinload(Item.images),
        )
        .filter(Item.status == "in_stock", Item.is_deleted == False)
        .all()
    )

    aging_items = []
    total_value = 0.0

    for item in items:
        age = _item_age(item, today)
        if age >= min_days:
            # 使用 allocated_cost 如果存在，否则用 cost_price
            cost_value = item.allocated_cost if item.allocated_cost is not None else item.cost_price
            if cost_value is not None:
                total_value += cost_value

            aging_items.append(
                StockAgingItem(
                    item_id=item.id,
                    sku_code=item.sku_code,
                    name=item.name,
                    batch_code=item.batch_code,
                    material_name=item.material.name,
                    type_name=item.item_type.name if item.item_type else None,
                    cost_price=item.cost_price,
                    allocated_cost=item.allocated_cost,
                    selling_price=item.selling_price,
                    purchase_date=item.purchase_date,
                    age_days=age,
                    cover_image=_cover_filename(item),
                    counter=item.counter,
                )
            )

    # 按库龄降序，最久压货排最前
    aging_items.sort(key=lambda x: x.age_days, reverse=True)

    # 构建响应
    response = StockAgingResponse(
        items=aging_items,
        total_items=len(aging_items),
        total_value=round(total_value, 2),
    )

    return ApiResponse(data=response)


# ──────────────────────────────────────────────
# 5. 概览数据
# ──────────────────────────────────────────────

@router.get(
    "/summary",
    response_model=ApiResponse[DashboardSummary],
    summary="仪表板概览",
    description="返回关键经营指标：在库件数、库存金额、本月销售、本月毛利、本月销售件数。",
)
def dashboard_summary(
    db: Session = Depends(get_db),
) -> ApiResponse[DashboardSummary]:
    today = datetime.date.today()
    month_start = today.replace(day=1)

    # 1. total_items: 在库货品数（status='in_stock' 且未删除）
    total_items = db.query(Item).filter(
        Item.status == "in_stock",
        Item.is_deleted == False,
    ).count()

    # 2. total_stock_value: 库存进价总和
    # 对于高货：使用 cost_price；对于通货：使用 allocated_cost
    stock_value_result = db.query(
        func.sum(
            func.coalesce(Item.allocated_cost, Item.cost_price, 0.0)
        )
    ).filter(
        Item.status == "in_stock",
        Item.is_deleted == False,
    ).scalar()
    total_stock_value = float(stock_value_result) if stock_value_result else 0.0

    # 3. 本月销售额、本月销售件数
    month_sales_query = db.query(SaleRecord).filter(
        SaleRecord.sale_date >= month_start
    )
    month_sold_count = month_sales_query.count()

    month_revenue_result = db.query(
        func.sum(SaleRecord.actual_price)
    ).filter(
        SaleRecord.sale_date >= month_start
    ).scalar()
    month_revenue = float(month_revenue_result) if month_revenue_result else 0.0

    # 4. 本月毛利：实际成交价 - 成本
    month_profit_result = db.query(
        func.sum(
            SaleRecord.actual_price -
            func.coalesce(Item.allocated_cost, Item.cost_price, 0.0)
        )
    ).join(
        Item, SaleRecord.item_id == Item.id
    ).filter(
        SaleRecord.sale_date >= month_start,
        Item.is_deleted == False,
    ).scalar()
    month_profit = float(month_profit_result) if month_profit_result else 0.0

    return ApiResponse(
        data=DashboardSummary(
            total_items=total_items,
            total_stock_value=round(total_stock_value, 2),
            month_revenue=round(month_revenue, 2),
            month_profit=round(month_profit, 2),
            month_sold_count=month_sold_count,
        )
    )


# ──────────────────────────────────────────────
# 6. 批次利润看板
# ──────────────────────────────────────────────

@router.get(
    "/batch-profit",
    response_model=ApiResponse[List[BatchProfitItem]],
    summary="批次利润看板",
    description="返回所有批次回本状态列表，支持按材质和状态筛选。",
)
def get_batch_profit(
    material_id: Optional[int] = Query(None, description="按材质ID筛选"),
    status: Optional[str] = Query(None, description="按批次状态筛选：new / selling / paid_back / cleared"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[BatchProfitItem]]:
    # 构建基础查询
    query = db.query(Batch)

    if material_id is not None:
        # 验证材质是否存在（可选）
        material = db.get(DictMaterial, material_id)
        if not material:
            raise HTTPException(status_code=404, detail="材质不存在")
        query = query.filter(Batch.material_id == material_id)

    # 获取所有符合条件的批次
    batches = query.order_by(Batch.created_at.desc()).all()

    result = []
    for batch in batches:
        stats = _compute_batch_stats(batch, db)

        # 按状态筛选（如果提供了 status 参数）
        if status is not None and stats["status"] != status:
            continue

        # 获取材质名称
        material_name = batch.material.name

        result.append(
            BatchProfitItem(
                batch_code=batch.batch_code,
                material_name=material_name,
                total_cost=batch.total_cost,
                quantity=batch.quantity,
                sold_count=stats["sold_count"],
                revenue=stats["revenue"],
                profit=stats["profit"],
                payback_rate=stats["payback_rate"],
                status=stats["status"],
            )
        )

    return ApiResponse(data=result)
