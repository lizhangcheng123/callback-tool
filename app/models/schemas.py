"""数据模型定义"""
from typing import Optional, Any
from pydantic import BaseModel, Field


class Scene(BaseModel):
    """单个场景配置"""
    id: str = Field(description="场景唯一标识")
    name: str = Field(description="场景名称")
    description: str = Field(default="", description="场景描述")
    url: str = Field(description="请求 URL (支持模板变量)")
    method: str = Field(default="POST", description="HTTP 方法")
    headers: dict[str, str] = Field(default_factory=dict, description="请求头")
    body: str = Field(default="", description="请求体 (支持模板变量)")
    defaults: dict[str, Any] = Field(default_factory=dict, description="默认变量值")


class SceneStep(BaseModel):
    """批量场景中的单个步骤"""
    scene: str = Field(description="场景 ID")
    delay_after: float = Field(default=0.0, description="执行后延迟秒数")


class Scenario(BaseModel):
    """批量场景配置"""
    id: str = Field(description="批量场景唯一标识")
    name: str = Field(description="批量场景名称")
    description: str = Field(default="", description="批量场景描述")
    steps: list[SceneStep] = Field(default_factory=list, description="执行步骤")


class ScenesConfig(BaseModel):
    """场景配置文件结构"""
    environments: dict[str, dict] = Field(default_factory=dict, description="环境变量")
    scenes: dict[str, Scene] = Field(default_factory=dict, description="场景定义")
    scenarios: dict[str, Scenario] = Field(default_factory=dict, description="批量场景定义")


class CallbackResponse(BaseModel):
    """回调执行响应"""
    success: bool = Field(description="是否成功")
    message: str = Field(description="结果消息")
    scene_id: str = Field(default="", description="场景 ID")
    scene_name: str = Field(default="", description="场景名称")
    request_url: Optional[str] = Field(default=None, description="请求 URL")
    request_method: Optional[str] = Field(default=None, description="请求方法")
    request_headers: Optional[dict[str, str]] = Field(default=None, description="请求头")
    request_body: Optional[str] = Field(default=None, description="请求体")
    response_status: Optional[int] = Field(default=None, description="响应状态码")
    response_body: Optional[str] = Field(default=None, description="响应体")
    duration_ms: Optional[float] = Field(default=None, description="耗时毫秒")


class ScenarioResponse(BaseModel):
    """批量场景执行响应"""
    success: bool = Field(description="是否全部成功")
    scenario_id: str = Field(description="批量场景 ID")
    scenario_name: str = Field(description="批量场景名称")
    total_steps: int = Field(description="总步骤数")
    completed_steps: int = Field(description="已完成步骤数")
    results: list[CallbackResponse] = Field(default_factory=list, description="每步执行结果")


class SceneSummary(BaseModel):
    """场景摘要信息"""
    id: str
    name: str
    description: str
    method: str
    url: str


class ScenarioSummary(BaseModel):
    """批量场景摘要信息"""
    id: str
    name: str
    description: str
    steps_count: int


class ReloadResponse(BaseModel):
    """重载配置响应"""
    success: bool
    message: str
    scenes_count: int = Field(default=0, description="场景数量")
    scenarios_count: int = Field(default=0, description="批量场景数量")
