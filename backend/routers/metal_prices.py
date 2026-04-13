"""
贵金属市价管理路由 — 市价查询、更新、历史记录、自动抓取。

市价表（metal_prices）记录各材质（贵金属）的克重单价历史。
每次调价插入新记录，不覆盖旧数据。
支持从新浪财经接口自动获取实时价格。
"""

import datetime
import logging
import re
import urllib.request
import asyncio
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database import get_db
from models import MetalPrice, DictMaterial, Item, ItemSpec, SysConfig
from schemas import (
    ApiResponse,
    MetalPriceUpdate,
    MetalPriceOut,
    RepriceRequest,
    RepricePreview,
)

logger = logging.getLogger(__name__)

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


# ──────────────────────────────────────────────
# 新浪财经实时价格抓取（免费，无需 API Key）
# ──────────────────────────────────────────────

# 通用请求头，模拟浏览器访问
_SINA_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://finance.sina.com.cn',
}


def _fetch_sina_gold_price() -> Optional[float]:
    """获取黄金实时价格（上海金交所 Au99.99，单位：元/克）"""
    url = "https://hq.sinajs.cn/list=Au99.99"
    try:
        req = urllib.request.Request(url, headers=_SINA_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode('gbk')
            # 解析格式: var hq_str_Au99.99="Au99.99,开盘价,最高价,...,当前价,...";
            match = re.search(r'"(.*?)"', data)
            if match:
                fields = match.group(1).split(',')
                # 第0位是品种名，第6位是当前价
                if len(fields) >= 7:
                    try:
                        return float(fields[6])
                    except (ValueError, IndexError):
                        pass
            logger.warning("[sina_gold] 返回数据格式异常: %s", data[:100])
    except Exception as e:
        logger.error("[sina_gold] 抓取失败: %s", e)
    return None


def _fetch_sina_silver_price() -> Optional[float]:
    """获取白银实时价格（Ag(T+D)，单位：元/千克，需要转换为元/克）"""
    url = "https://hq.sinajs.cn/list=Ag(T+D)"
    try:
        req = urllib.request.Request(url, headers=_SINA_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode('gbk')
            # 解析格式: var hq_str_Ag(T+D)="Ag(T+D),开盘价,...,当前价,...";
            match = re.search(r'"(.*?)"', data)
            if match:
                fields = match.group(1).split(',')
                if len(fields) >= 7:
                    try:
                        # 白银 Ag(T+D) 报价为元/千克，转换为元/克
                        return round(float(fields[6]) / 1000, 2)
                    except (ValueError, IndexError):
                        pass
            logger.warning("[sina_silver] 返回数据格式异常: %s", data[:100])
    except Exception as e:
        logger.error("[sina_silver] 抓取失败: %s", e)
    return None


def _fetch_sina_platinum_price() -> Optional[float]:
    """获取铂金实时价格（Pt99.95，单位：元/克）"""
    url = "https://hq.sinajs.cn/list=Pt99.95"
    try:
        req = urllib.request.Request(url, headers=_SINA_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode('gbk')
            # 解析格式: var hq_str_Pt99.95="Pt99.95,开盘价,...,当前价,...";
            match = re.search(r'"(.*?)"', data)
            if match:
                fields = match.group(1).split(',')
                if len(fields) >= 7:
                    try:
                        return float(fields[6])
                    except (ValueError, IndexError):
                        pass
            logger.warning("[sina_platinum] 返回数据格式异常: %s", data[:100])
    except Exception as e:
        logger.error("[sina_platinum] 抓取失败: %s", e)
    return None


# 材质名称 ↔ 数据源映射
# Au99.99 为纯金价格，18K金 = 纯金 × 0.75
_MATERIAL_FETCH_MAP = {
    "18K金": {"fetcher": _fetch_sina_gold_price, "factor": 0.75, "source": "Au99.99"},
    "银":    {"fetcher": _fetch_sina_silver_price, "factor": 1.0,  "source": "Ag(T+D)"},
    "k铂金": {"fetcher": _fetch_sina_platinum_price, "factor": 1.0,  "source": "Pt99.95"},
}


@router.get(
    "/fetch",
    response_model=ApiResponse,
    summary="自动获取贵金属实时价格",
    description="从新浪财经接口抓取黄金、白银、铂金实时价格，"
                "写入 metal_prices 表并更新 sys_config 中的抓取状态。",
)
async def fetch_metal_prices(db: Session = Depends(get_db)) -> ApiResponse:
    """
    自动获取贵金属实时价格。
    数据源：新浪财经接口（免费，无需 API Key）

    流程：
    1. 逐个调用新浪接口获取 Au99.99 / Ag(T+D) / Pt99.95 价格
    2. 按映射关系写入 metal_prices 表（新记录，不覆盖旧数据）
    3. 更新 sys_config 中 last_price_fetch_time 和 last_price_fetch_status
    4. 返回获取到的最新价格列表
    """
    fetch_results: List[Dict] = []
    success_count = 0
    fail_count = 0
    errors: List[str] = []

    for material_name, cfg in _MATERIAL_FETCH_MAP.items():
        # 查找数据库中对应的材质记录
        material = db.query(DictMaterial).filter(DictMaterial.name == material_name).first()
        if not material:
            errors.append(f"材质 '{material_name}' 在数据库中不存在，跳过")
            fail_count += 1
            continue

        # 调用抓取函数（异步，避免阻塞事件循环）
        raw_price = await asyncio.to_thread(cfg["fetcher"])
        if raw_price is None:
            errors.append(f"{material_name}（{cfg['source']}）抓取失败，网络不通或接口异常")
            fail_count += 1
            continue

        # 应用换算系数（如 18K金 = 纯金 × 0.75）
        final_price = round(raw_price * cfg["factor"], 2)

        # 插入新记录到 metal_prices 表
        new_record = MetalPrice(
            material_id=material.id,
            price_per_gram=final_price,
            effective_date=datetime.date.today(),
        )
        db.add(new_record)

        fetch_results.append({
            "material_name": material_name,
            "source": cfg["source"],
            "raw_price": raw_price,
            "factor": cfg["factor"],
            "final_price": final_price,
        })
        success_count += 1
        logger.info(
            "[fetch] %s: 原始价=%.2f, 系数=%.2f, 最终价=%.2f",
            material_name, raw_price, cfg["factor"], final_price,
        )

    db.commit()

    # 更新 sys_config 中的抓取状态
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if fail_count == 0:
        status_msg = "成功"
    elif success_count == 0:
        status_msg = "全部失败"
    else:
        status_msg = f"部分成功（成功 {success_count}，失败 {fail_count}）"

    for cfg_key, cfg_val in [
        ("last_price_fetch_time", now_str),
        ("last_price_fetch_status", status_msg),
    ]:
        config_record = db.query(SysConfig).filter(SysConfig.key == cfg_key).first()
        if config_record:
            config_record.value = cfg_val
        else:
            db.add(SysConfig(key=cfg_key, value=cfg_val))
    db.commit()

    # 构建响应
    if success_count == 0:
        return ApiResponse(
            code=1,
            data={"fetched": fetch_results, "errors": errors},
            message=f"抓取失败：{'；'.join(errors)}",
        )

    return ApiResponse(
        data={
            "fetched": fetch_results,
            "errors": errors,
            "summary": {
                "success_count": success_count,
                "fail_count": fail_count,
                "fetch_time": now_str,
            },
        },
        message=status_msg,
    )


@router.get(
    "/fetch-status",
    response_model=ApiResponse,
    summary="获取最近一次自动抓取状态",
    description="从 sys_config 表读取 last_price_fetch_time 和 last_price_fetch_status。",
)
def get_fetch_status(db: Session = Depends(get_db)) -> ApiResponse:
    """
    获取最近一次自动抓取的状态和时间。
    从 sys_config 表读取 last_price_fetch_time 和 last_price_fetch_status。
    """
    configs = db.query(SysConfig).filter(
        SysConfig.key.in_(["last_price_fetch_time", "last_price_fetch_status", "auto_fetch_prices"])
    ).all()

    config_map = {c.key: c.value for c in configs}

    return ApiResponse(data={
        "last_fetch_time": config_map.get("last_price_fetch_time", ""),
        "last_fetch_status": config_map.get("last_price_fetch_status", ""),
        "auto_fetch_enabled": config_map.get("auto_fetch_prices", "false") == "true",
    })
