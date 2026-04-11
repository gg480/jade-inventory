"""
Pydantic V2 请求/响应模型 — 对应 TECH_SPEC.md 第3节所有 API 端点。

使用 Pydantic V2: model_config = ConfigDict(from_attributes=True)

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
# 通用模型
# ──────────────────────────────────────────────
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """所有接口的统一响应格式：{ code, data, message }"""

    code: int = 0
    data: Optional[T] = None
    message: str = "ok"


class PaginationMeta(BaseModel):
    """分页元数据"""

    total: int = Field(description="总记录数")
    page: int = Field(description="当前页（从1开始）")
    size: int = Field(description="每页条数")
    pages: Optional[int] = Field(default=None, description="总页数")


# ──────────────────────────────────────────────
# 字典模型
# ──────────────────────────────────────────────
class DictMaterialCreate(BaseModel):
    """新增材质请求体"""

    name: str = Field(max_length=50, description="材质名称")
    sub_type: Optional[str] = Field(default=None, max_length=50, description="材质子类（如990、淡水珠、k999）")
    origin: Optional[str] = Field(default=None, max_length=100, description="默认产地（如缅甸、浙江）")
    cost_per_gram: Optional[float] = Field(default=None, description="克重单价（贵金属用，如银25、18K金780）")
    sort_order: int = Field(default=0, description="排序权重")


class DictMaterialUpdate(BaseModel):
    """编辑材质请求体（全部字段可选）"""

    name: Optional[str] = Field(default=None, max_length=50)
    sub_type: Optional[str] = Field(default=None, max_length=50)
    origin: Optional[str] = Field(default=None, max_length=100)
    cost_per_gram: Optional[float] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class DictMaterialOut(BaseModel):
    """材质响应体"""

    model_config = ConfigDict(from_attributes=True, exclude_none=False)

    id: int
    name: str
    sub_type: Optional[str] = Field(default=None, exclude=False)
    origin: Optional[str] = Field(default=None, exclude=False)
    cost_per_gram: Optional[float] = Field(default=None, exclude=False)
    sort_order: int
    is_active: bool


class DictTypeCreate(BaseModel):
    """新增器型请求体"""

    name: str = Field(max_length=50, description="器型名称")
    spec_fields: Optional[str] = Field(default=None, description="JSON，该器型需要的规格字段列表")
    sort_order: int = Field(default=0, description="排序权重")


class DictTypeUpdate(BaseModel):
    """编辑器型请求体（全部字段可选）"""

    name: Optional[str] = Field(default=None, max_length=50)
    spec_fields: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class DictTypeOut(BaseModel):
    """器型响应体"""

    model_config = ConfigDict(from_attributes=True, exclude_none=False)

    id: int
    name: str
    spec_fields: Optional[str] = Field(default=None)
    sort_order: int
    is_active: bool


class DictTagCreate(BaseModel):
    """新增标签请求体"""

    name: str = Field(max_length=50, description="标签名称")
    group_name: Optional[str] = Field(
        default=None, max_length=50, description="分组：种水/颜色/工艺/题材"
    )


class DictTagUpdate(BaseModel):
    """编辑标签请求体（全部字段可选）"""

    name: Optional[str] = Field(default=None, max_length=50)
    group_name: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = None


class DictTagOut(BaseModel):
    """标签响应体"""

    model_config = ConfigDict(from_attributes=True, exclude_none=False)

    id: int
    name: str
    group_name: Optional[str] = Field(default=None)
    is_active: bool


class ConfigOut(BaseModel):
    """系统配置响应体"""

    model_config = ConfigDict(from_attributes=True, exclude_none=False)

    key: str
    value: str
    description: Optional[str] = Field(default=None)


class ConfigUpdate(BaseModel):
    """更新系统配置请求体"""

    value: str = Field(description="配置值")


# ──────────────────────────────────────────────
# 供应商/客户模型
# ──────────────────────────────────────────────
class SupplierCreate(BaseModel):
    """新增供货商请求体"""

    name: str = Field(max_length=100, description="名称")
    contact: Optional[str] = Field(default=None, max_length=100, description="联系方式")
    notes: Optional[str] = Field(default=None, description="备注")


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


class CustomerCreate(BaseModel):
    """新增客户请求体"""

    name: str = Field(max_length=100, description="姓名/微信名")
    phone: Optional[str] = Field(default=None, max_length=20, description="电话")
    wechat: Optional[str] = Field(default=None, max_length=100, description="微信号")
    notes: Optional[str] = Field(default=None, description="备注（如'熟客'）")


class CustomerUpdate(BaseModel):
    """编辑客户请求体（全部字段可选）"""

    name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    wechat: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerOut(BaseModel):
    """客户响应体（基础）"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_code: str
    name: str
    phone: Optional[str]
    wechat: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime.datetime


