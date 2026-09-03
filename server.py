"""
server.py - Cloud Flet Web Server for Render
"""
import os
import sys

# บังคับใช้ UTF-8 เพื่อป้องกัน UnicodeEncodeError จาก Emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from contextlib import asynccontextmanager
from fastapi import FastAPI
import flet.fastapi as flet_fastapi
from app import main, BASE_DIR, DATA_DIR

@asynccontextmanager
async def lifespan(app: FastAPI):
    await flet_fastapi.app_manager.start()
    yield
    await flet_fastapi.app_manager.shutdown()

app = FastAPI(lifespan=lifespan)
app.mount("/", flet_fastapi.app(main))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    print("=" * 60)
    print("🌽 Corn Cloud Web Server (Optimized for Render)")
    print(f"🚀 Port {port}")
    print(f"💾 Data dir: {DATA_DIR}"
          + ("  [EPHEMERAL - ยังไม่ได้ผูก Persistent Disk]" if DATA_DIR == BASE_DIR else "  [PERSISTENT]"))
    print("=" * 60)
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level="info"
    )
