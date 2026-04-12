"""
供应商管理路由 — 供应商列表、新增、编辑。

供应商名称需保持唯一（包含已停用的供应商，防止激活冲突）。
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import get_db
from models import Supplier
from schemas import ApiResponse, SupplierCreate, SupplierOut, SupplierListOut, SupplierUpdate, PaginationMeta

router = APIRouter(prefix="/suppliers", tags=["供应商管理"])


# ══════════════════════════════════════════════
# 供应商列表
# ══════════════════════════════════════════════

@router.get(
    "/",
    response_model=ApiResponse[SupplierListOut],
    summary="获取供应商列表",
    description="支持按名称、联系方式搜索，默认只返回启用的供应商。支持分页。",
)
def list_suppliers(
    name: Optional[str] = Query(None, description="按名称模糊搜索"),
    contact: Optional[str] = Query(None, description="按联系方式搜索（精确匹配）"),
    include_inactive: bool = Query(False, description="是否包含已停用的供应商"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db),
) -> ApiResponse[SupplierListOut]:
    q = db.query(Supplier)

    if name:
        q = q.filter(Supplier.name.ilike(f"%{name}%"))
    if contact:
        q = q.filter(Supplier.contact == contact)

    if not include_inactive:
        q = q.filter(Supplier.is_active == True)

    total = q.count()
    pages = (total + size - 1) // size
    suppliers = q.order_by(desc(Supplier.id)).offset((page - 1) * size).limit(size).all()
    return ApiResponse(
        data=SupplierListOut(
            items=[SupplierOut.model_validate(s) for s in suppliers],
            pagination=PaginationMeta(total=total, page=page, size=size, pages=pages),
        )
    )


# ══════════════════════════════════════════════
# 新增供应商
# ══════════════════════════════════════════════

@router.post(
    "/",
    response_model=ApiResponse[SupplierOut],
    status_code=status.HTTP_201_CREATED,
    summary="新增供应商",
    description="供应商名称不能重复（包含已停用的供应商）。",
)
def create_supplier(
    body: SupplierCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[SupplierOut]:
    # 名称唯一性校验（包含已停用的，防止激活冲突）
    if db.query(Supplier).filter(Supplier.name == body.name).first():
        raise HTTPException(
            status_code=400,
            detail={"code": 400, "message": f"供应商「{body.name}」已存在"}
        )

    supplier = Supplier(
        name=body.name,
        contact=body.contact,
        notes=body.notes,
        is_active=True,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return ApiResponse(data=SupplierOut.model_validate(supplier))


# ══════════════════════════════════════════════
# 编辑供应商
# ══════════════════════════════════════════════

@router.put(
    "/{supplier_id}",
    response_model=ApiResponse[SupplierOut],
    summary="编辑供应商",
    description="支持部分更新，供应商名称不能与其他供应商重复。",
)
def update_supplier(
    supplier_id: int,
    body: SupplierUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[SupplierOut]:
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")

    # 名称改变时检查重复（排除自身）
    if body.name is not None and body.name != supplier.name:
        if db.query(Supplier).filter(Supplier.name == body.name).first():
            raise HTTPException(
                status_code=400,
                detail={"code": 400, "message": f"供应商「{body.name}」已存在"}
            )
        supplier.name = body.name

    if body.contact is not None:
        supplier.contact = body.contact
    if body.notes is not None:
        supplier.notes = body.notes
    if body.is_active is not None:
        supplier.is_active = body.is_active

    db.commit()
    db.refresh(supplier)
    return ApiResponse(data=SupplierOut.model_validate(supplier))


