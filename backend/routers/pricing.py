"""
利润测算定价生成器路由 — 结合历史销售数据和珠宝零售逻辑，为新货品提供科学定价建议。

核心逻辑：
1. 分析历史销售数据：按材质/器型统计平均周转天数、毛利率、价格分布
2. 定价推荐引擎：基于成本 + 经营参数 + 历史数据生成推荐价格区间
3. 风险评估：根据品类特性评估压货风险和定价合理性
"""

import math
from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import (
    DictMaterial, DictType, Item, ItemSpec, SaleRecord,
    SysConfig,
)
from schemas import ApiResponse

router = APIRouter(prefix="/pricing", tags=["利润测算"])


def _get_config_value(db: Session, key: str, default: float = 0.0) -> float:
    """从 sys_config 读取配置值，失败返回默认值。"""
    config = db.query(SysConfig).filter(SysConfig.key == key).first()
    if config:
        try:
            return float(config.value)
        except (ValueError, TypeError):
            return default
    return default


def _calculate_material_stats(
    db: Session, material_id: int
) -> dict:
    """
    计算指定材质的历史销售统计：
    - 平均周转天数（进货到售出）
    - 平均毛利率
    - 平均成交价 / 平均成本价
    - 销售件数 / 总件数
    - 价格分位数（P25, P50, P75）
    """
    # 查询该材质已售出货品的销售记录
    sold_items = (
        db.query(Item)
        .join(SaleRecord, SaleRecord.item_id == Item.id)
        .filter(
            Item.material_id == material_id,
            Item.is_deleted == False,
        )
        .all()
    )

    if not sold_items:
        return {
            "material_id": material_id,
            "sold_count": 0,
            "avg_turnover_days": None,
            "avg_profit_margin": None,
            "avg_selling_price": None,
            "avg_cost": None,
            "median_selling_price": None,
            "price_p25": None,
            "price_p75": None,
        }

    turnover_days_list = []
    profit_margins = []
    selling_prices = []
    costs = []

    for item in sold_items:
        cost = item.allocated_cost if item.allocated_cost is not None else item.cost_price
        if cost is None:
            cost = 0.0

        # 取该货品的最新一条销售记录
        latest_sale = (
            db.query(SaleRecord)
            .filter(SaleRecord.item_id == item.id)
            .order_by(SaleRecord.sale_date.desc())
            .first()
        )

        if latest_sale:
            selling_prices.append(latest_sale.actual_price)
            costs.append(cost)
            profit = latest_sale.actual_price - cost
            margin = (profit / cost * 100) if cost > 0 else 0
            profit_margins.append(margin)

        # 计算周转天数
        if item.purchase_date and latest_sale:
            days = (latest_sale.sale_date - item.purchase_date).days
            if days >= 0:
                turnover_days_list.append(days)

    # 计算统计数据
    selling_prices.sort()
    costs.sort()
    profit_margins.sort()

    n = len(selling_prices)
    def percentile(sorted_list, p):
        if not sorted_list:
            return None
        idx = int(len(sorted_list) * p / 100)
        return sorted_list[min(idx, len(sorted_list) - 1)]

    avg_selling = sum(selling_prices) / n if n > 0 else None
    avg_cost = sum(costs) / len(costs) if costs else None
    avg_margin = sum(profit_margins) / len(profit_margins) if profit_margins else None
    avg_turnover = sum(turnover_days_list) / len(turnover_days_list) if turnover_days_list else None

    return {
        "material_id": material_id,
        "sold_count": len(sold_items),
        "avg_turnover_days": round(avg_turnover, 1) if avg_turnover is not None else None,
        "avg_profit_margin": round(avg_margin, 1) if avg_margin is not None else None,
        "avg_selling_price": round(avg_selling, 2) if avg_selling is not None else None,
        "avg_cost": round(avg_cost, 2) if avg_cost is not None else None,
        "median_selling_price": round(percentile(selling_prices, 50), 2),
        "price_p25": round(percentile(selling_prices, 25), 2),
        "price_p75": round(percentile(selling_prices, 75), 2),
    }


