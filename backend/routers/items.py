"""
货品管理路由 — 入库、查询、编辑、软删除。

路由注册顺序：POST /items/batch 必须在 GET/PUT/DELETE /items/{id} 之前，
否则 FastAPI 会把 "batch" 当作 id 参数处理，导致 422。
"""

import datetime
import math
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Batch, DictMaterial, DictTag, DictType, Item, ItemSpec, Supplier
from schemas import (
    ApiResponse,
    DictTagOut,
    ItemBatchCreate,
    ItemCreate,
    ItemImageOut,
    ItemListItem,
    ItemListOut,
    ItemOut,
    ItemSpecOut,
    ItemUpdate,
    PaginationMeta,
)

router = APIRouter(prefix="/items", tags=["货品管理"])

# 允许通过编辑接口设置的状态（sold 只能由销售接口触发）
_EDITABLE_STATUS = {"in_stock", "lent_out", "returned"}


# ──────────────────────────────────────────────
# 内部工具函数
# ──────────────────────────────────────────────

def _load_options():
    """统一的 selectinload 预加载配置，避免 N+1 查询。"""
    return [
        selectinload(Item.material),
        selectinload(Item.type),
        selectinload(Item.batch),
        selectinload(Item.supplier),
        selectinload(Item.tags),
        selectinload(Item.images),
        selectinload(Item.spec),
    ]


def _get_item_or_404(item_id: int, db: Session) -> Item:
    """按 ID 获取未删除货品，不存在则抛 404。"""
    item = (
        db.query(Item)
        .options(*_load_options())
        .filter(Item.id == item_id, Item.is_deleted == False)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="货品不存在或已删除")
    return item


def _cover_filename(item: Item) -> Optional[str]:
    """取封面图文件名：优先 is_cover=True，其次取第一张，无图返回 None。"""
    for img in item.images:
        if img.is_cover:
            return img.filename
    return item.images[0].filename if item.images else None


def _age_days(purchase_date: Optional[datetime.date]) -> Optional[int]:
    """计算在库天数；未填进货日期返回 None。"""
    if purchase_date is None:
        return None
    return (datetime.date.today() - purchase_date).days


def _to_item_out(item: Item) -> ItemOut:
    """将 ORM Item 对象转换为 ItemOut（含所有展开字段）。"""
    # 使用 model_validate 填充基础字段
    out = ItemOut.model_validate(item, from_attributes=True)
    # 手动设置关系字段
    out.batch_code = item.batch.batch_code if item.batch else None
    out.material_name = item.material.name
    out.type_name = item.type.name if item.type else None
    out.supplier_name = item.supplier.name if item.supplier else None
    out.spec = ItemSpecOut.model_validate(item.spec) if item.spec else None
    out.tags = [DictTagOut.model_validate(t) for t in item.tags]
    out.images = [ItemImageOut.model_validate(img) for img in item.images]
    out.age_days = _age_days(item.purchase_date)
    out.cover_image = _cover_filename(item)
    return out


def _to_list_item(item: Item) -> ItemListItem:
    """将 ORM Item 对象转换为列表条目（轻量版，不含完整图片列表）。"""
    # 使用 model_validate 填充基础字段
    out = ItemListItem.model_validate(item, from_attributes=True)
    # 手动设置关系字段
    out.batch_code = item.batch.batch_code if item.batch else None
    out.material_name = item.material.name
    out.type_name = item.type.name if item.type else None
    out.tags = [DictTagOut.model_validate(t) for t in item.tags]
    out.cover_image = _cover_filename(item)
    out.age_days = _age_days(item.purchase_date)
    return out


def _resolve_tags(tag_ids: List[int], db: Session) -> List[DictTag]:
    """校验并返回标签对象列表；有不存在的 ID 则抛 400。"""
    if not tag_ids:
        return []
    tags = db.query(DictTag).filter(DictTag.id.in_(tag_ids)).all()
    found_ids = {t.id for t in tags}
    missing = set(tag_ids) - found_ids
    if missing:
        raise HTTPException(status_code=400, detail=f"标签 ID {sorted(missing)} 不存在")
    return tags


