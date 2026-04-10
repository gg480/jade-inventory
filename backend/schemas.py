"""
Pydantic V2 请求/响应模型 — 对应 TECH_SPEC.md 第3节所有 API 端点。

命名规则：
- *Create  → POST 请求体
- *Update  → PUT 请求体（字段全部可选，支持部分更新）
- *Out     → 响应体（单条记录）
- *ListOut → 分页列表响应体
- ApiResponse[T] → 统一外层包装 { code, data, message }
"""

from __future__ import annotations

import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# ──────────────────────────────────────────────
# 泛型响应包装
# ──────────────────────────────────────────────
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """所有接口的统一响应格式：{ code, data, message }"""

    code: int = 0
    data: Optional[T] = None
    message: str = "ok"


# ──────────────────────────────────────────────
# 分页通用
# ──────────────────────────────────────────────
class Pagination(BaseModel):
    """分页元数据"""

    total: int = Field(description="总记录数")
    page: int = Field(description="当前页（从1开始）")
    size: int = Field(description="每页条数")
    pages: int = Field(description="总页数")


# ──────────────────────────────────────────────
# 字典 — 材质
# ──────────────────────────────────────────────
class DictMaterialCreate(BaseModel):
    """新增材质请求体"""

    name: str = Field(max_length=50, description="材质名称")
    sort_order: int = Field(default=0, description="排序权重，数字越小越靠前")


class DictMaterialUpdate(BaseModel):
    """编辑材质请求体（全部字段可选）"""

    name: Optional[str] = Field(default=None, max_length=50)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class DictMaterialOut(BaseModel):
    """材质响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sort_order: int
    is_active: bool


# ──────────────────────────────────────────────
# 字典 — 器型
# ──────────────────────────────────────────────
class DictTypeCreate(BaseModel):
    """新增器型请求体"""

    material_id: int = Field(description="所属材质 ID")
    name: str = Field(max_length=50, description="器型名称")
    sort_order: int = Field(default=0)


class DictTypeUpdate(BaseModel):
    """编辑器型请求体（全部字段可选）"""

    name: Optional[str] = Field(default=None, max_length=50)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class DictTypeOut(BaseModel):
    """器型响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    material_id: int
    name: str
    sort_order: int
    is_active: bool


# ──────────────────────────────────────────────
# 字典 — 标签
# ──────────────────────────────────────────────
class DictTagCreate(BaseModel):
    """新增标签请求体"""

    name: str = Field(max_length=50, description="标签名称")
    group_name: Optional[str] = Field(
        default=None, max_length=50, description="分组名，如：种水、颜色、工艺、题材"
    )


class DictTagUpdate(BaseModel):
    """编辑标签请求体（全部字段可选）"""

    name: Optional[str] = Field(default=None, max_length=50)
    group_name: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = None


class DictTagOut(BaseModel):
    """标签响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    group_name: Optional[str]
    is_active: bool


# ──────────────────────────────────────────────
# 供货商
# ──────────────────────────────────────────────
class SupplierCreate(BaseModel):
    """新增供货商请求体"""

    name: str = Field(max_length=100)
    contact: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None


class SupplierUpdate(BaseModel):
    """编辑供货商请求体（全部字段可选）"""

    name: Optional[str] = Field(default=None, max_length=100)
    contact: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierOut(BaseModel):
    """供货商响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    contact: Optional[str]
    notes: Optional[str]
    is_active: bool


