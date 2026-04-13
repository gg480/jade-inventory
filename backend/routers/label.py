"""
标签打印路由 — 条码生成、标签数据查询、批量标签打印。

核心流程：入库 → 打印标签（含 Code128 条码）→ 贴在货品上 → 手机扫码销售。
技术方案：python-barcode 生成 Code128 条码 PNG，通过 API 返回 base64 供前端渲染打印。
"""

import base64
import io
import os
from typing import List, Optional

from barcode import Code128
from barcode.writer import ImageWriter
from fastapi import APIRouter, Depends, HTTPException, Query
from PIL import Image
from sqlalchemy.orm import Session, selectinload

from config import IMAGE_DIR
from database import get_db
from models import DictTag, Item, ItemImage
from schemas import ApiResponse, ItemListItem

router = APIRouter(prefix="/labels", tags=["标签打印"])

# 条码图片缓存目录
BARCODE_DIR = IMAGE_DIR.parent / "barcodes"
BARCODE_DIR.mkdir(parents=True, exist_ok=True)


def _generate_barcode_base64(sku_code: str) -> str:
    """生成 Code128 条码 PNG，返回 base64 编码字符串。"""
    # 生成条码 SVG，然后转 PNG
    barcode = Code128(sku_code, writer=ImageWriter())
    buffer = io.BytesIO()
    barcode.write(buffer)
    buffer.seek(0)
    img = Image.open(buffer)

    # 缩放到合适的尺寸（宽度400px，高度按比例）
    target_width = 400
    ratio = target_width / img.width
    target_height = int(img.height * ratio)
    img = img.resize((target_width, target_height), Image.LANCZOS)

    # 转为 PNG base64
    png_buffer = io.BytesIO()
    img.save(png_buffer, format="PNG", optimize=True)
    png_buffer.seek(0)
    b64 = base64.b64encode(png_buffer.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _get_cover_image(item: Item) -> Optional[str]:
    """获取货品封面图路径。"""
    for img in item.images:
        if img.is_cover:
            return img.thumbnail_path or img.filename
    return item.images[0].thumbnail_path if item.images else None


def _to_label_item(item: Item) -> dict:
    """将货品转换为标签数据（含条码和封面图）。"""
    return {
        "id": item.id,
        "sku_code": item.sku_code,
        "name": item.name,
        "material_name": item.material.name,
        "type_name": item.type.name if item.type else None,
        "selling_price": item.selling_price,
        "floor_price": item.floor_price,
        "cost_price": item.cost_price,
        "allocated_cost": item.allocated_cost,
        "origin": item.origin,
        "counter": item.counter,
        "cert_no": item.cert_no,
        "purchase_date": item.purchase_date.isoformat() if item.purchase_date else None,
        "barcode": _generate_barcode_base64(item.sku_code),
        "cover_image": _get_cover_image(item),
    }


# ──────────────────────────────────────────────
# 端点
# ──────────────────────────────────────────────

@router.get(
    "/item/{item_id}",
    summary="单件标签数据",
    description="返回指定货品的完整标签数据，包含 Code128 条码 base64 图片，供前端渲染打印。",
)
def get_label(
    item_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse:
    """获取单件货品的标签数据（含条码）。"""
    item = (
        db.query(Item)
        .options(
            selectinload(Item.material),
            selectinload(Item.type),
            selectinload(Item.images),
        )
        .filter(Item.id == item_id, Item.is_deleted == False)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="货品不存在或已删除")

    return ApiResponse(data=_to_label_item(item))


@router.post(
    "/batch",
    summary="批量标签数据",
    description="批量获取多个货品的标签数据，支持从库存列表勾选后批量打印。",
)
def get_batch_labels(
    item_ids: List[int] = Query(..., description="货品ID列表"),
    db: Session = Depends(get_db),
) -> ApiResponse:
    """批量获取标签数据。"""
    items = (
        db.query(Item)
        .options(
            selectinload(Item.material),
            selectinload(Item.type),
            selectinload(Item.images),
        )
        .filter(Item.id.in_(item_ids), Item.is_deleted == False)
        .all()
    )

    if not items:
        raise HTTPException(status_code=404, detail="未找到有效货品")

    labels = [_to_label_item(item) for item in items]
    return ApiResponse(data=labels)


@router.get(
    "/barcode/{sku_code}",
    summary="条码图片",
    description="根据 SKU 编号生成 Code128 条码 PNG 图片，直接返回图片二进制。",
)
def get_barcode_image(
    sku_code: str,
    db: Session = Depends(get_db),
):
    """生成并返回条码图片。"""
    # 检查货品是否存在
    item = db.query(Item).filter(
        Item.sku_code == sku_code, Item.is_deleted == False
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"货品编号「{sku_code}」不存在")

    # 生成条码
    barcode = Code128(sku_code, writer=ImageWriter())
    buffer = io.BytesIO()
    barcode.write(buffer)
    buffer.seek(0)
    img = Image.open(buffer)

    # 缩放到合适尺寸
    target_width = 600
    ratio = target_width / img.width
    target_height = int(img.height * ratio)
    img = img.resize((target_width, target_height), Image.LANCZOS)

    # 返回 PNG
    png_buffer = io.BytesIO()
    img.save(png_buffer, format="PNG", optimize=True)
    png_buffer.seek(0)

    from fastapi.responses import Response
    return Response(
        content=png_buffer.read(),
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=barcode_{sku_code}.png"},
    )


@router.get(
    "/lookup",
    summary="SKU 扫码查询",
    description="通过 SKU 编号查询货品信息，供手机扫码后快速获取货品详情并进入销售流程。",
)
def lookup_by_sku(
    sku: str = Query(..., description="SKU 编号（扫描条码值）"),
    db: Session = Depends(get_db),
) -> ApiResponse:
    """扫码查询货品信息。"""
    item = (
        db.query(Item)
        .options(
            selectinload(Item.material),
            selectinload(Item.type),
            selectinload(Item.images),
            selectinload(Item.spec),
            selectinload(Item.tags),
        )
        .filter(Item.sku_code == sku, Item.is_deleted == False)
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail=f"未找到编号为「{sku}」的货品")

    # 获取成本
    cost = item.allocated_cost if item.allocated_cost is not None else item.cost_price
    if cost is None:
        cost = 0.0

    return ApiResponse(data={
        "id": item.id,
        "sku_code": item.sku_code,
        "name": item.name,
        "material_name": item.material.name,
        "type_name": item.type.name if item.type else None,
        "cost": round(cost, 2),
        "selling_price": item.selling_price,
        "floor_price": item.floor_price,
        "status": item.status,
        "origin": item.origin,
        "counter": item.counter,
        "cert_no": item.cert_no,
        "tags": [{"id": t.id, "name": t.name} for t in item.tags],
        "cover_image": _get_cover_image(item),
        "spec": {
            "weight": item.spec.weight if item.spec else None,
            "metal_weight": item.spec.metal_weight if item.spec else None,
            "size": item.spec.size if item.spec else None,
            "bracelet_size": item.spec.bracelet_size if item.spec else None,
            "bead_count": item.spec.bead_count if item.spec else None,
            "bead_diameter": item.spec.bead_diameter if item.spec else None,
            "ring_size": item.spec.ring_size if item.spec else None,
        },
        "purchase_date": item.purchase_date.isoformat() if item.purchase_date else None,
    })
