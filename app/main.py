"""FastAPI 主入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import callback, logs, scenario
from app.services.scene_loader import scene_loader
from app.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时加载场景配置
    try:
        scene_loader.load(config.scenes_file)
        scenes_count = len(scene_loader.config.scenes)
        scenarios_count = len(scene_loader.config.scenarios)
        print(f"✅ 场景配置加载完成: {scenes_count} 个场景, {scenarios_count} 个批量场景")
    except FileNotFoundError as e:
        print(f"⚠️  {e}")
        print("   请复制 scenes.example.yaml 为 scenes.yaml 并配置场景")
    except Exception as e:
        print(f"❌ 场景配置加载失败: {e}")

    yield
    print("👋 应用关闭")


app = FastAPI(
    title="Callback Tool",
    description="自动化测试回调模拟服务",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(callback.router)
app.include_router(logs.router)
app.include_router(scenario.router)


@app.get("/")
async def root():
    """首页"""
    return {
        "name": "Callback Tool",
        "description": "自动化测试回调模拟服务",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "scenes": "/api/scenes",
            "scenarios": "/api/scenarios",
            "callback": "/api/callback/{scene_id}",
            "callback_verify": "/api/callback/{scene_id}/verify",
            "logs_query": "/api/logs/query",
            "scenario": "/api/scenario/{scenario_id}",
            "reload": "/api/scenes/reload",
        }
    }


@app.get("/health")
async def health():
    """健康检查"""
    conf = scene_loader.config
    return {
        "status": "healthy",
        "scenes_loaded": conf is not None,
        "scenes_count": len(conf.scenes) if conf else 0,
        "scenarios_count": len(conf.scenarios) if conf else 0,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug
    )
