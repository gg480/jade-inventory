"""
ORM 模型定义 — 对应 TECH_SPEC.md 第2节全部14张表。
使用 SQLAlchemy 2.0 风格：DeclarativeBase + Mapped[T] + mapped_column()。
"""

from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ──────────────────────────────────────────────
# 1. sys_config — 系统配置（key/value/description）
# ──────────────────────────────────────────────
class SysConfig(Base):
    """系统配置表（键值对）"""

    __tablename__ = "sys_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


# ──────────────────────────────────────────────
# 2. dict_material — 材质字典
# ──────────────────────────────────────────────
class DictMaterial(Base):
    """材质字典（一级分类）"""

    __tablename__ = "dict_material"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    sub_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origin: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cost_per_gram: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="material")
    items: Mapped[List["Item"]] = relationship("Item", back_populates="material")
    metal_prices: Mapped[List["MetalPrice"]] = relationship("MetalPrice", back_populates="material")


# ──────────────────────────────────────────────
# 3. dict_type — 器型字典（无 material_id FK，器型跨材质通用）
# ──────────────────────────────────────────────
class DictType(Base):
    """器型字典（二级分类），独立于材质"""

    __tablename__ = "dict_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    spec_fields: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 字符串
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系
    items: Mapped[List["Item"]] = relationship("Item", back_populates="type")


# ──────────────────────────────────────────────
# 4. dict_tag — 标签字典
# ──────────────────────────────────────────────
class DictTag(Base):
    """标签字典（三级，可分组），与货品是多对多关系"""

    __tablename__ = "dict_tag"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    group_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系（通过关联表 item_tag）
    items: Mapped[List["Item"]] = relationship(
        "Item", secondary="item_tag", back_populates="tags"
    )


# ──────────────────────────────────────────────
# 5. suppliers — 供应商
# ──────────────────────────────────────────────
class Supplier(Base):
    """供货商表"""

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="supplier")
    items: Mapped[List["Item"]] = relationship("Item", back_populates="supplier")


# ──────────────────────────────────────────────
# 6. customers — 客户
# ──────────────────────────────────────────────
class Customer(Base):
    """客户表"""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    wechat: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # 关系
    sale_records: Mapped[List["SaleRecord"]] = relationship("SaleRecord", back_populates="customer")
    bundle_sales: Mapped[List["BundleSale"]] = relationship("BundleSale", back_populates="customer")


# ──────────────────────────────────────────────
# 7. batches — 批次表（通货专用）
# ──────────────────────────────────────────────
class Batch(Base):
    """批次表（通货整手进货）"""

    __tablename__ = "batches"

    def __repr__(self) -> str:
        return f"<Batch id={self.id} code={self.batch_code!r}>"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dict_material.id"), nullable=False
    )
    type_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("dict_type.id"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    cost_alloc_method: Mapped[str] = mapped_column(String(20), nullable=False)  # equal / by_weight / by_price
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("suppliers.id"), nullable=True
    )
    purchase_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # 关系
    material: Mapped["DictMaterial"] = relationship("DictMaterial", back_populates="batches")
    type: Mapped[Optional["DictType"]] = relationship("DictType")
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", back_populates="batches")
    items: Mapped[List["Item"]] = relationship("Item", back_populates="batch")