class CustomerDetailOut(CustomerOut):
    """客户详情响应体（含关联购买记录）"""

    purchase_records: List["SaleRecordOut"] = Field(default_factory=list, description="购买记录列表")


# ──────────────────────────────────────────────
# 批次模型
# ──────────────────────────────────────────────
class BatchCreate(BaseModel):
    """创建批次请求体"""

    batch_code: str = Field(max_length=50, description="批次编号")
    material_id: int = Field(description="材质ID")
    type_id: Optional[int] = Field(default=None, description="器型ID")
    quantity: int = Field(description="总数量")
    total_cost: float = Field(description="批次总进价")
    cost_alloc_method: str = Field(description="成本分摊算法: equal / by_weight / by_price")
    supplier_id: Optional[int] = Field(default=None, description="供货商ID")
    purchase_date: Optional[datetime.date] = Field(default=None, description="进货日期")
    notes: Optional[str] = Field(default=None, description="备注")


class BatchUpdate(BaseModel):
    """编辑批次请求体（全部字段可选）"""

    batch_code: Optional[str] = Field(default=None, max_length=50)
    material_id: Optional[int] = None
    type_id: Optional[int] = None
    quantity: Optional[int] = None
    total_cost: Optional[float] = None
    cost_alloc_method: Optional[str] = None
    supplier_id: Optional[int] = None
    purchase_date: Optional[datetime.date] = None
    notes: Optional[str] = None


class BatchOut(BaseModel):
    """批次响应体（含统计字段）"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_code: str
    material_id: int
    material_name: Optional[str] = Field(default=None, description="材质名称")
    type_id: Optional[int]
    type_name: Optional[str] = Field(default=None, description="器型名称")
    quantity: int
    total_cost: float
    cost_alloc_method: str
    supplier_id: Optional[int]
    supplier_name: Optional[str] = Field(default=None, description="供货商名称")
    purchase_date: Optional[datetime.date]
    notes: Optional[str]
    created_at: datetime.datetime
    # 统计字段
    items_count: int = Field(description="关联货品数量")
    sold_count: int = Field(description="已售数量")
    revenue: float = Field(description="已售回款")
    profit: float = Field(description="利润 = 已售回款 - 总进价")
    payback_rate: float = Field(description="回本进度 = 已售回款 / 总进价 (0-1)")
    status: str = Field(description="批次状态: new / selling / paid_back / cleared")


class BatchListOut(BaseModel):
    """批次分页列表响应体"""

    items: List["BatchOut"]
    pagination: PaginationMeta


class BatchDetailOut(BatchOut):
    """批次详情响应体（含关联货品列表）"""

    items: List["ItemListItem"] = Field(default_factory=list, description="关联货品列表")


class BatchAllocItem(BaseModel):
    """成本分摊结果项"""

    sku_code: str
    allocated_cost: float = Field(description="分摊成本")
    floor_price: float = Field(description="底价")


class BatchAllocResult(BaseModel):
    """成本分摊结果列表"""

    items: List[BatchAllocItem] = Field(description="分摊结果列表")


# ──────────────────────────────────────────────
# 货品模型
# ──────────────────────────────────────────────
class ItemSpecCreate(BaseModel):
    """货品规格参数创建"""

    weight: Optional[float] = Field(default=None, description="总克重")
    metal_weight: Optional[float] = Field(default=None, description="金属克重")
    size: Optional[str] = Field(default=None, max_length=100, description="通用尺寸描述")
    bracelet_size: Optional[str] = Field(default=None, max_length=50, description="圈口（手镯）")
    bead_count: Optional[int] = Field(default=None, description="粒数（手串/项链）")
    bead_diameter: Optional[str] = Field(default=None, max_length=50, description="珠子口径")
    ring_size: Optional[str] = Field(default=None, max_length=50, description="戒指尺寸")


class ItemSpecOut(BaseModel):
    """货品规格参数响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    weight: Optional[float]
    metal_weight: Optional[float]
    size: Optional[str]
    bracelet_size: Optional[str]
    bead_count: Optional[int]
    bead_diameter: Optional[str]
    ring_size: Optional[str]


