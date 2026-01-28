"""回调场景执行 API"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request

from app.models.schemas import (
    CallbackResponse, Scene, SceneSummary, ReloadResponse
)
from app.services.scene_loader import scene_loader
from app.services.http_sender import http_sender
from app.config import config

router = APIRouter(prefix="/api", tags=["callback"])


def _merge_variables(
    scene: Scene,
    env: str,
    query_params: dict,
    body_params: Optional[dict]
) -> dict:
    """合并变量，优先级: defaults < env < query params < body params

    Args:
        scene: 场景配置
        env: 环境名称
        query_params: URL 查询参数
        body_params: JSON body 参数

    Returns:
        合并后的变量字典
    """
    variables = {}

    # 1. 场景默认值
    if scene.defaults:
        variables.update(scene.defaults)

    # 2. 环境变量
    env_vars = scene_loader.get_env_variables(env)
    if env_vars:
        variables.update(env_vars)

    # 3. URL 查询参数 (排除保留参数)
    reserved_params = {"env", "dry_run"}
    for key, value in query_params.items():
        if key not in reserved_params:
            variables[key] = value

    # 4. JSON body 参数
    if body_params:
        variables.update(body_params)

    return variables


@router.post("/callback/{scene_id}", response_model=CallbackResponse)
async def execute_callback(
    scene_id: str,
    request: Request,
    env: str = Query(default=None, description="目标环境"),
    dry_run: bool = Query(default=False, description="仅预览不发送"),
):
    """执行单个回调场景

    变量优先级: 场景 defaults < 环境变量 < URL query params < JSON body
    """
    # 获取场景
    scene = scene_loader.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail=f"场景不存在: {scene_id}")

    # 使用默认环境
    if env is None:
        env = config.default_env

    # 解析 body (如果是 JSON)
    body_params = None
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            body_params = await request.json()
        except Exception:
            pass

    # 合并变量
    query_params = dict(request.query_params)
    variables = _merge_variables(scene, env, query_params, body_params)

    # 执行回调
    return await http_sender.send(scene, variables, dry_run)


@router.get("/scenes", response_model=list[SceneSummary])
async def list_scenes():
    """列出所有场景"""
    scenes = scene_loader.list_scenes()
    return [
        SceneSummary(
            id=s.id,
            name=s.name,
            description=s.description,
            method=s.method,
            url=s.url,
        )
        for s in scenes
    ]


@router.get("/scenes/{scene_id}", response_model=Scene)
async def get_scene(scene_id: str):
    """获取场景详情"""
    scene = scene_loader.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail=f"场景不存在: {scene_id}")
    return scene


@router.post("/scenes/reload", response_model=ReloadResponse)
async def reload_scenes():
    """重新加载场景配置"""
    try:
        scene_loader.reload()
        conf = scene_loader.config
        return ReloadResponse(
            success=True,
            message="配置重载成功",
            scenes_count=len(conf.scenes) if conf else 0,
            scenarios_count=len(conf.scenarios) if conf else 0,
        )
    except Exception as e:
        return ReloadResponse(
            success=False,
            message=f"配置重载失败: {str(e)}",
        )