# ──────────────────────────────────────────────
# 8. items — 货品主表
# ──────────────────────────────────────────────
class Item(Base):
    """货品表 — 核心表，记录每一件进货商品"""

    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_status", "status"),
        Index("ix_items_material", "material_id"),
        Index("ix_items_batch", "batch_id"),
    )

    def __repr__(self) -> str:
        return f"<Item id={self.id} sku={self.sku_code!r}>"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku_code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    batch_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    batch_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("batches.id"), nullable=True
    )
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dict_material.id"), nullable=False
    )
    type_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("dict_type.id"), nullable=True
    )
    cost_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    allocated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    selling_price: Mapped[float] = mapped_column(Float, nullable=False)
    floor_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    origin: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    counter: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cert_no: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("suppliers.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="in_stock", nullable=False)
    purchase_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # 关系
    material: Mapped["DictMaterial"] = relationship("DictMaterial", back_populates="items")
    type: Mapped[Optional["DictType"]] = relationship("DictType", back_populates="items")
    batch: Mapped[Optional["Batch"]] = relationship("Batch", back_populates="items")
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", back_populates="items")
    spec: Mapped[Optional["ItemSpec"]] = relationship(
        "ItemSpec", back_populates="item", uselist=False, cascade="all, delete-orphan"
    )
    images: Mapped[List["ItemImage"]] = relationship(
        "ItemImage", back_populates="item", cascade="all, delete-orphan"
    )
    tags: Mapped[List["DictTag"]] = relationship(
        "DictTag", secondary="item_tag", back_populates="items"
    )
    sale_records: Mapped[List["SaleRecord"]] = relationship(
        "SaleRecord", back_populates="item"
    )


# ──────────────────────────────────────────────
# 9. item_tag — 多对多关联表
# ──────────────────────────────────────────────
class ItemTag(Base):
    """货品-标签关联表（多对多）"""

    __tablename__ = "item_tag"

    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dict_tag.id", ondelete="CASCADE"), primary_key=True
    )


# ──────────────────────────────────────────────
# 10. item_spec — 货品规格
# ──────────────────────────────────────────────
class ItemSpec(Base):
    """货品规格参数表（与 items 一对一）"""

    __tablename__ = "item_spec"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("items.id"), unique=True, nullable=False
    )
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metal_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bracelet_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bead_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bead_diameter: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ring_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 关系
    item: Mapped["Item"] = relationship("Item", back_populates="spec")


# ──────────────────────────────────────────────
# 11. item_images — 货品图片
# ──────────────────────────────────────────────
class ItemImage(Base):
    """货品图片表"""

    __tablename__ = "item_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # 关系
    item: Mapped["Item"] = relationship("Item", back_populates="images")


# ──────────────────────────────────────────────
# 12. sale_records — 销售记录
# ──────────────────────────────────────────────
class SaleRecord(Base):
    """销售记录表"""

    __tablename__ = "sale_records"
    __table_args__ = (
        Index("ix_sale_date", "sale_date"),
        Index("ix_sale_channel", "channel"),
    )

    def __repr__(self) -> str:
        return f"<SaleRecord id={self.id} no={self.sale_no!r}>"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("items.id"), nullable=False
    )
    actual_price: Mapped[float] = mapped_column(Float, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    sale_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=True
    )
    bundle_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("bundle_sales.id"), nullable=True
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # 关系
    item: Mapped["Item"] = relationship("Item", back_populates="sale_records")
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="sale_records")
    bundle: Mapped[Optional["BundleSale"]] = relationship("BundleSale", back_populates="sale_records")


# ──────────────────────────────────────────────
# 13. bundle_sales — 套装销售
# ──────────────────────────────────────────────
class BundleSale(Base):
    """套装销售表（一次交易包含多件货品）"""

    __tablename__ = "bundle_sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bundle_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    alloc_method: Mapped[str] = mapped_column(String(20), nullable=False)  # by_ratio / chain_at_cost
    sale_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=True
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # 关系
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="bundle_sales")
    sale_records: Mapped[List["SaleRecord"]] = relationship("SaleRecord", back_populates="bundle")


# ──────────────────────────────────────────────
# 14. metal_prices — 贵金属市价
# ──────────────────────────────────────────────
class MetalPrice(Base):
    """贵金属市价记录表"""

    __tablename__ = "metal_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dict_material.id"), nullable=False
    )
    price_per_gram: Mapped[float] = mapped_column(Float, nullable=False)
    effective_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # 关系
    material: Mapped["DictMaterial"] = relationship("DictMaterial", back_populates="metal_prices")