# ──────────────────────────────────────────────
# 货品图片
# ──────────────────────────────────────────────
class ItemImageOut(BaseModel):
    """货品图片响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    filename: str
    is_cover: bool
    created_at: datetime.datetime


# ──────────────────────────────────────────────
# 货品
# ──────────────────────────────────────────────
class ItemCreate(BaseModel):
    """单件入库请求体"""

    sku_code: str = Field(max_length=50, description="唯一编号，如 FC-20240315-001")
    batch_code: Optional[str] = Field(
        default=None, max_length=50, description="批次款号（通货填写，高货留空）"
    )
    material_id: int = Field(description="材质 ID")
    type_id: Optional[int] = Field(default=None, description="器型 ID")
    tag_ids: List[int] = Field(default_factory=list, description="标签 ID 列表")
    cost_price: float = Field(gt=0, description="进货成本（元）")
    selling_price: float = Field(gt=0, description="标价（元）")
    weight: Optional[float] = Field(default=None, description="克重（克）")
    size: Optional[str] = Field(default=None, max_length=100, description="尺寸描述")
    cert_no: Optional[str] = Field(default=None, max_length=100, description="证书编号")
    notes: Optional[str] = Field(default=None, description="备注")
    supplier_id: Optional[int] = Field(default=None, description="供货商 ID")
    purchase_date: Optional[datetime.date] = Field(default=None, description="进货日期")


class ItemBatchCreate(BaseModel):
    """批量入库请求体 — 同款 N 件，系统自动生成 SKU 编号"""

    batch_code: str = Field(max_length=50, description="款号（同款货品共用）")
    material_id: int = Field(description="材质 ID")
    type_id: Optional[int] = Field(default=None, description="器型 ID")
    tag_ids: List[int] = Field(default_factory=list, description="标签 ID 列表")
    quantity: int = Field(ge=1, le=500, description="数量")
    cost_price: float = Field(gt=0, description="单件进货成本（元）")
    selling_price: float = Field(gt=0, description="单件标价（元）")
    # SKU 前缀，如 "SJ"，生成规则：{sku_prefix}-{YYYYMMDD}-{三位序号}
    sku_prefix: Optional[str] = Field(
        default=None, max_length=20, description="SKU 前缀，留空则用 ITEM"
    )
    weight: Optional[float] = None
    size: Optional[str] = Field(default=None, max_length=100)
    supplier_id: Optional[int] = None
    purchase_date: Optional[datetime.date] = None


class ItemUpdate(BaseModel):
    """编辑货品请求体（全部字段可选，支持部分更新）"""

    batch_code: Optional[str] = Field(default=None, max_length=50)
    material_id: Optional[int] = None
    type_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    cost_price: Optional[float] = Field(default=None, gt=0)
    selling_price: Optional[float] = Field(default=None, gt=0)
    weight: Optional[float] = None
    size: Optional[str] = Field(default=None, max_length=100)
    cert_no: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None
    supplier_id: Optional[int] = None
    purchase_date: Optional[datetime.date] = None
    status: Optional[str] = Field(
        default=None,
        description="状态：in_stock / lent_out / returned（sold 状态由销售接口管理）",
    )


class ItemOut(BaseModel):
    """货品详情响应体（含关联对象的展开字段）"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_code: str
    batch_code: Optional[str]
    material_id: int
    material_name: str = Field(description="材质名称（冗余，方便前端展示）")
    type_id: Optional[int]
    type_name: Optional[str] = Field(default=None, description="器型名称")
    cost_price: float
    selling_price: float
    weight: Optional[float]
    size: Optional[str]
    cert_no: Optional[str]
    notes: Optional[str]
    supplier_id: Optional[int]
    supplier_name: Optional[str] = Field(default=None, description="供货商名称")
    status: str
    purchase_date: Optional[datetime.date]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    # 关联对象
    tags: List[DictTagOut] = Field(default_factory=list)
    images: List[ItemImageOut] = Field(default_factory=list)
    # 计算字段
    age_days: Optional[int] = Field(default=None, description="在库天数（purchase_date 到今日）")
    cover_image: Optional[str] = Field(default=None, description="封面图文件名")


