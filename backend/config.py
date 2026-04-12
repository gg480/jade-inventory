"""
玉器店进销存系统配置管理

所有硬编码的参数集中在此处，便于统一管理和环境变量覆盖。
"""

import os
from pathlib import Path

# ──────────────────────────────────────────────
# 数据库配置
# ──────────────────────────────────────────────

# 数据库文件路径
_DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "jade.db"
DB_PATH: str = os.getenv("DB_PATH", str(_DEFAULT_DB_PATH))

# ──────────────────────────────────────────────
# 业务逻辑配置
# ──────────────────────────────────────────────

# 压货警报天数阈值（默认90天）
ALERT_DAYS: int = int(os.getenv("ALERT_DAYS", 90))

# ──────────────────────────────────────────────
# 图片管理配置
# ──────────────────────────────────────────────

# 图片存储目录
_DEFAULT_IMAGE_DIR = Path(__file__).parent.parent / "data" / "images"
IMAGE_DIR: Path = Path(os.getenv("IMAGE_DIR", str(_DEFAULT_IMAGE_DIR)))

# 图片上传允许的扩展名
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# 图片最大大小（字节，默认5MB）
MAX_IMAGE_SIZE: int = int(os.getenv("MAX_IMAGE_SIZE", 5 * 1024 * 1024))

# ──────────────────────────────────────────────
# 系统配置
# ──────────────────────────────────────────────

# 分页默认大小
DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", 20))

# 批量入库最大数量
MAX_BATCH_QUANTITY: int = int(os.getenv("MAX_BATCH_QUANTITY", 500))

# ──────────────────────────────────────────────
# 初始化检查
# ──────────────────────────────────────────────

# 确保必要的目录存在
def init_directories() -> None:
    """初始化必要的目录结构"""
    # 确保数据库目录存在
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    # 确保图片目录存在
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)


# 打印配置摘要（仅调试用）
if __name__ == "__main__":
    init_directories()
    print("=== 玉器店进销存系统配置 ===")
    print(f"数据库路径: {DB_PATH}")
    print(f"压货警报天数: {ALERT_DAYS}天")
    print(f"图片目录: {IMAGE_DIR}")
    print(f"允许的图片扩展名: {ALLOWED_IMAGE_EXTENSIONS}")
    print(f"最大图片大小: {MAX_IMAGE_SIZE / 1024 / 1024:.1f}MB")
    print(f"默认分页大小: {DEFAULT_PAGE_SIZE}")
    print(f"批量入库最大数量: {MAX_BATCH_QUANTITY}")
    print("==============================")