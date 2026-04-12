"""
批次统计公共模块 — 提取自 dashboard.py / batches.py / export.py 的重复逻辑。

提供一个统一的 compute_batch_stats 函数，用于计算批次的销售统计、利润和回本状态。
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Batch, Item, SaleRecord


def compute_batch_stats(batch: Batch, db: Session) -> dict:
    """
    计算批次的统计指标。

    返回字典包含以下字段：
    - items_count:    关联货品数量（未删除）
    - sold_count:     已售货品数量
    - remaining_count: 未售货品数量 = items_count - sold_count
    - revenue:        已售回款总额
    - total_cost:     批次总进价
    - profit:         利润 = revenue - total_cost
    - payback_rate:   回本进度 = revenue / total_cost（0‑1）
    - status:         批次状态（new / selling / paid_back / cleared）
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
    total_cost = batch.total_cost
    profit = revenue - total_cost
    payback_rate = revenue / total_cost if total_cost > 0 else 0.0

    # 未售数量
    remaining_count = items_count - sold_count

    # 批次状态（基于回本进度和销售情况）
    if sold_count == 0:
        batch_status = "new"  # 未售
    elif payback_rate >= 1.0:
        if sold_count >= batch.quantity:
            batch_status = "cleared"  # 清仓完
        else:
            batch_status = "paid_back"  # 已回本
    else:
        batch_status = "selling"  # 销售中

    return {
        "items_count": items_count,
        "sold_count": sold_count,
        "remaining_count": remaining_count,
        "revenue": round(revenue, 2),
        "total_cost": total_cost,
        "profit": round(profit, 2),
        "payback_rate": round(payback_rate, 4),
        "status": batch_status,
    }
