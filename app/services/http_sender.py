"""HTTP 发送服务"""
import time
from typing import Optional
import httpx

from app.models.schemas import Scene, CallbackResponse
from app.services.renderer import renderer


class HttpSender:
    """HTTP 请求发送器"""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def send(
        self,
        scene: Scene,
        variables: dict,
        dry_run: bool = False
    ) -> CallbackResponse:
        """执行 HTTP 请求

        Args:
            scene: 场景配置
            variables: 渲染变量 (已合并 defaults、query params、body)
            dry_run: 仅渲染不发送

        Returns:
            回调响应
        """
        try:
            # 渲染 URL
            url = renderer.render(scene.url, variables)

            # 渲染 headers
            headers = renderer.render_dict(scene.headers, variables)

            # 渲染 body
            body = renderer.render(scene.body, variables) if scene.body else None

            if dry_run:
                return CallbackResponse(
                    success=True,
                    message="[Dry Run] 仅预览，未实际发送",
                    scene_id=scene.id,
                    scene_name=scene.name,
                    request_url=url,
                    request_method=scene.method,
                    request_headers=headers,
                    request_body=body,
                )

            # 实际发送请求
            start_time = time.time()

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=scene.method,
                    url=url,
                    headers=headers,
                    content=body,
                )

            duration_ms = (time.time() - start_time) * 1000

            return CallbackResponse(
                success=200 <= response.status_code < 300,
                message="请求成功" if 200 <= response.status_code < 300 else f"HTTP {response.status_code}",
                scene_id=scene.id,
                scene_name=scene.name,
                request_url=url,
                request_method=scene.method,
                request_headers=headers,
                request_body=body,
                response_status=response.status_code,
                response_body=response.text[:2000],  # 限制响应长度
                duration_ms=round(duration_ms, 2),
            )

        except httpx.TimeoutException:
            return CallbackResponse(
                success=False,
                message="请求超时",
                scene_id=scene.id,
                scene_name=scene.name,
            )
        except httpx.RequestError as e:
            return CallbackResponse(
                success=False,
                message=f"请求错误: {str(e)}",
                scene_id=scene.id,
                scene_name=scene.name,
            )
        except Exception as e:
            return CallbackResponse(
                success=False,
                message=f"发送失败: {str(e)}",
                scene_id=scene.id,
                scene_name=scene.name,
            )


# 全局实例
http_sender = HttpSender()
