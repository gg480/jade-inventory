"""
ORM 模型定义 — 对应 TECH_SPEC.md 第2节全部8张表。
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
# 多对多关联表：货品 ↔ 标签
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
# 字典表
# ──────────────────────────────────────────────
class DictMaterial(Base):
    """材质字典（一级分类）"""

    __tablename__ = "dict_material"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系
    types: Mapped[List["DictType"]] = relationship(
        "DictType", back_populates="material", cascade="all, delete-orphan"
    )
    items: Mapped[List["Item"]] = relationship("Item", back_populates="material")


class DictType(Base):
    """器型字典（二级分类），隶属于某个材质"""

    __tablename__ = "dict_type"
    __table_args__ = (
        UniqueConstraint("material_id", "name", name="uq_dict_type_material_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dict_material.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系
    material: Mapped["DictMaterial"] = relationship(
        "DictMaterial", back_populates="types"
    )
    items: Mapped[List["Item"]] = relationship("Item", back_populates="item_type")


class DictTag(Base):
    """标签字典（三级，可分组），与货品是多对多关系"""

    __tablename__ = "dict_tag"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    group_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系
    items: Mapped[List["Item"]] = relationship(
        "Item", secondary="item_tag", back_populates="tags"
    )


# ──────────────────────────────────────────────
# 供货商
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
    items: Mapped[List["Item"]] = relationship("Item", back_populates="supplier")


# ──────────────────────────────────────────────
# 货品（核心表）
# ──────────────────────────────────────────────
class Item(Base):
    """货品表 — 核心表，记录每一件进货商品"""

    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_status", "status"),
        Index("ix_items_material", "material_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku_code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    batch_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dict_material.id"), nullable=False
    )
    type_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("dict_type.id"), nullable=True
    )
    cost_price: Mapped[float] = mapped_column(Float, nullable=False)
    selling_price: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cert_no: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("suppliers.id"), nullable=True
    )
    # 状态：in_stock / sold / returned / lent_out
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
    material: Mapped["DictMaterial"] = relationship(
        "DictMaterial", back_populates="items"
    )
    item_type: Mapped[Optional["DictType"]] = relationship(
        "DictType", back_populates="items"
    )
    supplier: Mapped[Optional["Supplier"]] = relationship(
        "Supplier", back_populates="items"
    )
    tags: Mapped[List["DictTag"]] = relationship(
        "DictTag", secondary="item_tag", back_populates="items"
    )
    images: Mapped[List["ItemImage"]] = relationship(
        "ItemImage", back_populates="item", cascade="all, delete-orphan"
    )
    sale_records: Mapped[List["SaleRecord"]] = relationship(
        "SaleRecord", back_populates="item"
    )


# ──────────────────────────────────────────────
# 货品图片
# ──────────────────────────────────────────────
class ItemImage(Base):
    """货品图片表"""

    __tablename__ = "item_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # 关系
    item: Mapped["Item"] = relationship("Item", back_populates="images")


# ──────────────────────────────────────────────
# 销售记录
# ──────────────────────────────────────────────
class SaleRecord(Base):
    """销售记录表"""

    __tablename__ = "sale_records"
    __table_args__ = (
        Index("ix_sale_records_date", "sale_date"),
        Index("ix_sale_records_channel", "channel"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("items.id"), nullable=False
    )
    actual_price: Mapped[float] = mapped_column(Float, nullable=False)
    # 渠道：store / wechat / ecommerce
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    sale_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    customer_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # 关系
    item: Mapped["Item"] = relationship("Item", back_populates="sale_records")
