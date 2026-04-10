"""
数据库连接管理 — 引擎创建、Session 工厂、init_db()（建表 + 种子数据）。
数据库文件默认位于项目根目录的 data/jade.db，可通过环境变量 DB_PATH 覆盖。
"""

import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config import DB_PATH, init_directories
from models import (
    Base,
    DictMaterial,
    DictTag,
    DictType,
    Supplier,
)

# 确保必要的目录存在
init_directories()

# ──────────────────────────────────────────────
# SQLAlchemy 引擎 & Session
# ──────────────────────────────────────────────
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},  # SQLite 多线程需要
    echo=False,  # 生产时关闭 SQL 日志，调试时可改为 True
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """FastAPI 依赖注入：提供数据库 Session，请求结束后自动关闭。"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ──────────────────────────────────────────────
# 建表 + 种子数据
# ──────────────────────────────────────────────

# 种子材质列表（按 PRD.md 第5节）
_SEED_MATERIALS = [
    "翡翠", "和田玉", "水晶", "白银", "珍珠",
    "檀木", "朱砂", "蜜蜡", "玛瑙", "南红",
]

# 通用器型（每个材质都关联同一批器型）
_SEED_TYPES = ["手镯", "挂件", "手串/手链", "戒指", "项链", "耳饰", "摆件", "吊坠"]

# 标签（按分组）
_SEED_TAGS = [
    # (name, group_name)
    ("玻璃种", "种水"),
    ("冰种",   "种水"),
    ("糯冰种", "种水"),
    ("糯种",   "种水"),
    ("豆种",   "种水"),
    ("满绿",   "颜色"),
    ("飘花",   "颜色"),
    ("紫罗兰", "颜色"),
    ("黄翡",   "颜色"),
    ("墨翠",   "颜色"),
    ("无色",   "颜色"),
    ("手工雕", "工艺"),
    ("机雕",   "工艺"),
    ("素面",   "工艺"),
    ("观音",   "题材"),
    ("佛公",   "题材"),
    ("平安扣", "题材"),
    ("如意",   "题材"),
    ("山水",   "题材"),
    ("花鸟",   "题材"),
]


def _seed_data(db: Session) -> None:
    """插入初始种子数据；如果 dict_material 表已有数据则跳过，保证幂等。"""
    if db.query(DictMaterial).count() > 0:
        return  # 已有数据，跳过

    # 1. 插入材质
    materials = []
    for idx, name in enumerate(_SEED_MATERIALS, start=1):
        m = DictMaterial(name=name, sort_order=idx, is_active=True)
        db.add(m)
        materials.append(m)
    db.flush()  # 让 materials 获得 id，供器型外键使用

    # 2. 为每个材质插入全部通用器型
    for material in materials:
        for idx, type_name in enumerate(_SEED_TYPES, start=1):
            db.add(
                DictType(
                    material_id=material.id,
                    name=type_name,
                    sort_order=idx,
                    is_active=True,
                )
            )

    # 3. 插入标签
    for idx, (tag_name, group) in enumerate(_SEED_TAGS, start=1):
        db.add(DictTag(name=tag_name, group_name=group, is_active=True))

    db.commit()
    print(
        f"[init_db] 种子数据已插入：{len(materials)} 个材质，"
        f"{len(materials) * len(_SEED_TYPES)} 个器型，"
        f"{len(_SEED_TAGS)} 个标签。"
    )


def init_db() -> None:
    """
    初始化数据库：
    1. 根据 ORM 模型创建所有表（如果已存在则跳过）
    2. 插入种子数据（如果表为空）
    """
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        _seed_data(db)
    print(f"[init_db] 数据库就绪：{DB_PATH}")
