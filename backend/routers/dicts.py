"""
字典管理路由 — 材质 / 器型 / 标签 / 系统配置的 CRUD。

所有删除操作均为软删除（is_active = false），不物理删除，
保证已关联货品的历史数据不受影响。
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import DictMaterial, DictTag, DictType, SysConfig
from schemas import (
    ApiResponse,
    ConfigOut,
    ConfigUpdate,
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
    # 调试：打印第一个材质的属性
    if materials:
        m = materials[0]
        print(f"[DEBUG] First material: id={m.id}, name={m.name}, sub_type={m.sub_type}, origin={m.origin}, cost_per_gram={m.cost_per_gram}")
        print(f"[DEBUG] Material object dict: {m.__dict__ if hasattr(m, '__dict__') else 'no __dict__'}")
        # 测试序列化
        out = DictMaterialOut.model_validate(m)
        print(f"[DEBUG] Serialized dict: {out.model_dump()}")
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
        raise HTTPException(
            status_code=400,
            detail={"code": 400, "message": f"材质「{body.name}」已存在"}
        )
    print(f"[DEBUG] Creating material: name={body.name}, sub_type={body.sub_type}, origin={body.origin}, cost_per_gram={body.cost_per_gram}, sort_order={body.sort_order}")
    print(f"[DEBUG] Body dict: {body.model_dump()}")
    m = DictMaterial(
        name=body.name,
        sub_type=body.sub_type,
        origin=body.origin,
        cost_per_gram=body.cost_per_gram,
        sort_order=body.sort_order,
        is_active=True,
    )
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
            raise HTTPException(
                status_code=400,
                detail={"code": 400, "message": f"材质「{body.name}」已存在"}
            )
        m.name = body.name
    if body.sub_type is not None:
        m.sub_type = body.sub_type
    if body.origin is not None:
        m.origin = body.origin
    if body.cost_per_gram is not None:
        m.cost_per_gram = body.cost_per_gram
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
# 器型（dict_type）— 独立于材质，跨材质通用
# ══════════════════════════════════════════════

@router.get(
    "/types",
    response_model=ApiResponse[List[DictTypeOut]],
    summary="获取器型列表",
    description="返回所有器型；默认只返回启用的，传 include_inactive=true 返回全部。",
)
def list_types(
    include_inactive: bool = Query(False, description="是否包含已停用的器型"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[DictTypeOut]]:
    q = db.query(DictType)
    if not include_inactive:
        q = q.filter(DictType.is_active == True)
    types = q.order_by(DictType.sort_order, DictType.id).all()
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
    # 名称唯一性校验（包含已停用的，防止激活冲突）
    if db.query(DictType).filter(DictType.name == body.name).first():
        raise HTTPException(
            status_code=400,
            detail={"code": 400, "message": f"器型「{body.name}」已存在"}
        )
    t = DictType(
        name=body.name,
        spec_fields=body.spec_fields,
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
        if db.query(DictType).filter(DictType.name == body.name).first():
            raise HTTPException(
                status_code=400,
                detail={"code": 400, "message": f"器型「{body.name}」已存在"}
            )
        t.name = body.name
    if body.spec_fields is not None:
        t.spec_fields = body.spec_fields
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
        raise HTTPException(
            status_code=400,
            detail={"code": 400, "message": f"标签「{body.name}」已存在"}
        )
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
            raise HTTPException(
                status_code=400,
                detail={"code": 400, "message": f"标签「{body.name}」已存在"}
            )
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


# ══════════════════════════════════════════════
# 系统配置（sys_config）
# ══════════════════════════════════════════════

router_config = APIRouter(prefix="/config", tags=["系统配置"])


@router_config.get(
    "/",
    response_model=ApiResponse[List[ConfigOut]],
    summary="获取所有系统配置",
)
def list_configs(
    db: Session = Depends(get_db),
) -> ApiResponse[List[ConfigOut]]:
    configs = db.query(SysConfig).order_by(SysConfig.key).all()
    return ApiResponse(data=[ConfigOut.model_validate(c) for c in configs])


@router_config.put(
    "/{key}",
    response_model=ApiResponse[ConfigOut],
    summary="更新系统配置",
)
def update_config(
    key: str,
    body: ConfigUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[ConfigOut]:
    config = db.query(SysConfig).filter(SysConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置项不存在")
    config.value = body.value
    db.commit()
    db.refresh(config)
    return ApiResponse(data=ConfigOut.model_validate(config))


# 配置路由已直接挂载到主应用（main.py）