# 生产部署指南

本文档详细说明如何将应用部署到生产环境，包括安全加固、性能优化和高可用配置。

---

## 📋 部署前检查清单

### 安全审计

- [ ] **秘密管理**
  - [ ] 生成强 `SECRET_KEY`（≥32 字节）：`openssl rand -hex 32`
  - [ ] 修改初始超管密码：`FIRST_SUPERUSER_PASSWORD`
  - [ ] 修改数据库密码：`MYSQL_PASSWORD`
  - [ ] 修改 SMTP 凭证（若使用）
  - [ ] 使用密钥管理服务（AWS Secrets Manager / Azure Key Vault）

- [ ] **网络隔离**
  - [ ] 数据库仅允许后端访问（不暴露 3306）
  - [ ] 后端仅通过 HTTPS 暴露
  - [ ] 启用防火墙规则

- [ ] **认证加固**
  - [ ] 启用 HTTPS（Let's Encrypt + Nginx）
  - [ ] 设置 CORS 到具体域名（不使用 `*`）
  - [ ] 配置 HTTP 安全头（HSTS、CSP）

### 性能审计

- [ ] **数据库**
  - [ ] 创建适当索引（见下文）
  - [ ] 配置慢查询日志
  - [ ] 定期备份

- [ ] **缓存**
  - [ ] 启用静态资源缓存
  - [ ] 考虑添加 Redis 缓存层（可选）

- [ ] **日志**
  - [ ] 启用审计日志：`LOG_TO_FILE=true`
  - [ ] 配置日志轮转（避免磁盘满）
  - [ ] 集成 Sentry 错误追踪：`SENTRY_DSN=<your-dsn>`

---

## 🐳 Docker Compose 部署（推荐用于小规模）

适合中小型应用（单机）。

### 步骤 1：准备服务器

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证
docker --version
docker compose --version
```

### 步骤 2：准备生产 .env

编辑 `.env`，应用生产配置：

```env
# ================================
# Application
# ================================
APP_ENV=production
PROJECT_NAME="Enterprise App"
SECRET_KEY=<生成的随机字符串>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# ================================
# Database
# ================================
MYSQL_SERVER=db                           # 保持为 service 名称
MYSQL_PORT=3306
MYSQL_USER=appuser
MYSQL_PASSWORD=<强密码，长度≥12>
MYSQL_DB=appdb
MYSQL_ROOT_PASSWORD=<root 密码>

# ================================
# First Superuser
# ================================
FIRST_SUPERUSER=admin
FIRST_SUPERUSER_PASSWORD=<强密码，长度≥12>  # ⚠️ 首次登录后立即修改

# ================================
# CORS
# ================================
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]  # 改为实际域名
FRONTEND_HOST=https://yourdomain.com

# ================================
# Email
# ================================
SMTP_HOST=smtp.gmail.com              # 或其他邮件服务
SMTP_PORT=587
SMTP_TLS=true
SMTP_SSL=false
SMTP_USER=<your-email>
SMTP_PASSWORD=<your-app-password>      # 应用密码，非登录密码
EMAILS_FROM_EMAIL=noreply@yourdomain.com
EMAILS_FROM_NAME="Your App"

# ================================
# Audit Log
# ================================
LOG_TO_FILE=true
LOG_FILE_PATH=/app/logs/audit.jsonl

# ================================
# Error Tracking (Sentry)
# ================================
SENTRY_DSN=https://<key>@sentry.io/<project>
ENVIRONMENT=production

# ================================
# Startup Automation
# ================================
AUTO_MIGRATE_ON_STARTUP=true
AUTO_SEED_ON_STARTUP=false              # 生产环境不自动初始化
AUTO_CREATE_TABLES_IF_NO_MIGRATIONS=false
```

### 步骤 3：准备生产 compose.yml

创建 `docker-compose.prod.yml`（覆盖默认配置）：

```yaml
version: "3.8"

services:
  db:
    image: mysql:8.0
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DB}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./my.cnf:/etc/mysql/conf.d/my.cnf:ro  # 自定义配置
    ports:
      - "3306:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - app-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    env_file: .env
    environment:
      MYSQL_SERVER: db
      MYSQL_PORT: 3306
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./backend/logs:/app/logs
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: always
    depends_on:
      - backend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-prod.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro            # SSL 证书
      - ./frontend/dist:/usr/share/nginx/html:ro
    networks:
      - app-network

volumes:
  mysql_data:
    driver: local

networks:
  app-network:
    driver: bridge
```

创建 `my.cnf`（MySQL 性能调优）：

```ini
[mysqld]
# 性能
max_connections=500
innodb_buffer_pool_size=2G
innodb_log_file_size=512M

# 日志
slow_query_log=1
slow_query_log_file=/var/log/mysql/slow.log
long_query_time=2

# 字符集
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
```

创建 `nginx-prod.conf`（HTTPS + 反向代理）：

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss;
    gzip_min_length 1000;

    # HTTP 重定向到 HTTPS
    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS 服务器
    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL 证书
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # 安全头
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # 前端 SPA
        root /usr/share/nginx/html;
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API 反向代理
        location /api/ {
            proxy_pass http://backend:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }

        # 缓存策略
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### 步骤 4：获取 SSL 证书

使用 Let's Encrypt + Certbot：

```bash
# 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 申请证书（需要域名 DNS 已指向服务器）
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 证书位置
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem

