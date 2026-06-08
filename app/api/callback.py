"""回调场景执行 API"""
import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request

from app.models.schemas import (
    CallbackResponse, CallbackVerifyResponse, LogQueryResponse, LogVerifyConfig,
    Scene, SceneSummary, ReloadResponse
)
from app.services.scene_loader import scene_loader
from app.services.http_sender import http_sender
from app.services.renderer import renderer
from app.services.sls_query import sls_query_service
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


def _build_verify_config(scene: Scene, variables: dict, overrides: dict) -> LogVerifyConfig:
    """根据场景配置、变量和请求覆盖项生成最终 SLS 查询配置。"""
    if not scene.verify:
        raise HTTPException(status_code=400, detail=f"场景未配置 verify: {scene.id}")

    values = scene.verify.model_dump()
    for key, value in overrides.items():
        if value is not None:
            values[key] = value

    rendered = {}
    for key, value in values.items():
        if isinstance(value, str):
            rendered[key] = renderer.render(value, variables)
        else:
            rendered[key] = value

    return LogVerifyConfig(**rendered)


@router.post("/callback/{scene_id}/verify", response_model=CallbackVerifyResponse)
async def execute_callback_and_verify(
    scene_id: str,
    request: Request,
    env: str = Query(default=None, description="目标环境"),
    dry_run: bool = Query(default=False, description="仅预览不发送、不查询"),
    project: Optional[str] = Query(default=None, description="覆盖 SLS Project"),
    logstore: Optional[str] = Query(default=None, description="覆盖 SLS Logstore"),
    query: Optional[str] = Query(default=None, description="覆盖 SLS 查询条件"),
    from_time: Optional[str] = Query(default=None, description="覆盖查询开始时间"),
    to_time: Optional[str] = Query(default=None, description="覆盖查询结束时间"),
    wait_seconds: Optional[float] = Query(default=None, description="覆盖发送后等待秒数"),
    max_results: Optional[int] = Query(default=None, description="覆盖最多返回日志条数"),
):
    """执行回调并查询 SLS 验证是否收到日志。"""
    scene = scene_loader.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail=f"场景不存在: {scene_id}")

    if env is None:
        env = config.default_env

    body_params = None
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            body_params = await request.json()
        except Exception:
            pass

    query_params = dict(request.query_params)
    variables = _merge_variables(scene, env, query_params, body_params)
    callback_result = await http_sender.send(scene, variables, dry_run)

    verify_config = _build_verify_config(
        scene,
        variables,
        {
            "project": project,
            "logstore": logstore,
            "query": query,
            "from_time": from_time,
            "to_time": to_time,
            "wait_seconds": wait_seconds,
            "max_results": max_results,
        },
    )

    if dry_run:
        verification = LogQueryResponse(
            success=True,
            message="[Dry Run] 仅预览，未查询 SLS",
            project=verify_config.project,
            logstore=verify_config.logstore,
            query=verify_config.query,
            from_time=verify_config.from_time,
            to_time=verify_config.to_time,
        )
        return CallbackVerifyResponse(
            success=True,
            message="[Dry Run] 回调和日志查询均未实际执行",
            callback=callback_result,
            verification=verification,
        )

    if not callback_result.success:
        return CallbackVerifyResponse(
            success=False,
            message=f"回调发送失败: {callback_result.message}",
            callback=callback_result,
            verification=None,
        )

    if verify_config.wait_seconds > 0:
        await asyncio.sleep(verify_config.wait_seconds)

    verification = await asyncio.to_thread(sls_query_service.query, verify_config)
    return CallbackVerifyResponse(
        success=callback_result.success and verification.success,
        message="回调已发送且 SLS 命中日志" if verification.success else "回调已发送，但 SLS 未命中日志",
        callback=callback_result,
        verification=verification,
    )


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
