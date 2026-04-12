"""
认证路由 — 登录验证、修改密码、Token 校验。
单用户模式：admin/admin123 为默认凭据。
"""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, DB_PATH
from models import SysConfig
from schemas import ApiResponse

router = APIRouter(tags=["认证"])

# ── 配置 ──
JWT_SECRET = os.getenv("JWT_SECRET", "jade-inventory-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "30"))

# 默认密码（首次启动时写入数据库）
DEFAULT_PASSWORD = "admin123"


# ── 密码工具函数 ──

def _hash_password(password: str) -> str:
    """生成密码哈希。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    """验证密码。"""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _get_password_hash(db: Session) -> str:
    """
    从数据库获取当前密码哈希，如果没有则创建默认密码。
    返回密码哈希字符串。
    """
    config = db.query(SysConfig).filter(SysConfig.key == "admin_password").first()
    if not config:
        # 首次启动，创建默认密码
        hashed = _hash_password(DEFAULT_PASSWORD)
        db.add(SysConfig(
            key="admin_password",
            value=hashed,
            description="管理员登录密码",
        ))
        db.add(SysConfig(
            key="admin_password_changed",
            value="false",
            description="密码是否已从默认值修改",
        ))
        db.commit()
        db.refresh(config)
        return hashed
    return config.value


def _is_default_password(db: Session) -> bool:
    """检查当前密码是否仍为默认密码。"""
    config = db.query(SysConfig).filter(SysConfig.key == "admin_password_changed").first()
    if not config:
        return True
    return config.value.lower() != "true"


def _create_access_token(subject: str = "admin", expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Token。"""
    if expires_delta is None:
        expires_delta = timedelta(days=JWT_EXPIRE_DAYS)
    now = datetime.utcnow()
    expire = now + expires_delta
    to_encode = {
        "sub": subject,
        "iat": now,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def _decode_token(token: str) -> dict:
    """解码并验证 JWT Token，返回 payload dict。验证失败抛 HTTPException。"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        subject: Optional[str] = payload.get("sub")
        if subject is None:
            raise HTTPException(status_code=401, detail="Token 无效：缺少 subject")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")


# ── Schemas ──

class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class TokenData(BaseModel):
    sub: str
    exp: Optional[int] = None


# ── Endpoints ──

@router.post("/auth/login", summary="管理员登录")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """管理员登录，返回 JWT Token。"""
    # 1. 获取密码哈希
    hashed = _get_password_hash(db)

    # 2. 验证密码
    if not _verify_password(body.password, hashed):
        raise HTTPException(status_code=401, detail="密码错误")

    # 3. 创建 JWT Token
    token = _create_access_token()

    # 4. 检查是否需要修改默认密码
    must_change = _is_default_password(db)

    return ApiResponse(
        data=LoginResponse(
            token=token,
            token_type="bearer",
            must_change_password=must_change,
        ).model_dump(),
        message="ok",
    )


@router.post("/auth/change-password", summary="修改管理员密码")
def change_password(
    body: PasswordChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """修改管理员密码。需要当前 Token。"""
    # 1. 验证当前 Token
    user = get_current_user(request, db)

    # 2. 验证旧密码
    hashed = _get_password_hash(db)
    if not _verify_password(body.old_password, hashed):
        raise HTTPException(status_code=400, detail="旧密码错误")

    # 3. 验证新密码
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")

    if body.new_password == body.old_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")

    # 4. 更新密码
    new_hashed = _hash_password(body.new_password)
    config = db.query(SysConfig).filter(SysConfig.key == "admin_password").first()
    config.value = new_hashed

    # 5. 标记密码已修改
    changed_config = db.query(SysConfig).filter(SysConfig.key == "admin_password_changed").first()
    if changed_config:
        changed_config.value = "true"

    db.commit()

    return ApiResponse(data=None, message="密码修改成功")


@router.get("/auth/me", summary="验证 Token 有效性")
def get_me(request: Request, db: Session = Depends(get_db)):
    """验证 Token 有效性（返回当前用户信息）。"""
    payload = get_current_user(request, db)
    return ApiResponse(
        data={
            "username": payload.get("sub", "admin"),
            "iat": payload.get("iat"),
            "exp": payload.get("exp"),
        },
        message="ok",
    )


@router.post("/auth/backup-db", summary="备份数据库")
def backup_database(
    request: Request,
    db: Session = Depends(get_db),
):
    """备份数据库，返回下载文件。需要认证。"""
    # 1. 验证 Token
    get_current_user(request, db)

    # 2. 复制数据库文件到临时目录
    source_path = Path(DB_PATH)
    if not source_path.exists():
        raise HTTPException(status_code=500, detail="数据库文件不存在")

    # 3. 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"jade_backup_{timestamp}.db"

    # 4. 使用 SQLite 的 backup API 进行热备份（推荐方式）
    # 使用 tempfile 创建临时文件，然后通过 shutil 复制
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        # 使用 SQLite 在线备份 API
        import sqlite3
        source_conn = sqlite3.connect(str(source_path))
        dest_conn = sqlite3.connect(str(tmp_path))
        source_conn.backup(dest_conn)
        dest_conn.close()
        source_conn.close()

        return FileResponse(
            path=str(tmp_path),
            filename=backup_filename,
            media_type="application/octet-stream",
            background=None,
        )
    except Exception as e:
        # 如果在线备份失败，回退到简单复制
        if tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(status_code=500, detail=f"数据库备份失败: {str(e)}")


# ── Auth Dependency ──

def get_current_user(request: Request, db: Session = Depends(get_db)) -> dict:
    """
    FastAPI 依赖：从请求头 Authorization: Bearer xxx 中提取并验证 JWT。
    验证通过返回 {"sub": "admin"}, 失败抛 401。
    所有需要认证的路由都应依赖此函数。

    Usage:
        @router.get("/protected")
        def protected_route(user: dict = Depends(get_current_user)):
            ...
    """
    auth_header: Optional[str] = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="缺少 Authorization 请求头")

    # 支持 "Bearer <token>" 格式
    parts = auth_header.split(" ", maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization 格式错误，应为 'Bearer <token>'")

    token = parts[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token 不能为空")

    payload = _decode_token(token)
    return payload