class ItemImageOut(BaseModel):
    """货品图片响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    filename: str
    is_cover: bool
    created_at: datetime.datetime


class ItemBatchCreate(BaseModel):
    """批量入库请求体（同款商品批量入库）"""

    material_id: int = Field(description="材质ID")
    type_id: Optional[int] = Field(default=None, description="器型ID")
    supplier_id: Optional[int] = Field(default=None, description="供货商ID")
    sku_prefix: Optional[str] = Field(default=None, max_length=10, description="SKU前缀，默认取材质名前两个字符")
    quantity: int = Field(ge=1, description="入库数量")
    batch_code: Optional[str] = Field(default=None, max_length=50, description="批次编号（可选）")
    cost_price: Optional[float] = Field(default=None, description="高货进价（通货此字段为空）")
    selling_price: float = Field(description="零售价/标价")
    weight: Optional[float] = Field(default=None, description="总克重")
    size: Optional[str] = Field(default=None, max_length=100, description="通用尺寸描述")
    purchase_date: Optional[datetime.date] = Field(default=None, description="进货日期")
    tag_ids: List[int] = Field(default_factory=list, description="标签ID列表")


class ItemCreate(BaseModel):
    """入库货品请求体（高货或通货单件）"""

    sku_code: Optional[str] = Field(default=None, max_length=50, description="唯一编号，自动生成时留空")
    name: Optional[str] = Field(default=None, max_length=200, description="商品名称")
    batch_id: Optional[int] = Field(default=None, description="通货关联批次，高货为空")
    material_id: int = Field(description="材质ID")
    type_id: Optional[int] = Field(default=None, description="器型ID")
    cost_price: Optional[float] = Field(default=None, description="高货进价（通货此字段为空）")
    selling_price: float = Field(description="零售价/标价")
    floor_price: Optional[float] = Field(default=None, description="底价（最低可接受价）")
    origin: Optional[str] = Field(default=None, max_length=100, description="产地")
    counter: Optional[int] = Field(default=None, description="柜台号")
    cert_no: Optional[str] = Field(default=None, max_length=100, description="证书编号")
    notes: Optional[str] = Field(default=None, description="备注")
    tag_ids: List[int] = Field(default_factory=list, description="标签ID列表")
    spec: Optional[ItemSpecCreate] = Field(default=None, description="规格参数")
    supplier_id: Optional[int] = Field(default=None, description="供货商ID")
    purchase_date: Optional[datetime.date] = Field(default=None, description="进货日期")


class ItemUpdate(BaseModel):
    """编辑货品请求体（全部字段可选）"""

    sku_code: Optional[str] = Field(default=None, max_length=50)
    name: Optional[str] = Field(default=None, max_length=200)
    batch_id: Optional[int] = None
    material_id: Optional[int] = None
    type_id: Optional[int] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    floor_price: Optional[float] = None
    origin: Optional[str] = Field(default=None, max_length=100)
    counter: Optional[int] = None
    cert_no: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None
    tag_ids: Optional[List[int]] = None
    spec: Optional[ItemSpecCreate] = None
    supplier_id: Optional[int] = None
    purchase_date: Optional[datetime.date] = None
    status: Optional[str] = Field(default=None, description="状态: in_stock / sold / returned")


class ItemOut(BaseModel):
    """货品详情响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_code: str
    name: Optional[str]
    batch_id: Optional[int]
    batch_code: Optional[str] = Field(default=None, description="批次编号")
    material_id: int
    material_name: Optional[str] = Field(default=None, description="材质名称")
    type_id: Optional[int]
    type_name: Optional[str] = Field(default=None, description="器型名称")
    cost_price: Optional[float]
    allocated_cost: Optional[float] = Field(default=None, description="分摊成本（通货由算法填充）")
    selling_price: float
    floor_price: Optional[float]
    origin: Optional[str]
    counter: Optional[int]
    cert_no: Optional[str]
    notes: Optional[str]
    supplier_id: Optional[int]
    supplier_name: Optional[str] = Field(default=None, description="供货商名称")
    status: str
    purchase_date: Optional[datetime.date]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_deleted: bool
    # 关联对象
    spec: Optional[ItemSpecOut] = None
    tags: List[DictTagOut] = Field(default_factory=list)
    images: List[ItemImageOut] = Field(default_factory=list)
    # 计算字段
    age_days: Optional[int] = Field(default=None, description="在库天数")
    cover_image: Optional[str] = Field(default=None, description="封面图文件名")