# 复制到项目
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/key.pem
sudo chown $USER:$USER ./ssl/*

# 配置自动续期（Certbot 自动处理）
sudo systemctl enable certbot.timer
```

### 步骤 5：启动应用

```bash
docker compose -f docker-compose.prod.yml up -d

# 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 验证服务
curl -I https://yourdomain.com
curl https://yourdomain.com/api/v1/docs
```

### 步骤 6：备份与恢复

```bash
# 备份数据库
docker compose -f docker-compose.prod.yml exec db mysqldump \
  -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DB} > backup.sql

# 恢复数据库
docker compose -f docker-compose.prod.yml exec -T db mysql \
  -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DB} < backup.sql

# 备份 Docker Volume
docker run --rm -v mysql_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/mysql_backup.tar.gz /data
```

---

## ☁️ 云平台部署（AWS/Azure/GCP）

### AWS ECS + RDS

使用完全托管的容器和数据库服务。

1. **创建 RDS MySQL**
   - 实例类型：db.t3.medium（生产最小）
   - 多可用区：启用
   - 自动备份：7 天
   - 加密：启用

2. **创建 ECR 仓库**
   ```bash
   aws ecr create-repository --repository-name fastapi-app
   aws ecr create-repository --repository-name vue3-app
   ```

3. **推送镜像**
   ```bash
   docker build -t fastapi-app ./backend
   docker tag fastapi-app:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/fastapi-app:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/fastapi-app:latest
   ```

4. **创建 ECS Cluster** 并配置 Task Definition、Service

### Azure Container Instances + Azure Database for MySQL

类似流程，使用 Azure CLI。

---

## 📊 监控与告警

### 后端监控

启用 Sentry：

```python
# backend/app/main.py
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,  # 10% 采样
        enable_tracing=True,
    )
```

### 数据库监控

配置慢查询日志：

```sql
-- 登录 MySQL
mysql -u root -p

-- 启用慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;

-- 查看慢查询
SELECT * FROM mysql.slow_log LIMIT 10;
```

### 应用日志

集成 ELK Stack（Elasticsearch + Logstash + Kibana）或 DataDog。

---

## 🔄 更新与回滚

### 执行更新

```bash
# 拉取最新代码
git pull origin main

# 重建镜像（如果有变更）
docker compose -f docker-compose.prod.yml build

# 启动新版本
docker compose -f docker-compose.prod.yml up -d

# 验证
docker compose -f docker-compose.prod.yml logs -f backend
```

### 快速回滚

```bash
# 使用旧镜像 tag（需要提前标记）
docker compose -f docker-compose.prod.yml up -d --force-recreate

# 或恢复数据库备份
docker compose -f docker-compose.prod.yml exec -T db mysql \
  -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DB} < backup_before_update.sql
```

---

## 🎯 性能基准与调优

### 数据库索引

添加关键查询索引：

```sql
-- 用户登录快速查询
CREATE INDEX idx_user_username ON user(username);

-- 权限检查快速查询
CREATE INDEX idx_permission_full_code ON permission(full_code);

-- 审计日志时间范围查询
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);

-- 软删除过滤
CREATE INDEX idx_user_deleted_at ON user(deleted_at);
```

### 常用优化配置

| 参数 | 值 | 说明 |
|------|-----|------|
| `max_connections` | 500-1000 | 最大连接数 |
| `innodb_buffer_pool_size` | 总内存 75% | 缓冲池大小 |
| `innodb_log_file_size` | 512M-1G | 日志文件大小 |
| `query_cache_size` | 0（禁用） | MySQL 8.0 已废弃 |
| `innodb_flush_log_at_trx_commit` | 2 | 性能与安全平衡 |

---

## 🔐 安全加固清单

- [ ] 启用 HTTPS（TLS 1.2+）
- [ ] 配置 HTTP 安全头（HSTS、CSP、X-Frame-Options）
- [ ] 设置 CORS 到具体域名
- [ ] 启用审计日志
- [ ] 定期备份数据库
- [ ] 配置日志监控告警
- [ ] 定期更新依赖（检查 CVE）
- [ ] 配置 WAF（Web Application Firewall）
- [ ] 禁用 root 远程登录（MySQL）
- [ ] 启用数据库加密（TDE / 传输层加密）

---

## 📞 故障处理

### 数据库连接失败

```bash
# 检查 MySQL 容器
docker compose -f docker-compose.prod.yml logs db

# 检查网络连通性
docker compose -f docker-compose.prod.yml exec backend \
  curl http://db:3306

# 重启数据库
docker compose -f docker-compose.prod.yml restart db
```

### 高 CPU / 内存占用

```bash
# 查看容器资源使用
docker stats

# 查看 MySQL 慢查询
docker compose -f docker-compose.prod.yml exec db \
  tail -f /var/log/mysql/slow.log

# 优化查询或增加资源
```

### 磁盘空间不足

```bash
# 检查磁盘
df -h

# 清理 Docker 数据
docker system prune -a --volumes

# 定期轮转日志
# 在 logrotate 中配置
```

---

## 📖 相关资源

- [Docker 官方文档](https://docs.docker.com/)
- [MySQL 官方文档](https://dev.mysql.com/doc/)
- [Nginx 官方文档](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [AWS ECS 部署](https://docs.aws.amazon.com/ecs/)
- [Azure Container Instances](https://docs.microsoft.com/en-us/azure/container-instances/)
