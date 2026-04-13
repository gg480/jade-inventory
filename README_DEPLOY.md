# 翡翠库存管理系统 — 部署指南

> Docker 镜像：`lrunningmjgoat/jadeinventory`
> 适用于极空间 NAS / 群晖 NAS / 任意支持 Docker 的设备

---

## 核心设计：数据 + 配置 全部持久化

容器通过 **两个文件夹** 将所有数据写入你的 NAS 本地存储：

| 本地文件夹 | 容器路径 | 内容 | 说明 |
|-----------|---------|------|------|
| `./data/` | `/app/data` | `jade.db`（数据库）、`images/`（商品图片）、`barcodes/`（条码） | 所有业务数据 |
| `./config/` | `/app/config` | `.env`（配置文件） | 所有配置参数 |

**只需在极空间设置一次文件夹映射，以后更新镜像、重启容器，数据和配置都不会丢失。**

---

## 一、极空间 NAS Docker Compose 部署（推荐）

### 1. 准备工作

在极空间的文件管理中，找一个位置创建部署文件夹，例如：

```
/docker/jade-inventory/
├── docker-compose.yml   ← 下面的配置文件
├── data/                ← 数据库+图片（自动创建）
└── config/              ← 配置文件（首次启动自动生成）
```

### 2. 创建 docker-compose.yml

在极空间文件管理中，创建 `/docker/jade-inventory/docker-compose.yml`，内容如下：

```yaml
version: "3.8"
services:
  jade:
    image: lrunningmjgoat/jadeinventory:latest
    container_name: jade-inventory
    ports:
      - "8080:8000"
    volumes:
      # 数据持久化：数据库 + 上传图片
      - ./data:/app/data
      # 配置持久化：.env 由容器首次启动自动生成
      - ./config:/app/config
    environment:
      # 固定的环境变量（不需要修改）
      - DB_PATH=/app/data/jade.db
      - IMAGE_DIR=/app/data/images
      - CORS_ORIGINS=*
      - TZ=Asia/Shanghai
    restart: unless-stopped
```

### 3. 启动容器

在极空间 Docker 管理器中，使用 Compose 功能指向上面的 `docker-compose.yml` 文件启动。

### 4. 首次启动后

容器启动后会自动在你的本地 `config/` 文件夹中生成一个 `.env` 配置文件：

```
config/
└── .env    ← 自动生成的配置文件
```

### 5. 配置 JWT_SECRET（必须）

在极空间文件管理中，打开 `config/.env`，找到这一行：

```
JWT_SECRET=please-change-this-to-a-random-string
```

改为一个随机字符串（至少16位），例如：

```
JWT_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

修改后，重启容器让配置生效。

### 6. 访问系统

打开浏览器，访问：

```
http://你的NAS内网IP:8080
```

首次访问会自动创建数据库，使用默认管理员密码登录，**系统会强制要求你修改密码**。

---

## 二、极空间 NAS GUI 手动部署（不用 Compose）

### 1. 拉取镜像

进入极空间 Docker 管理器 → **「镜像」** → **「拉取」** → 输入：

```
lrunningmjgoat/jadeinventory:latest
```

### 2. 创建容器

在镜像列表中找到拉取的镜像，点击 **「创建容器」**。

#### 基本设置

| 设置项 | 值 |
|--------|-----|
| 容器名称 | `jade-inventory` |
| 重启策略 | **始终重启** |

#### 端口映射

| 容器端口 | 主机端口 | 协议 |
|----------|---------|------|
| 8000 | **8080** | TCP |

#### 挂载目录（关键！）

| 容器路径 | 主机路径 | 说明 |
|----------|---------|------|
| `/app/data` | `/vol1/1000/docker/jade-inventory/data` | 数据库和图片 |
| `/app/config` | `/vol1/1000/docker/jade-inventory/config` | 配置文件 |

#### 环境变量

| 变量名 | 值 |
|--------|-----|
| `DB_PATH` | `/app/data/jade.db` |
| `IMAGE_DIR` | `/app/data/images` |
| `CORS_ORIGINS` | `*` |
| `TZ` | `Asia/Shanghai` |

### 3. 启动后配置

1. 启动容器后，在极空间文件管理中找到 `config/` 文件夹
2. 打开自动生成的 `.env` 文件
3. 修改 `JWT_SECRET` 为随机字符串
4. 重启容器

---

## 三、Docker 命令行一键部署

```bash
mkdir -p ~/jade-inventory/{data,config}
cd ~/jade-inventory

cat > docker-compose.yml << 'EOF'
version: "3.8"
services:
  jade:
    image: lrunningmjgoat/jadeinventory:latest
    container_name: jade-inventory
    ports:
      - "8080:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - DB_PATH=/app/data/jade.db
      - IMAGE_DIR=/app/data/images
      - CORS_ORIGINS=*
      - TZ=Asia/Shanghai
    restart: unless-stopped
EOF

# 启动
docker compose up -d

# 等容器启动后，编辑配置
nano config/.env  # 修改 JWT_SECRET
docker compose restart
```

---

## 四、更新版本

### 极空间 NAS 操作

1. 在 Docker 管理器中停止 `jade-inventory` 容器
2. **删除容器**（放心，数据在 `data/` 和 `config/` 文件夹中，不会丢失）
3. **「镜像」→「拉取」** 新版镜像
4. 重新创建容器（使用相同的文件夹映射设置）
5. 容器启动后，`config/.env` 不会变化（已有文件不会被覆盖），配置保持

### 命令行操作

```bash
cd ~/jade-inventory
docker compose pull
docker compose up -d
```

旧容器会被自动替换，`data/` 和 `config/` 目录不受影响。

---

## 五、配置文件说明

容器首次启动后，`config/.env` 的内容如下：

```env
# JWT 签名密钥（必须修改！至少16位随机字符串）
JWT_SECRET=please-change-this-to-a-random-string

# 默认管理员密码（仅首次初始化数据库时生效）
# DEFAULT_ADMIN_PASSWORD=admin888

# JWT Token 有效天数
# JWT_EXPIRE_DAYS=30

# 压货预警天数
# ALERT_DAYS=90

# 调试模式
# DEBUG=false

# 时区
# TZ=Asia/Shanghai
```

修改任何配置后，**需重启容器** 才能生效。

加载优先级：`docker-compose environment` > `config/.env` > 系统默认值

---

## 六、数据备份

所有数据在 `data/` 文件夹中，备份只需复制该文件夹：

```bash
# 备份
cp -r ~/jade-inventory/data ~/backup/jade-$(date +%Y%m%d)

# 恢复
cp -r ~/backup/jade-20250101/* ~/jade-inventory/data/
```

也可以在系统的 **「账户设置」** 页面中，点击「备份数据库」按钮下载 `.db` 文件。

---

## 七、常见问题

### Q: 容器启动后访问不了？

1. 检查容器是否正常运行
2. 查看日志确认是否有报错
3. 确认 8080 端口没有被其他服务占用
4. 检查 `config/.env` 中 `JWT_SECRET` 是否已修改

### Q: 数据丢失了？

检查挂载目录是否正确配置。必须同时挂载 `/app/data` 和 `/app/config`。

### Q: 更新镜像后配置还在吗？

在的。容器启动时检测到 `config/.env` 已存在，不会覆盖。你的所有配置修改都会保留。

### Q: 如何修改密码？

登录系统后，进入 **「账户设置」** 页面修改密码。
