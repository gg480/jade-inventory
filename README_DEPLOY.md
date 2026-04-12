# 翡翠库存管理系统 — 部署指南

> Docker 镜像：`gg480/jade-inventory`
> 适用于极空间 NAS / 群晖 NAS / 任意支持 Docker 的设备

---

## 一、极空间 NAS Docker 部署步骤

### 1. 打开 Docker 管理器

进入极空间 NAS 系统桌面，点击 **「应用中心」→「Docker」** 打开 Docker 管理界面。

> 📷 *截图：极空间桌面 → 应用中心 → Docker 图标*

### 2. 拉取镜像

点击 **「镜像」** 标签页 → 点击右上角 **「拉取」** 按钮 → 在输入框中填写：

```
gg480/jade-inventory:latest
```

点击 **「确定」** 开始拉取，等待下载完成（约 200MB，首次需 2-5 分钟）。

> 📷 *截图：Docker → 镜像 → 拉取 → 输入镜像名称 → 确定*

### 3. 创建容器

拉取完成后，在镜像列表中找到 `gg480/jade-inventory:latest`，点击右侧 **「创建容器」**。

#### 3.1 基本设置

| 设置项 | 值 |
|--------|-----|
| 容器名称 | `jade-inventory` |
| 镜像 | `gg480/jade-inventory:latest` |
| 重启策略 | **始终重启**（unless-stopped） |

#### 3.2 端口映射

| 容器端口 | 主机端口 | 协议 |
|----------|---------|------|
| 8000 | **8080** | TCP |

> 📷 *截图：端口设置页面，将容器 8000 映射到主机 8080*

#### 3.3 挂载目录（数据持久化）

| 容器路径 | 主机路径 | 说明 |
|----------|---------|------|
| `/app/data` | 选择一个 NAS 上的文件夹，如 `/vol1/1000/docker/jade-inventory/data` | 数据库和图片存储 |

> 📷 *截图：存储卷设置，添加 `/app/data` → 主机路径映射*

#### 3.4 环境变量

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `DB_PATH` | `/app/data/jade.db` | 数据库文件路径（默认值，无需修改） |
| `IMAGE_DIR` | `/app/data/images` | 图片存储目录（默认值，无需修改） |
| `CORS_ORIGINS` | `*` | 跨域设置（默认值，无需修改） |
| `JWT_SECRET` | **请改为随机字符串** | JWT 密钥，用于登录认证 |
| `TZ` | `Asia/Shanghai` | 时区设置 |

> ⚠️ **重要**：`JWT_SECRET` 必须修改为一个随机的安全字符串，否则存在安全风险！
> 可以在终端中执行以下命令生成随机密钥：
> ```bash
> openssl rand -hex 32
> ```

> 📷 *截图：环境变量设置页面，逐项添加*

### 4. 启动容器

点击 **「下一步」→「创建」**，容器将自动启动。

> 📷 *截图：容器列表，jade-inventory 状态为"运行中"*

### 5. 访问系统

打开浏览器，访问：

```
http://你的NAS内网IP:8080
```

例如：`http://192.168.1.100:8080`

首次访问会自动创建数据库，使用默认管理员账号登录（账号: `admin`，密码: `admin123`），**请立即修改密码**。

---

## 二、Docker 命令行一键部署

如果你更喜欢命令行，可以使用以下 `docker-compose` 方式部署：

### 1. 创建部署目录

```bash
mkdir -p ~/jade-inventory/data
cd ~/jade-inventory
```

### 2. 创建 docker-compose.yml

```bash
cat > docker-compose.yml << 'EOF'
version: "3.8"
services:
  jade:
    image: gg480/jade-inventory:latest
    container_name: jade-inventory
    ports:
      - "8080:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DB_PATH=/app/data/jade.db
      - IMAGE_DIR=/app/data/images
      - CORS_ORIGINS=*
      - JWT_SECRET=change-this-to-a-random-string
      - TZ=Asia/Shanghai
    restart: unless-stopped
EOF
```

### 3. 启动

```bash
docker compose up -d
```

### 4. 查看日志

```bash
docker logs -f jade-inventory
```

---

## 三、更新版本

当发布新版本时，按以下步骤更新：

### 极空间 NAS GUI 操作

1. 打开 Docker 管理器 → **「镜像」** 标签
2. 点击 **「拉取」** → 输入 `gg480/jade-inventory:latest`
3. 等待拉取完成后，进入 **「容器」** 标签
4. 停止并删除旧的 `jade-inventory` 容器（**数据不会丢失**，因为挂载了目录）
5. 基于新镜像重新创建容器（参考步骤 3，使用相同的设置）

### 命令行操作

```bash
cd ~/jade-inventory
docker compose pull
docker compose up -d
```

旧容器会被自动替换，数据卷不受影响。

---

## 四、配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_PATH` | `/app/data/jade.db` | SQLite 数据库文件路径 |
| `IMAGE_DIR` | `/app/data/images` | 商品图片存储目录 |
| `CORS_ORIGINS` | `*` | 允许的跨域来源 |
| `JWT_SECRET` | — | **必填** JWT 签名密钥 |
| `TZ` | — | 时区，建议设为 `Asia/Shanghai` |
| `PYTHONUNBUFFERED` | `1` | Python 日志实时输出（容器内已预设） |

### 端口说明

- 容器内部始终使用 **8000** 端口
- 主机映射端口可自定义（推荐 `8080`，也可改为 `3000`、`9000` 等）
- 如果极空间 8080 端口被其他服务占用，请修改主机端口

### 数据备份

所有数据（数据库 + 图片）都存储在挂载目录 `/app/data` 中。备份只需复制该目录：

```bash
# 备份
cp -r ~/jade-inventory/data ~/backup/jade-inventory-$(date +%Y%m%d)

# 恢复
docker compose down
cp -r ~/backup/jade-inventory-20250101/* ~/jade-inventory/data/
docker compose up -d
```

---

## 五、常见问题

### Q: 容器启动后访问不了？

1. 检查容器是否正常运行：`docker ps`
2. 查看日志：`docker logs jade-inventory`
3. 确认防火墙/安全组是否放行了 8080 端口
4. 尝试使用 `http://127.0.0.1:8080` 访问（排除网络问题）

### Q: 数据丢失了？

检查挂载目录是否正确配置。如果没有挂载 `/app/data`，数据只会存在于容器内部，容器删除后数据会丢失。

### Q: 如何修改密码？

登录系统后，进入 **「账户设置」** 页面修改密码。