class ItemListItem(BaseModel):
    """货品列表条目（轻量版，不含图片列表）"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_code: str
    batch_code: Optional[str]
    material_id: int
    material_name: str
    type_id: Optional[int]
    type_name: Optional[str]
    cost_price: float
    selling_price: float
    status: str
    purchase_date: Optional[datetime.date]
    created_at: datetime.datetime
    tags: List[DictTagOut] = Field(default_factory=list)
    cover_image: Optional[str] = Field(default=None, description="封面图文件名")
    age_days: Optional[int] = None


class ItemListOut(BaseModel):
    """货品分页列表响应体"""

    items: List[ItemListItem]
    pagination: Pagination


# ──────────────────────────────────────────────
# 借出 / 归还
# ──────────────────────────────────────────────
class ItemLendOut(BaseModel):
    """标记借出请求体"""

    lend_to: Optional[str] = Field(
        default=None, max_length=100, description="借出对象（姓名/微信等）"
    )
    notes: Optional[str] = Field(default=None, description="备注")


# ──────────────────────────────────────────────
# 销售记录
# ──────────────────────────────────────────────
class SaleRecordCreate(BaseModel):
    """创建销售记录请求体"""

    item_id: int = Field(description="货品 ID（必须是 in_stock 状态）")
    actual_price: float = Field(gt=0, description="实际成交价（元）")
    channel: str = Field(
        description="销售渠道：store（门店）/ wechat（微信）/ ecommerce（电商）"
    )
    sale_date: datetime.date = Field(description="成交日期")
    customer_note: Optional[str] = Field(default=None, description="客户/交易备注")


class SaleRecordOut(BaseModel):
    """销售记录响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    sku_code: str = Field(description="货品编号（冗余，方便展示）")
    material_name: str = Field(description="材质名称")
    actual_price: float
    channel: str
    sale_date: datetime.date
    customer_note: Optional[str]
    created_at: datetime.datetime
    # 计算字段
    cost_price: float = Field(description="进货成本（来自货品）")
    gross_profit: float = Field(description="毛利 = 成交价 - 进价")
    gross_margin: float = Field(description="毛利率 = 毛利 / 成交价")


class SaleRecordListOut(BaseModel):
    """销售记录分页列表响应体"""

    items: List[SaleRecordOut]
    pagination: Pagination


# ──────────────────────────────────────────────
# 看板 — 统计数据
# ──────────────────────────────────────────────
class ProfitByCategory(BaseModel):
    """按材质的利润统计（对应 /dashboard/profit/by-category）"""

    material_id: int
    material_name: str
    sales_count: int = Field(description="销售件数")
    total_revenue: float = Field(description="销售额合计（元）")
    total_cost: float = Field(description="进货成本合计（元）")
    gross_profit: float = Field(description="毛利合计（元）")
    gross_margin: float = Field(description="毛利率（0~1 之间的小数）")


class ProfitByChannel(BaseModel):
    """按渠道的利润统计（对应 /dashboard/profit/by-channel）"""

    channel: str = Field(description="渠道：store / wechat / ecommerce")
    sales_count: int
    total_revenue: float
    total_cost: float
    gross_profit: float
    gross_margin: float


class SalesTrendItem(BaseModel):
    """按月销售趋势数据点（对应 /dashboard/trend）"""

    year_month: str = Field(description="年月，格式 YYYY-MM")
    sales_count: int
    total_revenue: float
    gross_profit: float


class StockAgingItem(BaseModel):
    """压货预警列表条目（对应 /dashboard/stock-aging）"""

    item_id: int
    sku_code: str
    batch_code: Optional[str]
    material_name: str
    type_name: Optional[str]
    cost_price: float = Field(description="进货成本（占用资金）")
    selling_price: float
    purchase_date: Optional[datetime.date]
    age_days: int = Field(description="在库天数")
    cover_image: Optional[str] = None


class DashboardSummary(BaseModel):
    """首页概览数据（对应 /dashboard/summary）"""

    total_stock: int = Field(description="当前在库件数（in_stock）")
    total_stock_value: float = Field(description="在库商品进价总和（占用资金）")
    lent_out_count: int = Field(description="借出中件数")
    monthly_sales_count: int = Field(description="本月销售件数")
    monthly_revenue: float = Field(description="本月销售额（元）")
    monthly_profit: float = Field(description="本月毛利（元）")
    overage_count: int = Field(description="超过阈值的压货件数（默认90天）")
    overage_value: float = Field(description="压货占用资金（元）")