class ItemListItem(BaseModel):
    """货品列表条目（轻量版）"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_code: str
    name: Optional[str]
    batch_id: Optional[int]
    batch_code: Optional[str]
    material_id: int
    material_name: Optional[str] = None
    type_id: Optional[int]
    type_name: Optional[str] = None
    cost_price: Optional[float]
    allocated_cost: Optional[float]
    selling_price: float
    status: str
    purchase_date: Optional[datetime.date]
    created_at: datetime.datetime
    tags: List[DictTagOut] = Field(default_factory=list)
    age_days: Optional[int] = None
    cover_image: Optional[str] = Field(default=None, description="封面图文件名")


class ItemListOut(BaseModel):
    """货品分页列表响应体"""

    items: List[ItemListItem]
    pagination: PaginationMeta


# ──────────────────────────────────────────────
# 销售模型
# ──────────────────────────────────────────────
class SaleCreate(BaseModel):
    """单件销售请求体"""

    item_id: int = Field(description="货品ID")
    actual_price: float = Field(description="实际成交价")
    channel: str = Field(description="销售渠道: store / wechat")
    sale_date: datetime.date = Field(description="销售日期")
    customer_id: Optional[int] = Field(default=None, description="客户ID")
    note: Optional[str] = Field(default=None, description="备注")


class SaleOut(BaseModel):
    """销售记录响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_no: str
    item_id: int
    item_sku: str = Field(description="货品SKU")
    item_name: Optional[str] = Field(default=None, description="货品名称")
    actual_price: float
    channel: str
    sale_date: datetime.date
    customer_id: Optional[int]
    customer_name: Optional[str] = Field(default=None, description="客户姓名")
    bundle_id: Optional[int]
    note: Optional[str]
    created_at: datetime.datetime
    # 计算字段
    gross_profit: float = Field(description="毛利 = 实际成交价 - 分摊成本")


class SaleRecordOut(SaleOut):
    """销售记录响应体（别名）"""
    pass


class SaleRecordListOut(BaseModel):
    """销售记录分页列表响应体"""

    items: List[SaleRecordOut]
    pagination: PaginationMeta


