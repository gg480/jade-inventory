"""
看板统计路由 — 利润分析、销售趋势、压货预警、概览数据。

所有统计查询均使用 SQLAlchemy ORM 聚合（func.sum / func.count / func.strftime），
不执行原生 SQL，保持可移植性。
"""

import datetime
import math
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import DictMaterial, Item, SaleRecord
from schemas import (
    ApiResponse,
    DashboardSummary,
    ProfitByCategory,
    ProfitByChannel,
    SalesTrendItem,
    StockAgingItem,
)

router = APIRouter(prefix="/dashboard", tags=["看板统计"])

# 压货默认阈值（天）
_DEFAULT_AGING_DAYS = 90


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
                total_revenue=round(revenue, 2),
                total_cost=round(cost, 2),
                gross_profit=gp,
                gross_margin=_safe_margin(gp, revenue),
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
                total_revenue=round(revenue, 2),
                total_cost=round(cost, 2),
                gross_profit=gp,
                gross_margin=_safe_margin(gp, revenue),
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
            total_revenue=round(float(row.total_revenue or 0), 2),
            gross_profit=round(float(row.gross_profit or 0), 2),
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
                SalesTrendItem(year_month=ym, sales_count=0, total_revenue=0.0, gross_profit=0.0),
            )
        )
    return ApiResponse(data=result)


# ──────────────────────────────────────────────
# 4. 压货预警
# ──────────────────────────────────────────────

@router.get(
    "/stock-aging",
    response_model=ApiResponse[List[StockAgingItem]],
    summary="压货预警",
    description="列出在库超过指定天数的货品，按库龄降序排列，显示占用资金。",
)
def stock_aging(
    min_days: int = Query(_DEFAULT_AGING_DAYS, ge=0, description="在库天数阈值，默认 90 天"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[StockAgingItem]]:
    today = datetime.date.today()

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

    result = []
    for item in items:
        age = _item_age(item, today)
        if age >= min_days:
            result.append(
                StockAgingItem(
                    item_id=item.id,
                    sku_code=item.sku_code,
                    batch_code=item.batch_code,
                    material_name=item.material.name,
                    type_name=item.item_type.name if item.item_type else None,
                    cost_price=item.cost_price,
                    selling_price=item.selling_price,
                    purchase_date=item.purchase_date,
                    age_days=age,
                    cover_image=_cover_filename(item),
                )
            )

    # 按库龄降序，最久压货排最前
    result.sort(key=lambda x: x.age_days, reverse=True)
    return ApiResponse(data=result)


# ──────────────────────────────────────────────
# 5. 概览数据
# ──────────────────────────────────────────────

@router.get(
    "/summary",
    response_model=ApiResponse[DashboardSummary],
    summary="首页概览",
    description="返回总库存件数、占用资金、本月销售额/毛利、压货件数等核心指标。",
)
def dashboard_summary(
    aging_days: int = Query(_DEFAULT_AGING_DAYS, ge=0, description="压货阈值（天），默认 90"),
    db: Session = Depends(get_db),
) -> ApiResponse[DashboardSummary]:
    today = datetime.date.today()
    month_start = today.replace(day=1)

    # ── 库存统计 ──
    stock_rows = (
        db.query(
            Item.status,
            func.count(Item.id).label("cnt"),
            func.sum(Item.cost_price).label("total_cost"),
        )
        .filter(Item.is_deleted == False, Item.status.in_(["in_stock", "lent_out"]))
        .group_by(Item.status)
        .all()
    )
    total_stock = 0
    total_stock_value = 0.0
    lent_out_count = 0
    for row in stock_rows:
        if row.status == "in_stock":
            total_stock = row.cnt
            total_stock_value = float(row.total_cost or 0)
        elif row.status == "lent_out":
            lent_out_count = row.cnt

    # ── 本月销售统计 ──
    month_rows = (
        db.query(
            func.count(SaleRecord.id).label("sales_count"),
            func.sum(SaleRecord.actual_price).label("revenue"),
            func.sum(SaleRecord.actual_price - Item.cost_price).label("profit"),
        )
        .join(Item, SaleRecord.item_id == Item.id)
        .filter(SaleRecord.sale_date >= month_start)
        .one()
    )
    monthly_sales_count = month_rows.sales_count or 0
    monthly_revenue = round(float(month_rows.revenue or 0), 2)
    monthly_profit = round(float(month_rows.profit or 0), 2)

    # ── 压货预警统计 ──
    in_stock_items = (
        db.query(Item.purchase_date, Item.created_at, Item.cost_price)
        .filter(Item.status == "in_stock", Item.is_deleted == False)
        .all()
    )
    overage_count = 0
    overage_value = 0.0
    for row in in_stock_items:
        ref = row.purchase_date or row.created_at.date()
        age = (today - ref).days
        if age >= aging_days:
            overage_count += 1
            overage_value += row.cost_price

    return ApiResponse(
        data=DashboardSummary(
            total_stock=total_stock,
            total_stock_value=round(total_stock_value, 2),
            lent_out_count=lent_out_count,
            monthly_sales_count=monthly_sales_count,
            monthly_revenue=monthly_revenue,
            monthly_profit=monthly_profit,
            overage_count=overage_count,
            overage_value=round(overage_value, 2),
        )
    )
