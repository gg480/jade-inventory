"""
数据库连接管理 — SQLAlchemy 2.0 引擎配置。

数据库文件默认位于项目根目录的 data/jade.db，可通过环境变量 DB_PATH 覆盖。
"""

import os
from pathlib import Path
from typing import Generator

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)

# 数据库路径配置
_DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "jade.db"
DB_PATH = os.getenv("DB_PATH", str(_DEFAULT_DB_PATH))

# 确保数据库目录存在
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# SQLAlchemy 2.0 引擎配置
# ──────────────────────────────────────────────

# 创建引擎（SQLite）
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},  # SQLite 多线程需要
    echo=False,  # 生产时关闭 SQL 日志，调试时可改为 True
    future=True,  # 使用 SQLAlchemy 2.0 风格
    pool_pre_ping=True,  # 连接前检测可用性
    pool_recycle=3600,  # 1小时回收连接
)

# Session 工厂
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
    future=True,  # 使用 SQLAlchemy 2.0 风格
)

# ──────────────────────────────────────────────
# 依赖注入生成器
# ──────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 依赖注入：提供数据库 Session，请求结束后自动关闭。

    Usage:
        @app.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ──────────────────────────────────────────────
# 数据库初始化函数
# ──────────────────────────────────────────────

def seed_data(session: Session) -> None:
    """
    插入种子数据（材质、器型、标签、系统配置等）。

    幂等设计：检查表是否已有数据，有则跳过。

    种子数据内容详见 PRD_v2.md 附录：
    - 36 种材质（含子类、产地、贵金属克重单价）
    - 9 种器型（含 spec_fields JSON）
    - 22 个标签（4个分组）
    - 4 条系统配置
    - 2 条贵金属初始市价（18K金780、银25）
    """
    # 即使已有材质数据，也需要补充缺失的系统配置
    from models import SysConfig
    _missing_configs = [
        ("auto_fetch_prices", "是否自动获取贵金属市价"),
        ("last_price_fetch_time", "最近一次市价抓取时间"),
        ("last_price_fetch_status", "最近一次市价抓取状态"),
    ]
    for cfg_key, cfg_desc in _missing_configs:
        existing = session.execute(
            text("SELECT id FROM sys_config WHERE key = :k"), {"k": cfg_key}
        ).scalar()
        if not existing:
            session.add(SysConfig(key=cfg_key, value="", description=cfg_desc))
    session.commit()

    # 检查 dict_material 表是否已有数据，有则跳过
    result = session.execute(text("SELECT COUNT(*) FROM dict_material"))
    count = result.scalar()
    if count and count > 0:
        logger.info("[seed_data] 数据库已有 %s 条材质记录，跳过种子数据插入", count)
        return

    logger.info("[seed_data] 插入种子数据...")

    # 导入模型（在函数内导入避免循环依赖）
    from models import SysConfig, DictMaterial, DictType, DictTag, MetalPrice

    # 1. 36种材质
    materials = [
        # 贵金属（3种）
        DictMaterial(name="18K金", sub_type="780", cost_per_gram=780.0),
        DictMaterial(name="银", sub_type="990", origin="", cost_per_gram=25.0),
        DictMaterial(name="k铂金", sub_type="", cost_per_gram=320.0),
        # 翡翠类（2种）
        DictMaterial(name="翡翠", origin="缅甸"),
        DictMaterial(name="和田玉", origin="新疆"),
        # 水晶类（1种）
        DictMaterial(name="水晶", sub_type="白水晶"),
        # 宝石类（PRD附录 11种）
        DictMaterial(name="珍珠", sub_type="淡水珠", origin="浙江"),
        DictMaterial(name="朱砂", origin="贵州"),
        DictMaterial(name="蜜蜡", origin="波罗的海"),
        DictMaterial(name="碧玺"),
        DictMaterial(name="青金石", origin="阿富汗"),
        DictMaterial(name="黑曜石"),
        DictMaterial(name="金曜石"),
        DictMaterial(name="金虎眼"),
        DictMaterial(name="虎眼"),
        DictMaterial(name="珐彩螺", origin="意大利"),
        DictMaterial(name="鎉石", origin="梧州"),
        # 补充常见宝石（19种，总计36种）
        DictMaterial(name="绿松石", origin="湖北"),
        DictMaterial(name="红珊瑚", origin="台湾"),
        DictMaterial(name="琥珀", origin="波罗的海"),
        DictMaterial(name="玛瑙"),
        DictMaterial(name="玉髓"),
        DictMaterial(name="孔雀石"),
        DictMaterial(name="菱锰矿", origin="阿根廷"),
        DictMaterial(name="橄榄石"),
        DictMaterial(name="托帕石"),
        DictMaterial(name="海蓝宝"),
        DictMaterial(name="红宝石"),
        DictMaterial(name="蓝宝石"),
        DictMaterial(name="祖母绿"),
        DictMaterial(name="钻石"),
        DictMaterial(name="珊瑚"),
        DictMaterial(name="虎睛石"),
        DictMaterial(name="鹰眼石"),
        DictMaterial(name="木变石"),
        DictMaterial(name="彼得石"),
    ]
    session.add_all(materials)

    # 2. 9种器型（spec_fields 为 JSON 字符串）
    types = [
        DictType(name="手镯", spec_fields='["weight", "bracelet_size"]', sort_order=10),
        DictType(name="手串", spec_fields='["weight", "bead_count", "bead_diameter"]', sort_order=20),
        DictType(name="戒指", spec_fields='["weight", "ring_size"]', sort_order=30),
        DictType(name="项链", spec_fields='["weight", "bead_count", "bead_diameter"]', sort_order=40),
        DictType(name="吊坠", spec_fields='["weight", "size"]', sort_order=50),
        DictType(name="耳饰", spec_fields='["weight", "size"]', sort_order=60),
        DictType(name="挂件", spec_fields='["weight", "size"]', sort_order=70),
        DictType(name="摆件", spec_fields='["weight", "size"]', sort_order=80),
        DictType(name="脚链", spec_fields='["weight", "bead_count", "bead_diameter"]', sort_order=90),
    ]
    session.add_all(types)

    # 3. 22个标签（4个分组）
    tags = [
        # 种水（翡翠用）
        DictTag(name="玻璃种", group_name="种水"),
        DictTag(name="冰种", group_name="种水"),
        DictTag(name="糯冰种", group_name="种水"),
        DictTag(name="糯种", group_name="种水"),
        DictTag(name="豆种", group_name="种水"),
        # 颜色
        DictTag(name="满绿", group_name="颜色"),
        DictTag(name="飘花", group_name="颜色"),
        DictTag(name="紫罗兰", group_name="颜色"),
        DictTag(name="黄翡", group_name="颜色"),
        DictTag(name="墨翠", group_name="颜色"),
        DictTag(name="无色", group_name="颜色"),
        # 工艺
        DictTag(name="手工雕", group_name="工艺"),
        DictTag(name="机雕", group_name="工艺"),
        DictTag(name="素面", group_name="工艺"),
        # 题材
        DictTag(name="观音", group_name="题材"),
        DictTag(name="佛公", group_name="题材"),
        DictTag(name="平安扣", group_name="题材"),
        DictTag(name="如意", group_name="题材"),
        DictTag(name="山水", group_name="题材"),
        DictTag(name="花鸟", group_name="题材"),
        DictTag(name="龙凤", group_name="题材"),
        DictTag(name="貔貅", group_name="题材"),
    ]
    session.add_all(tags)

    # 4. 系统配置（含自动抓取配置）
    configs = [
        SysConfig(key="operating_cost_rate", value="0.05", description="经营成本率（分摊成本的5%）"),
        SysConfig(key="markup_rate", value="0.30", description="上浮比例（底价的30%）"),
        SysConfig(key="aging_threshold_days", value="90", description="压货预警阈值（天）"),
        SysConfig(key="default_alloc_method", value="equal", description="默认成本分摊算法：均摊"),
    ]
    session.add_all(configs)

    # 5. 管理员默认密码（可通过环境变量 DEFAULT_ADMIN_PASSWORD 覆盖，首次登录强制修改）
    import bcrypt
    _default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    _hashed_password = bcrypt.hashpw(
        _default_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    admin_configs = [
        SysConfig(key="admin_password", value=_hashed_password, description="管理员登录密码"),
        SysConfig(key="admin_password_changed", value="false", description="密码是否已从默认值修改"),
    ]
    session.add_all(admin_configs)

    # 提交以便获取材质ID
    session.commit()

    # 5. 2条贵金属初始市价（需要材质ID）
    # 获取18K金和银的材质ID
    gold = session.execute(
        text("SELECT id FROM dict_material WHERE name = '18K金'")
    ).scalar()
    silver = session.execute(
        text("SELECT id FROM dict_material WHERE name = '银'")
    ).scalar()

    from datetime import date
    metal_prices = [
        MetalPrice(material_id=gold, price_per_gram=780.0, effective_date=date.today()),
        MetalPrice(material_id=silver, price_per_gram=25.0, effective_date=date.today()),
    ]
    session.add_all(metal_prices)

    session.commit()
    logger.info("[seed_data] 种子数据插入完成")


def init_db() -> None:
    """
    初始化数据库：
    1. 根据 ORM 模型创建所有表（如果已存在则跳过）
    2. 插入种子数据（如果表为空）

    幂等：可安全重复调用。

    注意：生产环境不使用 drop_all，表结构变更应通过 Alembic 迁移管理。
    如需强制重建表结构，可设置环境变量 RESET_DB=true。
    """
    from models import Base  # 延迟导入，避免循环依赖

    # 仅在显式设置 RESET_DB=true 时才删除所有表（仅用于开发/调试）
    if os.getenv("RESET_DB", "").lower() == "true":
        logger.warning("[init_db] RESET_DB=true，将删除所有表并重建！")
        Base.metadata.drop_all(bind=engine)

    # 创建所有表（如果已存在则跳过，不会丢失数据）
    Base.metadata.create_all(bind=engine)
    logger.info("[init_db] 表结构创建/更新完成（基于 TECH_SPEC.md v2）")

    # 插入种子数据
    with SessionLocal() as session:
        seed_data(session)

    logger.info("[init_db] 数据库初始化完成：%s", DB_PATH)

# ──────────────────────────────────────────────
# 直接执行测试
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # 测试数据库连接
    init_db()
    print("数据库引擎测试通过")

    # 验证引擎
    with engine.connect() as conn:
        result = conn.execute(text("SELECT sqlite_version()"))
        version = result.scalar()
        print(f"SQLite 版本: {version}")