class BundleSaleCreate(BaseModel):
    """套装销售请求体"""

    item_ids: List[int] = Field(description="货品ID列表")
    total_price: float = Field(description="套装总价")
    alloc_method: str = Field(description="价格分摊方法: by_ratio / chain_at_cost")
    channel: str = Field(description="销售渠道")
    sale_date: datetime.date = Field(description="销售日期")
    customer_id: Optional[int] = Field(default=None, description="客户ID")
    note: Optional[str] = Field(default=None, description="备注")


class BundleSaleOut(BaseModel):
    """套装销售响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    bundle_no: str
    total_price: float
    alloc_method: str
    sale_date: datetime.date
    channel: str
    customer_id: Optional[int]
    customer_name: Optional[str] = Field(default=None, description="客户姓名")
    note: Optional[str]
    created_at: datetime.datetime
    sale_records: List[SaleOut] = Field(default_factory=list, description="关联的销售记录")


# ──────────────────────────────────────────────
# 看板模型
# ──────────────────────────────────────────────
class DashboardSummary(BaseModel):
    """概览数据"""

    total_items: int = Field(description="总货品数")
    total_stock_value: float = Field(description="在库商品进价总和（占用资金）")
    month_revenue: float = Field(description="本月销售额")
    month_profit: float = Field(description="本月毛利")
    month_sold_count: int = Field(description="本月销售件数")


class BatchProfitItem(BaseModel):
    """批次利润看板条目"""

    batch_code: str
    material_name: str
    total_cost: float
    quantity: int
    sold_count: int
    revenue: float
    profit: float
    payback_rate: float
    status: str


class ProfitByCategory(BaseModel):
    """按材质利润统计"""

    material_id: int
    material_name: str
    sales_count: int
    revenue: float
    cost: float
    profit: float
    profit_margin: float


class ProfitByChannel(BaseModel):
    """按渠道利润统计"""

    channel: str
    sales_count: int
    revenue: float
    cost: float
    profit: float
    profit_margin: float


class SalesTrendItem(BaseModel):
    """销售趋势数据点"""

    year_month: str = Field(description="年月，格式 YYYY-MM")
    sales_count: int
    revenue: float
    profit: float


class StockAgingItem(BaseModel):
    """压货预警条目"""

    item_id: int
    sku_code: str
    name: Optional[str]
    batch_code: Optional[str]
    material_name: str
    type_name: Optional[str]
    cost_price: Optional[float]
    allocated_cost: Optional[float]
    selling_price: float
    purchase_date: Optional[datetime.date]
    age_days: int = Field(description="在库天数")
    cover_image: Optional[str] = None
    counter: Optional[int] = Field(default=None, description="柜台号")


# ──────────────────────────────────────────────
# 贵金属市价模型
# ──────────────────────────────────────────────
class MetalPriceUpdate(BaseModel):
    """更新贵金属市价请求体"""

    material_id: int = Field(description="材质ID")
    price_per_gram: float = Field(description="克重单价", gt=0)


class RepriceRequest(BaseModel):
    """批量调价请求体"""

    material_id: int = Field(description="材质ID")
    new_price_per_gram: float = Field(description="新的克重单价", gt=0)


class MetalPriceOut(BaseModel):
    """贵金属市价响应体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    material_id: int
    material_name: Optional[str] = Field(default=None, description="材质名称")
    price_per_gram: float
    effective_date: datetime.date
    created_at: datetime.datetime


class RepricePreviewItem(BaseModel):
    """批量调价预览项"""

    sku_code: str
    name: Optional[str]
    old_price: float
    new_price: float


class StockAgingResponse(BaseModel):
    """压货预警响应（含聚合信息）"""

    items: List[StockAgingItem] = Field(default_factory=list, description="压货货品列表")
    total_items: int = Field(description="压货总件数")
    total_value: float = Field(description="压货总价值（按分摊成本计算）")


class RepricePreview(BaseModel):
    """批量调价预览结果"""

    affected_items: List[RepricePreviewItem] = Field(description="受影响货品列表")


# 向前引用已通过 from __future__ import annotations 处理