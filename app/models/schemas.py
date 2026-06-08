"""数据模型定义"""
from typing import Optional, Any
from pydantic import BaseModel, Field


class LogVerifyConfig(BaseModel):
    """SLS 日志验证配置"""
    project: str = Field(description="SLS Project，支持模板变量")
    logstore: str = Field(description="SLS Logstore，支持模板变量")
    query: str = Field(description="SLS 查询条件，支持模板变量")
    from_time: str = Field(default="5 minutes ago", description="查询开始时间")
    to_time: str = Field(default="now", description="查询结束时间")
    endpoint: str = Field(default="ap-southeast-1.log.aliyuncs.com", description="SLS endpoint")
    profile: str = Field(default="default", description="aliyun CLI profile")
    max_results: int = Field(default=20, description="最多返回日志条数")
    wait_seconds: float = Field(default=2.0, description="发送回调后等待日志落库时间")


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
    verify: Optional[LogVerifyConfig] = Field(default=None, description="回调后的日志验证配置")


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


class LogEntry(BaseModel):
    """SLS 日志记录"""
    time: Optional[str] = Field(default=None, description="日志时间戳")
    pod: Optional[str] = Field(default=None, description="Pod 名称")
    path: Optional[str] = Field(default=None, description="日志路径")
    content: str = Field(default="", description="日志内容")
    raw: dict[str, Any] = Field(default_factory=dict, description="原始日志记录")


class LogQueryResponse(BaseModel):
    """SLS 查询响应"""
    success: bool = Field(description="查询是否成功")
    message: str = Field(default="", description="结果消息")
    project: str = Field(default="", description="SLS Project")
    logstore: str = Field(default="", description="SLS Logstore")
    query: str = Field(default="", description="查询条件")
    from_time: str = Field(default="", description="查询开始时间")
    to_time: str = Field(default="", description="查询结束时间")
    count: int = Field(default=0, description="返回日志条数")
    logs: list[LogEntry] = Field(default_factory=list, description="日志记录")


class LogQueryRequest(BaseModel):
    """SLS 查询请求"""
    project: str = Field(description="SLS Project")
    logstore: str = Field(description="SLS Logstore")
    query: str = Field(description="SLS 查询条件")
    from_time: str = Field(default="5 minutes ago", description="查询开始时间")
    to_time: str = Field(default="now", description="查询结束时间")
    endpoint: str = Field(default="ap-southeast-1.log.aliyuncs.com", description="SLS endpoint")
    profile: str = Field(default="default", description="aliyun CLI profile")
    max_results: int = Field(default=20, description="最多返回日志条数")


class CallbackVerifyResponse(BaseModel):
    """回调执行 + SLS 验证响应"""
    success: bool = Field(description="回调和日志验证是否都成功")
    message: str = Field(default="", description="结果消息")
    callback: CallbackResponse = Field(description="回调执行结果")
    verification: Optional[LogQueryResponse] = Field(default=None, description="日志验证结果")


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
