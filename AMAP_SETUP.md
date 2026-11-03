# 高德配置与换网络说明

本项目需要两种不同的高德 Key。配置完成后，在浏览器使用 `http://127.0.0.1:5173/`。

| 配置 | 用途 | 控制台限制 |
| --- | --- | --- |
| `backend/.env` 的 `AMAP_API_KEY` | Web 服务：后端 / MCP 查询景点、天气、酒店和路线 | IP 白名单，识别后端对外请求的公网出口 IP |
| `frontend/.env` 的 `VITE_AMAP_WEB_KEY` | Web 端（JS API）：浏览器显示地图 | 域名白名单，本机填写控制台允许的 `127.0.0.1` |
| `frontend/.env` 的 `VITE_AMAP_SECURITY_CODE` | 与浏览器 JS Key 配套的安全密钥 | 与同一把 JS Key 配套 |

## 动态热点：IP 白名单可以不设置吗？

高德官方 FAQ 说明 Web 服务 Key 的 IP 白名单：

> 此项为非必填，但强烈建议用户在线上正常使用时为 Key 设置一个 IP 白名单。

来源：[高德官方 IP 白名单说明](https://lbs.amap.com/faq/webservice/webservice-api/basic-configuration/43238)，于 2026-11-03 查阅。

用于个人本地开发或课堂演示时，如果当前账号控制台允许留空，可以清空 **Web 服务 Key 的 IP 白名单**并保存，然后重新查询一次景点确认生效。这样，更换手机热点或校园网时就不必反复填写出口 IP。本项目发布时尚未替账号执行清空操作；以实际控制台能力和调用结果为准。

取消 IP 限制后，任何拿到这把 Key 的人都可能使用它；Web 服务 Key 应只保存在后端环境变量中，不上传 GitHub，也不要和前端 JS Key 混用。浏览器 JS Key 的域名配置仍需单独保留。

如果控制台要求填写 IP，或者希望保留 IP 限制，继续使用白名单方案：连接实际演示网络后，查询其公网出口 IP，填入 Web 服务 Key 的 IP 白名单，再测试。重新连接手机热点后，出口 IP 可能变化。

## 多人共享：使用固定出口的后端

把后端和 MCP 放在具有固定出口公网 IP 的服务器上，将该出口 IP 加入 Web 服务 Key 的白名单。所有人访问同一个前端网址，由服务器调用高德；用户切换 Wi-Fi 或热点不影响服务器出口。

仓库提供 `docker-compose.yml`、前后端 `Dockerfile` 和 `deploy.env.example`，可作为部署起点：

```sh
cp deploy.env.example .env
# 编辑 .env，填写自己的模型、高德和数据库配置
docker compose up -d --build
```

前端域名或服务器地址需要加入 JS Key 的域名白名单。修改 `VITE_AMAP_*` 后需要重新构建前端镜像。若服务器位于 NAT 后，请确认它的实际出站公网 IP；仅有固定域名、DDNS 或容器，并不能保证出站 IP 固定。

当前项目是单用户演示应用，没有登录鉴权。共享部署应限制使用者范围；直接开放 `/api` 会允许访问者消耗部署账号的模型费用和高德配额。仓库中的 Compose 配置已做静态配置检查，服务器部署仍需在目标环境验证。

## 拉取后独立运行

1. 克隆仓库，按 README 安装 Python、前端依赖，并创建自己的 PostgreSQL 数据库。
2. 首次配置时，复制 `backend/.env.example` 为 `backend/.env`，填写自己的模型 Key、高德 **Web 服务** Key 和数据库连接。
3. 复制 `frontend/.env.example` 为 `frontend/.env`，填写自己的 **Web 端（JS API）** Key 和配套安全密钥。
4. 按前述说明选择清空允许清空的 IP 限制，或配置自己网络的出口 IP。各自申请 Key 可以分开账号和配额，但仍需处理动态 IP。
5. 依次运行 `start_backend.cmd` 和 `start_frontend.cmd`，保留运行服务的窗口，然后访问 `http://127.0.0.1:5173/`。

每个人的 `.env` 不随 Git 传递。数据库里的历史行程和聊天记录也不会随着 `git clone` 复制，首次运行的历史记录为空。

## 常见错误

| 现象 | 原因和处理 |
| --- | --- |
| `10005 / INVALID_USER_IP` | 请求的公网出口 IP 不在 Web 服务 Key 白名单中；检查后端 Key 的 IP 限制 |
| `10006 / INVALID_USER_DOMAIN` | 绑定域名无效；检查浏览器 JS Key 的类型、域名白名单和当前网页地址 |
| 地图工具超时或返回格式异常，但 `/health` 正常 | 检查后端启动窗口和 MCP 子进程；重新启动本项目后端后再测试实际查询 |
| 修改了 `.env` 仍使用旧配置 | 重启对应服务；Docker 前端的 `VITE_` 参数需要重新构建 |

`127.0.0.1`、`localhost`、`192.168.x.x` 都不能代替高德看到的公网出口 IP。不要通过伪造来源或修改错误返回来掩盖白名单问题。

错误码依据：[高德官方错误码表](https://lbs.amap.com/api/webservice/guide/tools/info)，于 2026-11-03 查阅。
