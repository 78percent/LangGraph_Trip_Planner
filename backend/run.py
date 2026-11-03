"""Run from any directory: python backend/run.py."""
from pathlib import Path
import sys

# IDE profilers may use runpy without adding the script directory to sys.path.
# Resolve imports relative to this file, independently of the working directory.
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import uvicorn
from app.config import get_settings
from app.services.event_loop import run_async

if __name__ == '__main__':
    settings = get_settings()
    # Keep the loop choice explicit and use one worker for per-session locks.
    server = uvicorn.Server(uvicorn.Config('app.api.main:app', host=settings.host,
                                           port=settings.port, reload=False))
    run_async(server.serve())

"""
run.py
→ 启动 uvicorn
→ 加载 FastAPI app
→ 触发 lifespan
→ lifespan 里调用 build_services()
→ 初始化数据库、Repository、Checkpointer、Amap、LLM、ChatAgent...
→ 后端正式开始接请求
"""