def _generate_skus(db: Session, prefix: str, date_str: str, quantity: int) -> List[str]:
    """
    生成批量 SKU 编号，规则：{prefix}-{YYYYMMDD}-{3位序号}。
    自动跳过数据库中已存在的编号，保证唯一性。
    """
    pattern = f"{prefix}-{date_str}-%"
    existing: set[str] = {
        row[0]
        for row in db.query(Item.sku_code).filter(Item.sku_code.like(pattern)).all()
    }
    skus: List[str] = []
    seq = 1
    while len(skus) < quantity:
        candidate = f"{prefix}-{date_str}-{seq:03d}"
        if candidate not in existing:
            skus.append(candidate)
        seq += 1
        if seq > 9999:
            raise HTTPException(
                status_code=500, detail="当日该前缀 SKU 序号已耗尽，请更换前缀"
            )
    return skus


def _validate_material_type(
    material_id: int, type_id: Optional[int], db: Session
) -> None:
    """校验材质存在；如果传了 type_id，也校验该器型存在（器型独立于材质）。"""
    if not db.get(DictMaterial, material_id):
        raise HTTPException(status_code=404, detail="材质不存在")
    if type_id is not None and not db.get(DictType, type_id):
        raise HTTPException(status_code=404, detail="器型不存在")


# ──────────────────────────────────────────────
# 端点
# ──────────────────────────────────────────────

