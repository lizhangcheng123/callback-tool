"""批量场景执行 API"""
import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request

from app.models.schemas import (
    ScenarioResponse, ScenarioSummary, Scenario
)
from app.services.scene_loader import scene_loader
from app.services.http_sender import http_sender
from app.config import config

router = APIRouter(prefix="/api", tags=["scenario"])


@router.post("/scenario/{scenario_id}", response_model=ScenarioResponse)
async def execute_scenario(
    scenario_id: str,
    request: Request,
    env: str = Query(default=None, description="目标环境"),
    dry_run: bool = Query(default=False, description="仅预览不发送"),
):
    """执行批量场景

    Body 中的变量将应用到所有步骤
    """
    # 获取批量场景
    scenario = scene_loader.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"批量场景不存在: {scenario_id}")

    # 使用默认环境
    if env is None:
        env = config.default_env

    # 解析公共变量 (从 body)
    common_vars = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            common_vars = await request.json()
        except Exception:
            pass

    # 执行每个步骤
    results = []
    for step in scenario.steps:
        # 获取场景
        scene = scene_loader.get_scene(step.scene)
        if not scene:
            results.append({
                "success": False,
                "message": f"场景不存在: {step.scene}",
                "scene_id": step.scene,
                "scene_name": "",
            })
            continue

        # 合并变量: defaults < env < common_vars
        variables = {}
        if scene.defaults:
            variables.update(scene.defaults)
        env_vars = scene_loader.get_env_variables(env)
        if env_vars:
            variables.update(env_vars)
        variables.update(common_vars)

        # 执行回调
        result = await http_sender.send(scene, variables, dry_run)
        results.append(result)

        # 步骤间延迟
        if step.delay_after > 0 and not dry_run:
            await asyncio.sleep(step.delay_after)

    # 统计结果
    success_count = sum(1 for r in results if r.success)
    all_success = success_count == len(results)

    return ScenarioResponse(
        success=all_success,
        scenario_id=scenario.id,
        scenario_name=scenario.name,
        total_steps=len(scenario.steps),
        completed_steps=success_count,
        results=results,
    )


@router.get("/scenarios", response_model=list[ScenarioSummary])
async def list_scenarios():
    """列出所有批量场景"""
    scenarios = scene_loader.list_scenarios()
    return [
        ScenarioSummary(
            id=s.id,
            name=s.name,
            description=s.description,
            steps_count=len(s.steps),
        )
        for s in scenarios
    ]


@router.get("/scenarios/{scenario_id}", response_model=Scenario)
async def get_scenario(scenario_id: str):
    """获取批量场景详情"""
    scenario = scene_loader.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"批量场景不存在: {scenario_id}")
    return scenario
