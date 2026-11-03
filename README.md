# 途间 · LangGraph 智能旅行助手

> 一个会查真实景点、天气和酒店，也会把结果组织成可执行行程的 AI 旅行规划应用。

途间使用 **LangGraph** 编排资料采集、行程生成、结构化校验与修复流程，以 **FastAPI** 提供规划、对话和地图接口，并通过 **Vue 3** 展示每日行程、预算、地图与路线。项目同时使用 PostgreSQL 保存历史计划和 LangGraph 对话检查点，适合学习完整的 AI 应用数据流，而不只是一次性的模型问答。

## 项目亮点

- **真实数据参与规划**：从高德接口获取景点、天气、酒店、POI 与路线信息。
- **LangGraph 并行工作流**：景点、天气和酒店三个节点并行执行，再汇合生成行程草案。
- **结构化输出保障**：Pydantic 校验模型结果；失败时进入一次修复流程，避免错误 JSON 直接返回前端。
- **持久化旅行对话**：Agent 可以调用地图工具，PostgreSQL Checkpointer 保存会话上下文和中断状态。
- **历史与二次修改**：保存历史行程，支持用自然语言修改已有计划并另存为新行程。
- **完整结果页**：展示每日安排、预算、天气、地图标记、真实路线，并支持图片与 PDF 导出。
- **旅行杂志式界面**：本地风景图以水墨晕染过渡，规划进度展示真实阶段，行程支持日期导航和分段阅读。
- **可验证的数据边界**：模型只选择 POI ID，名称、地址和坐标由代码回填；费用明确标记为估算值。

## 工作流程

```mermaid
flowchart LR
    A[旅行需求] --> B{LangGraph}
    B --> C[搜索景点]
    B --> D[查询天气]
    B --> E[搜索酒店]
    C --> F[生成结构化草案]
    D --> F
    E --> F
    F --> G[业务校验]
    G -->|通过| H[补全真实数据]
    G -->|失败| I[修复一次]
    I --> H
    H --> J[保存并返回行程]
```

核心图定义位于 `backend/app/agents/trip_planner_agent.py`。规划图之外，`chat_agent.py` 还实现了可循环调用地图工具的对话 Agent。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite、Ant Design Vue、Axios |
| 后端 | Python、FastAPI、Pydantic、httpx |
| AI 编排 | LangChain、LangGraph、OpenAI 兼容模型接口 |
| 数据与状态 | PostgreSQL、LangGraph PostgreSQL Checkpointer |
| 外部服务 | 高德 Web 服务 / JS API、Unsplash（可选） |
| 导出 | html2canvas、jsPDF |

## 项目结构

```text
LangGraph_Trip_Planner/
├─ backend/
│  ├─ app/agents/       # 行程规划图与旅行对话 Agent
│  ├─ app/api/routes/   # trip、chat、map、poi 接口
│  ├─ app/models/       # 请求、行程和地图数据模型
│  ├─ app/services/     # LLM、高德、图片、存储与运行时服务
│  └─ tests/            # API、工作流与高德 HTTP 测试
├─ frontend/
│  └─ src/
│     ├─ views/         # 首页、结果页、对话页
│     ├─ components/    # 地图组件
│     └─ services/      # 后端 API 调用
├─ run.py               # IDE 友好的后端启动入口
├─ start_backend.cmd
└─ start_frontend.cmd
```

## 本机启动

### 1. 准备环境

- Python 3.14（当前项目验证版本）
- Node.js 22.18 或更新版本、npm，以及用于安装 Python 环境的 uv
- PostgreSQL，并提前创建独立数据库
- DeepSeek 或其他 OpenAI 兼容模型 Key
- 高德 Web 服务 Key；如需前端地图，再准备 JS API Key 与安全密钥

### 2. 安装依赖

```powershell
uv venv --python 3.14 .venv
uv pip install --python .venv\Scripts\python.exe -r backend\requirements.lock

cd frontend
npm ci
cd ..
```

### 3. 配置环境变量

复制 `backend/.env.example` 为 `backend/.env`，填写：

```dotenv
LLM_API_KEY=
LLM_MODEL_ID=deepseek-v4-flash
LLM_BASE_URL=https://api.deepseek.com
AMAP_API_KEY=
DATABASE_URL=postgresql://postgres:replace_me@localhost:5432/langgraph_trip_planner
UNSPLASH_ACCESS_KEY=
```

再复制 `frontend/.env.example` 为 `frontend/.env`，填写高德浏览器 JS Key 与所需安全密钥。后端 Web 服务 Key 与前端 JS API Key 不能混用。

换网络反复出现 `10005`、前端地图报 `10006`，以及同学自行配置 Key 的步骤，见 [高德配置与换网络说明](AMAP_SETUP.md)。高德官方说明 Web 服务 Key 的 IP 白名单是非必填项；是否能清空，以当前账号控制台和实测为准。需要保留白名单时，可将后端部署到具有固定出口公网 IP 的服务器。

> `.env` 含敏感信息并已被 `.gitignore` 排除，请勿提交到版本控制。

### 4. 启动服务

Windows 下可以依次双击根目录的 `start_backend.cmd` 和 `start_frontend.cmd`，也可以在两个终端中运行：

```powershell
# 终端 1：后端会自动管理本机 MCP 子进程
.\.venv\Scripts\python.exe backend\run.py
```

```powershell
# 终端 2
cd frontend
npm run dev
```

- 前端：<http://127.0.0.1:5173>
- Swagger 文档：<http://127.0.0.1:8000/docs>
- 终端对话：`.\.venv\Scripts\python.exe backend\run_loop.py`

启动脚本固定使用 `127.0.0.1:8000` 和 `127.0.0.1:5173`；重复启动时会检查已有服务。后端自动管理 MCP 子进程。首次克隆不会包含原作者的密钥、数据库或历史记录，需填写自己的 `.env`。

## 主要接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `POST` | `/api/trip/plan` | 生成完整旅行计划 |
| `POST` | `/api/trip/plan/stream` | 以流式事件返回真实规划进度 |
| `GET` | `/api/trip/plans` | 查询历史行程 |
| `POST` | `/api/trip/plans/{plan_id}/revise` | 用自然语言修改并保存新版本 |
| `POST` | `/api/chat/send` | 与可调用地图工具的 Agent 对话 |
| `GET` | `/api/map/poi` | 查询兴趣点 |
| `GET` | `/api/map/weather` | 查询天气 |
| `POST` | `/api/map/route` | 查询步行、驾车或公共交通路线 |

完整参数和响应模型请以启动后的 Swagger 文档为准。

## 测试与构建

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider

cd ..\frontend
node --test tests/planningProgress.test.ts
npm run build
```

需要真实调用模型、高德并写入专用数据库时，再运行：

```powershell
cd backend
..\.venv\Scripts\python.exe tests\live_smoke.py --run
```

## 当前定位

这是一个面向学习与演示的单用户项目，重点展示 LangGraph 工作流、工具调用、结构化校验、状态持久化以及前后端协作。仓库提供 Docker Compose、前后端镜像与 nginx 反向代理配置，详见 [高德配置与换网络说明](AMAP_SETUP.md)。当前没有用户登录或租户隔离，共享部署时需要限制使用者范围。