def _generate_pricing_recommendation(
    cost: float,
    material_stats: dict,
    operating_cost_rate: float,
    markup_rate: float,
    weight: Optional[float] = None,
    is_precious_metal: bool = False,
) -> dict:
    """
    定价推荐引擎。

    考虑因素：
    1. 基础定价（成本 + 经营成本率 + 上浮率）— 系统当前逻辑
    2. 历史数据参考（同类材质的平均售价和毛利率）
    3. 周转速度调整（周转慢 → 降低溢价 / 周转快 → 适当提高）
    4. 品类特性（贵金属 vs 非贵金属）

    返回推荐价格区间和各档位建议。
    """
    # 1. 基础定价
    operating_cost = cost * operating_cost_rate
    floor_price = cost + operating_cost
    base_price = floor_price * (1 + markup_rate)

    # 2. 历史参考调整
    historical_price = material_stats.get("avg_selling_price")
    historical_margin = material_stats.get("avg_profit_margin")
    historical_turnover = material_stats.get("avg_turnover_days")

    # 3. 推荐价格区间
    # 底价 = 基础定价 * 0.85（最低不低于成本）
    # 标准价 = 基础定价
    # 期望价 = 基础定价 * 1.15
    low_price = max(cost * 1.05, base_price * 0.85)  # 至少5%毛利
    standard_price = base_price
    high_price = base_price * 1.15

    # 如果有历史数据，调整推荐区间
    if historical_price and historical_margin:
        # 如果历史毛利率较高，可适当提高定价
        if historical_margin > 60:
            high_price = max(high_price, historical_price * 1.05)
            standard_price = max(standard_price, historical_price)
        # 如果历史毛利率较低，降低期望价
        elif historical_margin < 30:
            high_price = min(high_price, base_price * 1.05)
            standard_price = min(standard_price, base_price * 0.95)

        # 周转速度调整
        if historical_turnover and historical_turnover > 90:
            # 周转慢 → 降低溢价，加速出货
            standard_price = standard_price * 0.9
            high_price = high_price * 0.9
        elif historical_turnover and historical_turnover < 30:
            # 周转快 → 可适当提价
            standard_price = standard_price * 1.05

    # 4. 计算各档位的毛利率
    def calc_margin(price):
        if cost <= 0:
            return 0
        return round((price - cost) / cost * 100, 1)

    # 5. 风险评估
    risk_level = "low"
    risk_factors = []
    if historical_turnover and historical_turnover > 90:
        risk_level = "high"
        risk_factors.append(f"该品类平均周转{historical_turnover:.0f}天，超过90天压货线")
    elif historical_turnover and historical_turnover > 60:
        risk_level = "medium"
        risk_factors.append(f"该品类平均周转{historical_turnover:.0f}天，需关注动销")

    if historical_margin and historical_margin < 25:
        risk_level = max(risk_level, "medium", key=lambda x: {"low": 0, "medium": 1, "high": 2}[x])
        risk_factors.append(f"该品类历史毛利率{historical_margin:.1f}%，偏低")

    # 6. 珠宝零售定价逻辑 — 贵金属特殊处理
    pricing_logic = []
    pricing_logic.append({
        "title": "基础定价公式",
        "formula": f"底价 = 成本({cost:.0f}) × (1 + 经营成本率{operating_cost_rate*100:.0f}%) = {floor_price:.0f}",
        "detail": "底价是最低可接受价，低于此价意味着亏损"
    })
    pricing_logic.append({
        "title": "零售价建议",
        "formula": f"零售价 = 底价({floor_price:.0f}) × (1 + 上浮率{markup_rate*100:.0f}%) = {base_price:.0f}",
        "detail": "上浮率可在系统配置中调整，建议根据品类特性微调"
    })

    if is_precious_metal:
        pricing_logic.append({
            "title": "贵金属特殊考虑",
            "formula": f"工费利润 = 零售价 - 材料成本({cost:.0f} × 克重) - 工费",
            "detail": "贵金属定价需关注金价波动，建议定期按市价重算"
        })

    return {
        "floor_price": round(floor_price, 2),
        "low_price": round(low_price, 2),
        "standard_price": round(standard_price, 2),
        "high_price": round(high_price, 2),
        "low_margin": calc_margin(low_price),
        "standard_margin": calc_margin(standard_price),
        "high_margin": calc_margin(high_price),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "pricing_logic": pricing_logic,
        "historical_reference": {
            "avg_selling_price": material_stats.get("avg_selling_price"),
            "avg_profit_margin": material_stats.get("avg_profit_margin"),
            "avg_turnover_days": material_stats.get("avg_turnover_days"),
            "sold_count": material_stats.get("sold_count", 0),
            "median_selling_price": material_stats.get("median_selling_price"),
        } if material_stats.get("sold_count", 0) > 0 else None,
    }


# ──────────────────────────────────────────────
# 端点
# ──────────────────────────────────────────────

@router.get(
    "/material-stats",
    summary="材质销售统计",
    description="返回各材质的历史销售统计数据，用于定价参考。",
)
def get_material_stats(
    db: Session = Depends(get_db),
) -> ApiResponse:
    """获取所有材质的历史销售统计。"""
    materials = db.query(DictMaterial).filter(DictMaterial.is_active == True).all()

    results = []
    for mat in materials:
        stats = _calculate_material_stats(db, mat.id)
        results.append({
            "material_id": mat.id,
            "material_name": mat.name,
            **stats,
        })

    return ApiResponse(data=results)


