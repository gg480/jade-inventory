"""
字典管理路由 — 材质 / 器型 / 标签三级分类的 CRUD。

所有删除操作均为软删除（is_active = false），不物理删除，
保证已关联货品的历史数据不受影响。
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from database import get_db
from models import DictMaterial, DictTag, DictType
from schemas import (
    ApiResponse,
    DictMaterialCreate,
    DictMaterialOut,
    DictMaterialUpdate,
    DictTagCreate,
    DictTagOut,
    DictTagUpdate,
    DictTypeCreate,
    DictTypeOut,
    DictTypeUpdate,
)

router = APIRouter(prefix="/dicts", tags=["字典管理"])


# ══════════════════════════════════════════════
# 材质（dict_material）
# ══════════════════════════════════════════════

@router.get(
    "/materials",
    response_model=ApiResponse[List[DictMaterialOut]],
    summary="获取材质列表",
    description="返回所有材质；默认只返回启用的，传 include_inactive=true 返回全部。",
)
def list_materials(
    include_inactive: bool = Query(False, description="是否包含已停用的材质"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[DictMaterialOut]]:
    q = db.query(DictMaterial)
    if not include_inactive:
        q = q.filter(DictMaterial.is_active == True)
    materials = q.order_by(DictMaterial.sort_order, DictMaterial.id).all()
    return ApiResponse(data=[DictMaterialOut.model_validate(m) for m in materials])


@router.post(
    "/materials",
    response_model=ApiResponse[DictMaterialOut],
    status_code=status.HTTP_201_CREATED,
    summary="新增材质",
)
def create_material(
    body: DictMaterialCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[DictMaterialOut]:
    # 名称唯一性校验（包含已停用的，防止激活冲突）
    if db.query(DictMaterial).filter(DictMaterial.name == body.name).first():
        raise HTTPException(status_code=400, detail=f"材质名称「{body.name}」已存在")
    m = DictMaterial(name=body.name, sort_order=body.sort_order, is_active=True)
    db.add(m)
    db.commit()
    db.refresh(m)
    return ApiResponse(data=DictMaterialOut.model_validate(m))


@router.put(
    "/materials/{material_id}",
    response_model=ApiResponse[DictMaterialOut],
    summary="编辑材质",
)
def update_material(
    material_id: int,
    body: DictMaterialUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[DictMaterialOut]:
    m = db.get(DictMaterial, material_id)
    if not m:
        raise HTTPException(status_code=404, detail="材质不存在")
    # 名称改变时检查重复（排除自身）
    if body.name is not None and body.name != m.name:
        if db.query(DictMaterial).filter(DictMaterial.name == body.name).first():
            raise HTTPException(status_code=400, detail=f"材质名称「{body.name}」已存在")
        m.name = body.name
    if body.sort_order is not None:
        m.sort_order = body.sort_order
    if body.is_active is not None:
        m.is_active = body.is_active
    db.commit()
    db.refresh(m)
    return ApiResponse(data=DictMaterialOut.model_validate(m))


@router.delete(
    "/materials/{material_id}",
    response_model=ApiResponse[None],
    summary="停用材质（软删除）",
)
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[None]:
    m = db.get(DictMaterial, material_id)
    if not m:
        raise HTTPException(status_code=404, detail="材质不存在")
    m.is_active = False
    db.commit()
    return ApiResponse(message="已停用")


# ══════════════════════════════════════════════
# 器型（dict_type）
# ══════════════════════════════════════════════

@router.get(
    "/types",
    response_model=ApiResponse[List[DictTypeOut]],
    summary="获取器型列表",
    description="支持按 material_id 筛选；默认只返回启用的。",
)
def list_types(
    material_id: Optional[int] = Query(None, description="按材质 ID 筛选"),
    include_inactive: bool = Query(False, description="是否包含已停用的器型"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[DictTypeOut]]:
    q = db.query(DictType)
    if material_id is not None:
        q = q.filter(DictType.material_id == material_id)
    if not include_inactive:
        q = q.filter(DictType.is_active == True)
    types = q.order_by(DictType.material_id, DictType.sort_order, DictType.id).all()
    return ApiResponse(data=[DictTypeOut.model_validate(t) for t in types])


@router.post(
    "/types",
    response_model=ApiResponse[DictTypeOut],
    status_code=status.HTTP_201_CREATED,
    summary="新增器型",
)
def create_type(
    body: DictTypeCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[DictTypeOut]:
    # 验证材质存在
    if not db.get(DictMaterial, body.material_id):
        raise HTTPException(status_code=404, detail="材质不存在")
    # 同一材质下名称唯一
    exists = (
        db.query(DictType)
        .filter(
            and_(DictType.material_id == body.material_id, DictType.name == body.name)
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=400,
            detail=f"该材质下器型名称「{body.name}」已存在",
        )
    t = DictType(
        material_id=body.material_id,
        name=body.name,
        sort_order=body.sort_order,
        is_active=True,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return ApiResponse(data=DictTypeOut.model_validate(t))


@router.put(
    "/types/{type_id}",
    response_model=ApiResponse[DictTypeOut],
    summary="编辑器型",
)
def update_type(
    type_id: int,
    body: DictTypeUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[DictTypeOut]:
    t = db.get(DictType, type_id)
    if not t:
        raise HTTPException(status_code=404, detail="器型不存在")
    if body.name is not None and body.name != t.name:
        exists = (
            db.query(DictType)
            .filter(
                and_(
                    DictType.material_id == t.material_id,
                    DictType.name == body.name,
                    DictType.id != type_id,
                )
            )
            .first()
        )
        if exists:
            raise HTTPException(
                status_code=400,
                detail=f"该材质下器型名称「{body.name}」已存在",
            )
        t.name = body.name
    if body.sort_order is not None:
        t.sort_order = body.sort_order
    if body.is_active is not None:
        t.is_active = body.is_active
    db.commit()
    db.refresh(t)
    return ApiResponse(data=DictTypeOut.model_validate(t))


@router.delete(
    "/types/{type_id}",
    response_model=ApiResponse[None],
    summary="停用器型（软删除）",
)
def delete_type(
    type_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[None]:
    t = db.get(DictType, type_id)
    if not t:
        raise HTTPException(status_code=404, detail="器型不存在")
    t.is_active = False
    db.commit()
    return ApiResponse(message="已停用")


# ══════════════════════════════════════════════
# 标签（dict_tag）
# ══════════════════════════════════════════════

@router.get(
    "/tags",
    response_model=ApiResponse[List[DictTagOut]],
    summary="获取标签列表",
    description="支持按 group_name 筛选；默认只返回启用的。",
)
def list_tags(
    group_name: Optional[str] = Query(None, description="按分组名筛选，如：种水、颜色"),
    include_inactive: bool = Query(False, description="是否包含已停用的标签"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[DictTagOut]]:
    q = db.query(DictTag)
    if group_name is not None:
        q = q.filter(DictTag.group_name == group_name)
    if not include_inactive:
        q = q.filter(DictTag.is_active == True)
    tags = q.order_by(DictTag.group_name, DictTag.id).all()
    return ApiResponse(data=[DictTagOut.model_validate(tag) for tag in tags])


@router.post(
    "/tags",
    response_model=ApiResponse[DictTagOut],
    status_code=status.HTTP_201_CREATED,
    summary="新增标签",
)
def create_tag(
    body: DictTagCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[DictTagOut]:
    if db.query(DictTag).filter(DictTag.name == body.name).first():
        raise HTTPException(status_code=400, detail=f"标签名称「{body.name}」已存在")
    tag = DictTag(name=body.name, group_name=body.group_name, is_active=True)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return ApiResponse(data=DictTagOut.model_validate(tag))


@router.put(
    "/tags/{tag_id}",
    response_model=ApiResponse[DictTagOut],
    summary="编辑标签",
)
def update_tag(
    tag_id: int,
    body: DictTagUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[DictTagOut]:
    tag = db.get(DictTag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    if body.name is not None and body.name != tag.name:
        if (
            db.query(DictTag)
            .filter(DictTag.name == body.name, DictTag.id != tag_id)
            .first()
        ):
            raise HTTPException(status_code=400, detail=f"标签名称「{body.name}」已存在")
        tag.name = body.name
    if body.group_name is not None:
        tag.group_name = body.group_name
    if body.is_active is not None:
        tag.is_active = body.is_active
    db.commit()
    db.refresh(tag)
    return ApiResponse(data=DictTagOut.model_validate(tag))


@router.delete(
    "/tags/{tag_id}",
    response_model=ApiResponse[None],
    summary="停用标签（软删除）",
)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[None]:
    tag = db.get(DictTag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    tag.is_active = False
    db.commit()
    return ApiResponse(message="已停用")
