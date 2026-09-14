# 途间 · LangGraph 智能旅行助手

基于 LangChain、LangGraph、FastAPI、MCP、PostgreSQL 与 Vue 3 的智能旅行规划应用。从旅行需求出发，查询真实景点、天气与酒店，生成多日行程与预算，并支持地图标记、路线查询与导出。

## 功能

- 旅行需求表单 → 真实景点、天气和酒店查询 → 多日行程与预算。
- LangGraph 并行查询、结构化草案、业务校验，最多修正一次。
- 可调用地图工具的旅行对话，PostgreSQL 检查点保存上下文和未完成状态。
- 历史行程、自然语言修改并另存新行程、真实规划进度。
- 地图标记、实际步行 / 驾车 / 公共交通路线查询、图片及 PDF 导出。
- 模型选择 POI ID，代码回填真实名称、地址、坐标；费用明确标为估算。

## 技术栈

- **后端**：Python 3.14 · FastAPI · LangChain · LangGraph · MCP · PostgreSQL
- **前端**：Vue 3 · Vite · TypeScript
- **数据**：高德 Web 服务 API / JS API；Unsplash（可选图片）

## 本机启动

Windows 下先双击根目录的 `start_backend.cmd`，等终端显示 `Application startup complete`，再双击 `start_frontend.cmd`。两个终端都应保持打开；只启动 Vite 能显示页面，但不能查询数据或生成行程。

IDE 中可以直接运行项目根目录的 `run.py`，它会自动使用项目 `.venv`，转入真正的后端入口 `backend/run.py`。不要运行 `app/api/main.py` 或 `mcp_server.py` 代替后端入口，MCP 服务由后端自动管理。

本项目按 Python 3.14 验证。终端位于项目根目录：

```powershell
# 后端自动启动本机 MCP 子进程，退出后端时自动关闭
.\.venv\Scripts\python.exe backend\run.py
```

另开一个终端启动前端：

```powershell
cd frontend
npm run dev
```

- 页面地址：<http://127.0.0.1:5173>
- 接口文档：<http://127.0.0.1:8000/docs>
- 终端对话入口：`.\.venv\Scripts\python.exe backend\run_loop.py`

## 从干净环境安装

```powershell
uv venv --python 3.14 .venv
uv pip install --python .venv\Scripts\python.exe -r backend\requirements.lock
cd frontend
npm ci
```

1. 复制 `backend/.env.example` 为 `backend/.env`，填写 DeepSeek、高德 Web 服务 Key 和独立 PostgreSQL 数据库的连接信息。数据库应事先创建，应用仅在该库中创建业务表和 LangGraph 检查点表。
2. 复制 `frontend/.env.example` 为 `frontend/.env`，填写高德浏览器 JS Key 与所需安全密钥。
3. 后端 Web 服务 Key 与前端 JS Key 不能混用；无 JS Key 时，文字行程与后端查询仍可使用。

> `.env` 含敏感信息，已被 `.gitignore` 排除，请勿提交到版本控制。

## 测试

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
# 下项会调用收费模型、查询高德，并在专用数据库保存示例记录：
..\.venv\Scripts\python.exe tests\live_smoke.py --run
cd ..\frontend
npm run build
```

生产构建位于 `frontend/dist`，独立部署前需为前端配置 API 地址或反向代理。这是面向本机学习与演示的单用户应用，没有用户登录、租户隔离或公网部署配置。