@router.get(
    "/material-stats/{material_id}",
    summary="单材质销售统计",
    description="返回指定材质的详细历史销售统计。",
)
def get_single_material_stats(
    material_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """获取指定材质的销售统计。"""
    material = db.get(DictMaterial, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="材质不存在")

    stats = _calculate_material_stats(db, material_id)
    return ApiResponse(data={
        "material_id": material.id,
        "material_name": material.name,
        **stats,
    })


@router.get(
    "/recommend",
    summary="定价推荐",
    description=(
        "基于成本、材质和系统配置参数，生成科学定价建议。"
        "综合考虑历史销售数据、周转速度和珠宝零售逻辑。"
    ),
)
def get_pricing_recommendation(
    cost: float = Query(..., description="货品成本（进价或分摊成本）", gt=0),
    material_id: int = Query(..., description="材质ID"),
    weight: Optional[float] = Query(None, description="克重（贵金属用）"),
    db: Session = Depends(get_db),
) -> ApiResponse:
    """获取定价推荐。"""
    # 校验材质
    material = db.get(DictMaterial, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="材质不存在")

    # 读取系统配置
    operating_cost_rate = _get_config_value(db, "operating_cost_rate", 0.05)
    markup_rate = _get_config_value(db, "markup_rate", 0.30)

    # 获取材质历史统计
    material_stats = _calculate_material_stats(db, material_id)

    # 判断是否为贵金属
    is_precious_metal = material.cost_per_gram is not None and material.cost_per_gram > 0

    # 生成推荐
    recommendation = _generate_pricing_recommendation(
        cost=cost,
        material_stats=material_stats,
        operating_cost_rate=operating_cost_rate,
        markup_rate=markup_rate,
        weight=weight,
        is_precious_metal=is_precious_metal,
    )

    return ApiResponse(data={
        "material_name": material.name,
        "cost": cost,
        "operating_cost_rate": operating_cost_rate,
        "markup_rate": markup_rate,
        "is_precious_metal": is_precious_metal,
        **recommendation,
    })


@router.get(
    "/type-stats/{material_id}",
    summary="按器型销售统计",
    description="返回指定材质下各器型（款式）的销售统计对比，帮助选择最优定价策略。",
)
def get_type_stats(
    material_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """获取指定材质下各器型的销售统计。"""
    # 获取该材质下所有有销售记录的器型
    results = (
        db.query(
            DictType.id,
            DictType.name,
            func.count(SaleRecord.id).label("sold_count"),
            func.avg(SaleRecord.actual_price).label("avg_price"),
            func.min(SaleRecord.actual_price).label("min_price"),
            func.max(SaleRecord.actual_price).label("max_price"),
        )
        .join(Item, Item.type_id == DictType.id)
        .join(SaleRecord, SaleRecord.item_id == Item.id)
        .filter(
            Item.material_id == material_id,
            Item.is_deleted == False,
        )
        .group_by(DictType.id, DictType.name)
        .having(func.count(SaleRecord.id) > 0)
        .order_by(func.count(SaleRecord.id).desc())
        .all()
    )

    type_stats = []
    for row in results:
        # 计算该器型的平均毛利率
        sold_items = (
            db.query(Item)
            .join(SaleRecord, SaleRecord.item_id == Item.id)
            .filter(
                Item.type_id == row.id,
                Item.material_id == material_id,
                Item.is_deleted == False,
            )
            .all()
        )

        margins = []
        for item in sold_items:
            item_cost = item.allocated_cost if item.allocated_cost is not None else item.cost_price
            if item_cost and item_cost > 0:
                latest_sale = (
                    db.query(SaleRecord)
                    .filter(SaleRecord.item_id == item.id)
                    .order_by(SaleRecord.sale_date.desc())
                    .first()
                )
                if latest_sale:
                    margin = (latest_sale.actual_price - item_cost) / item_cost * 100
                    margins.append(margin)

        avg_margin = sum(margins) / len(margins) if margins else None

        type_stats.append({
            "type_id": row.id,
            "type_name": row.name,
            "sold_count": row.sold_count,
            "avg_price": round(row.avg_price, 2) if row.avg_price else None,
            "min_price": round(row.min_price, 2) if row.min_price else None,
            "max_price": round(row.max_price, 2) if row.max_price else None,
            "avg_profit_margin": round(avg_margin, 1) if avg_margin is not None else None,
        })

    return ApiResponse(data=type_stats)


@router.get(
    "/config",
    summary="定价参数配置",
    description="返回当前系统的定价参数（经营成本率、上浮率等），供定价计算器使用。",
)
def get_pricing_config(
    db: Session = Depends(get_db),
) -> ApiResponse:
    """获取定价相关系统配置。"""
    configs = db.query(SysConfig).filter(
        SysConfig.key.in_(["operating_cost_rate", "markup_rate"])
    ).all()

    config_map = {}
    for c in configs:
        config_map[c.key] = {"value": c.value, "description": c.description}

    return ApiResponse(data={
        "operating_cost_rate": _get_config_value(db, "operating_cost_rate", 0.05),
        "markup_rate": _get_config_value(db, "markup_rate", 0.30),
        "aging_threshold_days": _get_config_value(db, "aging_threshold_days", 90),
        "config_details": config_map,
    })
