# syntax=docker/dockerfile:1
# 途间后端镜像：Python 3.14 + FastAPI + 本地 MCP 子进程
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app

# curl 仅用于容器健康检查；项目依赖都是 manylinux wheel，无需 gcc/libpq
# 国内服务器加速：把 Debian 源切到阿里云镜像（否则 apt-get update 会卡很久甚至断流）
RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list 2>/dev/null || true \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖清单，利用 Docker 层缓存（改代码不重装依赖）
# 注意：这里用 requirements.txt（顶层固定版本），而不是 requirements.lock，
# 因为 lock 是 Windows 下生成的、包含 pywin32，Linux 上无法安装。
COPY requirements.txt ./
RUN pip install -r requirements.txt

# 复制后端源码：app 包 + 本地 MCP 服务 + 入口
COPY app ./app
COPY mcp_server.py run.py ./

# 后端要绑定 0.0.0.0 才能被 nginx 容器反向代理访问
ENV HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["python", "run.py"]