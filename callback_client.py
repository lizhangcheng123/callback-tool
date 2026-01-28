"""
Callback Tool 客户端 - 用于在 pytest 中调用回调模拟服务

使用方式:
    from callback_client import CallbackClient

    client = CallbackClient()
    result = client.fire("whatsapp-message", sender_wa_id="8613800001111")
"""
import requests
from typing import Optional


class CallbackClient:
    """回调模拟服务客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def fire(
        self,
        scene_id: str,
        env: str = None,
        dry_run: bool = False,
        **variables
    ) -> dict:
        """触发回调场景

        Args:
            scene_id: 场景 ID，如 "whatsapp-message"
            env: 目标环境，默认使用服务端配置
            dry_run: True 则仅预览不实际发送
            **variables: 场景变量，如 sender_wa_id="8613800001111"

        Returns:
            响应字典，包含 success, message, response_status 等

        Raises:
            AssertionError: 回调执行失败时
        """
        params = {}
        if env:
            params["env"] = env
        if dry_run:
            params["dry_run"] = "true"

        resp = requests.post(
            f"{self.base_url}/api/callback/{scene_id}",
            params=params,
            json=variables if variables else None,
        )
        resp.raise_for_status()
        return resp.json()

    def fire_scenario(
        self,
        scenario_id: str,
        env: str = None,
        dry_run: bool = False,
        **variables
    ) -> dict:
        """触发批量场景

        Args:
            scenario_id: 批量场景 ID，如 "full-order-flow"
            **variables: 公共变量，应用到所有步骤
        """
        params = {}
        if env:
            params["env"] = env
        if dry_run:
            params["dry_run"] = "true"

        resp = requests.post(
            f"{self.base_url}/api/scenario/{scenario_id}",
            params=params,
            json=variables if variables else None,
        )
        resp.raise_for_status()
        return resp.json()

    def list_scenes(self) -> list[dict]:
        """列出所有可用场景"""
        resp = requests.get(f"{self.base_url}/api/scenes")
        resp.raise_for_status()
        return resp.json()

    def reload(self) -> dict:
        """热加载配置"""
        resp = requests.post(f"{self.base_url}/api/scenes/reload")
        resp.raise_for_status()
        return resp.json()
