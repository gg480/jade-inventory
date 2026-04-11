"""
客户管理路由 — 客户列表、新增、编辑、详情（含购买记录）。

新增客户时自动生成 customer_code 格式：cst + YYYYMMDD + 3位序号（如 cst20260411001）。
"""

import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import Customer, SaleRecord, Item
from schemas import (
    ApiResponse,
    CustomerCreate,
    CustomerDetailOut,
    CustomerOut,
    CustomerUpdate,
    SaleRecordOut,
)

router = APIRouter(prefix="/customers", tags=["客户管理"])


def _generate_customer_code(db: Session) -> str:
    """生成客户编号：cst + YYYYMMDD + 3位序号。

    每天从001开始递增，例：cst20260411001, cst20260411002。
    """
    today_str = datetime.date.today().strftime("%Y%m%d")
    prefix = f"cst{today_str}"

    # 查询今日已有最大序号
    max_code = (
        db.query(Customer.customer_code)
        .filter(Customer.customer_code.like(f"{prefix}%"))
        .order_by(desc(Customer.customer_code))
        .first()
    )

    if not max_code:
        # 今日第一个客户
        serial = "001"
    else:
        # 提取已有序号部分，转整数后+1
        existing_serial = max_code[0][len(prefix):]  # 去掉前缀
        try:
            serial_num = int(existing_serial) + 1
        except ValueError:
            # 如果格式异常，从001开始
            serial_num = 1

        # 格式化为3位数字，不足补零
        serial = f"{serial_num:03d}"

        # 防止序号超出范围（理论上999个客户一天足够）
        if serial_num > 999:
            raise HTTPException(
                status_code=500,
                detail="今日客户数量已超过999个上限，无法生成新编号"
            )

    return f"{prefix}{serial}"


# ══════════════════════════════════════════════
# 客户列表
# ══════════════════════════════════════════════

@router.get(
    "/",
    response_model=ApiResponse[List[CustomerOut]],
    summary="获取客户列表",
    description="支持按姓名、电话、微信号搜索，默认只返回启用的客户。",
)
def list_customers(
    name: Optional[str] = Query(None, description="按姓名模糊搜索"),
    phone: Optional[str] = Query(None, description="按电话搜索（精确匹配）"),
    wechat: Optional[str] = Query(None, description="按微信号搜索（精确匹配）"),
    include_inactive: bool = Query(False, description="是否包含已停用的客户"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[CustomerOut]]:
    q = db.query(Customer)

    if name:
        q = q.filter(Customer.name.ilike(f"%{name}%"))
    if phone:
        q = q.filter(Customer.phone == phone)
    if wechat:
        q = q.filter(Customer.wechat == wechat)

    if not include_inactive:
        q = q.filter(Customer.is_active == True)

    customers = q.order_by(desc(Customer.created_at), Customer.id).all()
    return ApiResponse(data=[CustomerOut.model_validate(c) for c in customers])


# ══════════════════════════════════════════════
# 新增客户
# ══════════════════════════════════════════════

@router.post(
    "/",
    response_model=ApiResponse[CustomerOut],
    status_code=status.HTTP_201_CREATED,
    summary="新增客户",
    description="自动生成客户编号，客户姓名不能重复（包含已停用的客户）。",
)
def create_customer(
    body: CustomerCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[CustomerOut]:
    # 姓名唯一性校验（包含已停用的，防止激活冲突）
    if db.query(Customer).filter(Customer.name == body.name).first():
        raise HTTPException(
            status_code=400,
            detail={"code": 400, "message": f"客户「{body.name}」已存在"}
        )

    # 生成客户编号
    customer_code = _generate_customer_code(db)

    customer = Customer(
        customer_code=customer_code,
        name=body.name,
        phone=body.phone,
        wechat=body.wechat,
        notes=body.notes,
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return ApiResponse(data=CustomerOut.model_validate(customer))


# ══════════════════════════════════════════════
# 编辑客户
# ══════════════════════════════════════════════

@router.put(
    "/{customer_id}",
    response_model=ApiResponse[CustomerOut],
    summary="编辑客户",
    description="支持部分更新，客户姓名不能与其他客户重复。",
)
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[CustomerOut]:
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 姓名改变时检查重复（排除自身）
    if body.name is not None and body.name != customer.name:
        if db.query(Customer).filter(Customer.name == body.name).first():
            raise HTTPException(
                status_code=400,
                detail={"code": 400, "message": f"客户「{body.name}」已存在"}
            )
        customer.name = body.name

    if body.phone is not None:
        customer.phone = body.phone
    if body.wechat is not None:
        customer.wechat = body.wechat
    if body.notes is not None:
        customer.notes = body.notes
    if body.is_active is not None:
        customer.is_active = body.is_active

    db.commit()
    db.refresh(customer)
    return ApiResponse(data=CustomerOut.model_validate(customer))


# ══════════════════════════════════════════════
# 客户详情（含购买记录）
# ══════════════════════════════════════════════

@router.get(
    "/{customer_id}",
    response_model=ApiResponse[CustomerDetailOut],
    summary="获取客户详情",
    description="返回客户基本信息及其购买记录列表。",
)
def get_customer_detail(
    customer_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[CustomerDetailOut]:
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 预加载购买记录及相关联的货品信息
    sale_records = (
        db.query(SaleRecord)
        .options(
            selectinload(SaleRecord.item).selectinload(Item.material),
        )
        .filter(SaleRecord.customer_id == customer_id)
        .order_by(desc(SaleRecord.sale_date), desc(SaleRecord.id))
        .all()
    )

    # 转换购买记录
    purchase_records = []
    for sale in sale_records:
        record = SaleRecordOut.model_validate(sale, from_attributes=True)
        # 填充扩展字段
        record.item_sku = sale.item.sku_code if sale.item else ""
        record.item_name = sale.item.name if sale.item else None
        record.customer_name = customer.name

        # 计算毛利（实际成交价 - 分摊成本）
        allocated_cost = sale.item.allocated_cost if sale.item else 0
        if allocated_cost is None:
            allocated_cost = 0
        record.gross_profit = sale.actual_price - allocated_cost

        purchase_records.append(record)

    # 构建客户详情响应
    detail = CustomerDetailOut.model_validate(customer, from_attributes=True)
    detail.purchase_records = purchase_records

    return ApiResponse(data=detail)