@router.get(
    "",
    response_model=ApiResponse[ItemListOut],
    summary="货品列表",
    description=(
        "分页查询在库货品；支持按材质、器型、状态、供货商筛选，"
        "以及按编号/款号/证书/备注全文搜索。"
    ),
)
def list_items(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    size: int = Query(20, ge=1, le=100, description="每页条数"),
    material_id: Optional[int] = Query(None, description="按材质 ID 筛选"),
    type_id: Optional[int] = Query(None, description="按器型 ID 筛选"),
    status: Optional[str] = Query(None, description="按状态筛选：in_stock / sold / lent_out / returned"),
    supplier_id: Optional[int] = Query(None, description="按供货商 ID 筛选"),
    batch_id: Optional[int] = Query(None, description="按批次 ID 筛选"),
    counter: Optional[int] = Query(None, description="按柜台号筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（编号/名称/款号/证书/备注）"),
    db: Session = Depends(get_db),
) -> ApiResponse[ItemListOut]:
    # 构建基础过滤条件
    filters = [Item.is_deleted == False]
    if material_id is not None:
        filters.append(Item.material_id == material_id)
    if type_id is not None:
        filters.append(Item.type_id == type_id)
    if status is not None:
        filters.append(Item.status == status)
    if supplier_id is not None:
        filters.append(Item.supplier_id == supplier_id)
    if batch_id is not None:
        filters.append(Item.batch_id == batch_id)
    if counter is not None:
        filters.append(Item.counter == counter)
    if keyword:
        kw = f"%{keyword}%"
        filters.append(
            or_(
                Item.sku_code.ilike(kw),
                Item.name.ilike(kw),
                Item.batch_code.ilike(kw),
                Item.cert_no.ilike(kw),
                Item.notes.ilike(kw),
            )
        )

    # 先单独计总数（不加 joinedload 避免 COUNT 污染）
    total = db.query(Item).filter(*filters).count()
    pages = math.ceil(total / size) if total > 0 else 1

    # 带预加载的分页数据查询
    items_orm = (
        db.query(Item)
        .options(*_load_options())
        .filter(*filters)
        .order_by(Item.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return ApiResponse(
        data=ItemListOut(
            items=[_to_list_item(it) for it in items_orm],
            pagination=PaginationMeta(total=total, page=page, size=size, pages=pages),
        )
    )


# ── 批量入库（必须在 /{id} 之前注册，否则 "batch" 会被解析为 id）──

@router.post(
    "/batch",
    response_model=ApiResponse[List[ItemOut]],
    status_code=status.HTTP_201_CREATED,
    summary="批量入库",
    description=(
        "同款商品批量入库，系统自动生成 N 个唯一 SKU 编号。"
        "规则：{sku_prefix}-{YYYYMMDD}-{三位序号}，如 SJ-20240315-001。"
    ),
)
def batch_create_items(
    body: ItemBatchCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[List[ItemOut]]:
    _validate_material_type(body.material_id, body.type_id, db)
    if body.supplier_id and not db.get(Supplier, body.supplier_id):
        raise HTTPException(status_code=404, detail="供货商不存在")

    # 获取材质对象，用于生成 SKU 前缀
    material = db.get(DictMaterial, body.material_id)
    material_name = material.name.strip()
    if len(material_name) >= 2:
        material_prefix = material_name[:2]
    else:
        material_prefix = material_name
    material_prefix = material_prefix.upper()

    tags = _resolve_tags(body.tag_ids, db)
    # 优先使用用户提供的 sku_prefix，否则使用材质缩写
    prefix = (body.sku_prefix or material_prefix).upper()
    date_str = datetime.date.today().strftime("%Y%m%d")
    skus = _generate_skus(db, prefix, date_str, body.quantity)

    created: List[Item] = []
    for sku in skus:
        item = Item(
            sku_code=sku,
            batch_code=body.batch_code,
            material_id=body.material_id,
            type_id=body.type_id,
            cost_price=body.cost_price,
            selling_price=body.selling_price,
            supplier_id=body.supplier_id,
            purchase_date=body.purchase_date,
            status="in_stock",
        )
        item.tags = tags
        db.add(item)
        created.append(item)

        # 如果提供了 weight 或 size，创建规格记录
        if body.weight is not None or body.size is not None:
            spec = ItemSpec(
                item_id=item.id,
                weight=body.weight,
                size=body.size,
                # 其他规格字段留空
            )
            db.add(spec)

    db.commit()
    for item in created:
        db.refresh(item)

    # 重新查询以确保关联数据已加载
    ids = [it.id for it in created]
    items_orm = (
        db.query(Item)
        .options(*_load_options())
        .filter(Item.id.in_(ids))
        .all()
    )
    return ApiResponse(data=[_to_item_out(it) for it in items_orm])


@router.post(
    "",
    response_model=ApiResponse[ItemOut],
    status_code=status.HTTP_201_CREATED,
    summary="单件入库",
)
def create_item(
    body: ItemCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[ItemOut]:
    # 1. 验证材质、器型、供货商（提前，以便生成 SKU 时使用材质名称）
    _validate_material_type(body.material_id, body.type_id, db)
    if body.supplier_id and not db.get(Supplier, body.supplier_id):
        raise HTTPException(status_code=404, detail="供货商不存在")

    # 2. SKU 自动生成（如果未提供）
    sku_code = body.sku_code
    if not sku_code:
        # 获取材质名称，取前两个字符作为前缀
        material = db.get(DictMaterial, body.material_id)
        # 材质已由 _validate_material_type 验证存在，这里直接使用
        material_name = material.name.strip()
        if len(material_name) >= 2:
            prefix = material_name[:2]
        else:
            prefix = material_name
        prefix = prefix.upper()
        date_str = datetime.date.today().strftime("%Y%m%d")
        # 生成一个 SKU
        skus = _generate_skus(db, prefix, date_str, quantity=1)
        sku_code = skus[0]
    else:
        # 校验唯一性
        if db.query(Item).filter(Item.sku_code == sku_code).first():
            raise HTTPException(status_code=400, detail=f"SKU 编号「{sku_code}」已存在")

    # 3. 验证批次（如果提供了 batch_id）
    batch = None
    if body.batch_id is not None:
        batch = db.get(Batch, body.batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="批次不存在")
        # 验证材质匹配（可选，但建议）
        if batch.material_id != body.material_id:
            raise HTTPException(status_code=400, detail="批次材质与货品材质不一致")
        # 通货：cost_price 必须为空
        if body.cost_price is not None:
            raise HTTPException(status_code=400, detail="通货货品不应填写进价（cost_price），成本由分摊算法分配")
        allocated_cost = None  # 稍后由分摊填充
    else:
        # 高货：cost_price 必填
        if body.cost_price is None:
            raise HTTPException(status_code=400, detail="高货必须填写进价（cost_price）")
        allocated_cost = body.cost_price

    # 4. 标签解析
    tags = _resolve_tags(body.tag_ids, db)

    # 5. 创建货品记录
    item = Item(
        sku_code=sku_code,
        name=body.name,
        batch_id=body.batch_id,
        material_id=body.material_id,
        type_id=body.type_id,
        cost_price=body.cost_price,
        allocated_cost=allocated_cost,
        selling_price=body.selling_price,
        floor_price=body.floor_price,
        origin=body.origin,
        counter=body.counter,
        cert_no=body.cert_no,
        notes=body.notes,
        supplier_id=body.supplier_id,
        status="in_stock",
        purchase_date=body.purchase_date,
    )
    item.tags = tags
    db.add(item)
    db.commit()
    db.refresh(item)

    # 6. 创建规格记录（如果提供了 spec）
    if body.spec is not None:
        spec = ItemSpec(
            item_id=item.id,
            weight=body.spec.weight,
            metal_weight=body.spec.metal_weight,
            size=body.spec.size,
            bracelet_size=body.spec.bracelet_size,
            bead_count=body.spec.bead_count,
            bead_diameter=body.spec.bead_diameter,
            ring_size=body.spec.ring_size,
        )
        db.add(spec)
        db.commit()
        db.refresh(spec)

    # 7. 重新加载完整数据并返回
    item = _get_item_or_404(item.id, db)
    return ApiResponse(data=_to_item_out(item))


@router.get(
    "/{item_id}",
    response_model=ApiResponse[ItemOut],
    summary="货品详情",
    description="返回货品完整信息，含关联的材质、器型、标签、图片列表。",
)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[ItemOut]:
    item = _get_item_or_404(item_id, db)
    return ApiResponse(data=_to_item_out(item))


@router.put(
    "/{item_id}",
    response_model=ApiResponse[ItemOut],
    summary="编辑货品",
    description="部分更新，只传需要修改的字段。tag_ids 传空列表 [] 表示清空所有标签。spec 字段可更新规格参数。",
)
def update_item(
    item_id: int,
    body: ItemUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[ItemOut]:
    item = _get_item_or_404(item_id, db)

    # 状态校验：不允许通过编辑接口将状态改为 sold
    if body.status is not None and body.status not in _EDITABLE_STATUS:
        raise HTTPException(
            status_code=400,
            detail=f"不允许将状态改为「{body.status}」，sold 状态由销售接口管理",
        )

    # 材质/器型变更校验
    new_material_id = body.material_id if body.material_id is not None else item.material_id
    new_type_id = body.type_id if body.type_id is not None else item.type_id
    if body.material_id is not None or body.type_id is not None:
        _validate_material_type(new_material_id, new_type_id, db)

    # 供货商校验
    if body.supplier_id is not None and not db.get(Supplier, body.supplier_id):
        raise HTTPException(status_code=404, detail="供货商不存在")

    # 批次校验与更新
    if body.batch_id is not None:
        batch = db.get(Batch, body.batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="批次不存在")
        # 验证批次材质与货品材质匹配（如果材质也更新了，使用新材质）
        effective_material_id = body.material_id if body.material_id is not None else item.material_id
        if batch.material_id != effective_material_id:
            raise HTTPException(
                status_code=400,
                detail=f"批次「{batch.batch_code}」的材质与货品材质不一致"
            )
        # 如果关联到批次（通货），cost_price 必须为空
        if body.cost_price is not None:
            raise HTTPException(
                status_code=400,
                detail="通货货品（关联批次）不应填写进价（cost_price），成本由分摊算法分配"
            )
        item.batch_id = body.batch_id
        # 清空 cost_price（即使 body.cost_price 为 None）
        item.cost_price = None

    # 逐字段更新（None 表示未传，跳过；显式传 None 需要用 UNSET 机制，这里简化处理）
    if body.sku_code is not None:
        # SKU 唯一性校验（不能与其他未删除货品重复）
        if body.sku_code != item.sku_code:
            existing = db.query(Item).filter(
                Item.sku_code == body.sku_code,
                Item.is_deleted == False,
                Item.id != item.id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"SKU 编号「{body.sku_code}」已存在"
                )
        item.sku_code = body.sku_code
    if body.name is not None:
        item.name = body.name
    if body.material_id is not None:
        item.material_id = body.material_id
    if body.type_id is not None:
        item.type_id = body.type_id
    if body.cost_price is not None:
        # 如果货品关联批次（通货），不允许设置 cost_price
        if item.batch_id is not None:
            raise HTTPException(
                status_code=400,
                detail="通货货品（关联批次）不应填写进价（cost_price），成本由分摊算法分配"
            )
        item.cost_price = body.cost_price
    if body.selling_price is not None:
        item.selling_price = body.selling_price
    if body.floor_price is not None:
        item.floor_price = body.floor_price
    if body.origin is not None:
        item.origin = body.origin
    if body.counter is not None:
        item.counter = body.counter
    if body.cert_no is not None:
        item.cert_no = body.cert_no
    if body.notes is not None:
        item.notes = body.notes
    if body.supplier_id is not None:
        item.supplier_id = body.supplier_id
    if body.purchase_date is not None:
        item.purchase_date = body.purchase_date
    if body.status is not None:
        item.status = body.status

    # 标签更新：tag_ids 为 None 表示不修改；传空列表表示清空
    if body.tag_ids is not None:
        item.tags = _resolve_tags(body.tag_ids, db)

    # 规格参数更新
    if body.spec is not None:
        spec_data = body.spec
        if item.spec:
            # 更新现有规格记录
            spec = item.spec
            if spec_data.weight is not None:
                spec.weight = spec_data.weight
            if spec_data.metal_weight is not None:
                spec.metal_weight = spec_data.metal_weight
            if spec_data.size is not None:
                spec.size = spec_data.size
            if spec_data.bracelet_size is not None:
                spec.bracelet_size = spec_data.bracelet_size
            if spec_data.bead_count is not None:
                spec.bead_count = spec_data.bead_count
            if spec_data.bead_diameter is not None:
                spec.bead_diameter = spec_data.bead_diameter
            if spec_data.ring_size is not None:
                spec.ring_size = spec_data.ring_size
        else:
            # 创建新规格记录
            spec = ItemSpec(
                item_id=item.id,
                weight=spec_data.weight,
                metal_weight=spec_data.metal_weight,
                size=spec_data.size,
                bracelet_size=spec_data.bracelet_size,
                bead_count=spec_data.bead_count,
                bead_diameter=spec_data.bead_diameter,
                ring_size=spec_data.ring_size,
            )
            db.add(spec)

    db.commit()
    item = _get_item_or_404(item_id, db)
    return ApiResponse(data=_to_item_out(item))


@router.delete(
    "/{item_id}",
    response_model=ApiResponse[None],
    summary="删除货品（软删除）",
)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[None]:
    item = (
        db.query(Item)
        .filter(Item.id == item_id, Item.is_deleted == False)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="货品不存在或已删除")
    item.is_deleted = True
    db.commit()
    return ApiResponse(message="已删除")
