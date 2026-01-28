"""
示例: 如何在 pytest 中使用 callback-tool 模拟 WhatsApp 消息回调

前置条件:
    1. 启动 callback-tool 服务: cd callback-tool && ./start.sh
    2. pip install requests pytest

运行:
    pytest test_example.py -v
"""
import time
import pytest
from callback_client import CallbackClient


# ============ Fixtures ============

@pytest.fixture(scope="session")
def callback():
    """回调客户端 - 整个测试会话共享"""
    client = CallbackClient("http://localhost:8000")
    # 验证服务可用
    try:
        scenes = client.list_scenes()
        print(f"\n[callback-tool] 已连接，共 {len(scenes)} 个场景")
    except Exception as e:
        pytest.skip(f"callback-tool 服务未启动: {e}")
    return client


# ============ 测试用例 ============

class TestWhatsAppCallback:
    """WhatsApp 消息回调测试"""

    def test_basic_message_callback(self, callback):
        """测试: 基本消息回调"""
        result = callback.fire(
            "whatsapp-message",
            sender_wa_id="8613800001111",
            sender_name="测试用户A",
            message_body="你好，这是自动化测试",
        )

        assert result["success"] is True, f"回调失败: {result['message']}"
        print(f"回调成功，耗时 {result['duration_ms']}ms")

    def test_callback_with_different_sender(self, callback):
        """测试: 不同发送者的消息回调"""
        result = callback.fire(
            "whatsapp-message",
            sender_wa_id="8613900002222",
            sender_name="用户B",
            message_body="Hello World",
        )

        assert result["success"] is True

    def test_callback_with_defaults(self, callback):
        """测试: 使用默认变量（只传必要参数）"""
        result = callback.fire("whatsapp-message")

        assert result["success"] is True
        # 默认值: sender_wa_id=8613806691211, message_body=你好

    def test_dry_run_preview(self, callback):
        """测试: dry_run 模式预览请求内容"""
        result = callback.fire(
            "whatsapp-message",
            dry_run=True,
            sender_wa_id="8613800003333",
            message_body="预览测试",
        )

        assert result["success"] is True
        assert "Dry Run" in result["message"]
        # 检查渲染后的 body 包含变量值
        assert "8613800003333" in result["request_body"]
        assert "预览测试" in result["request_body"]
        assert result["response_status"] is None  # dry_run 不实际发送


class TestCallbackIntegrationFlow:
    """
    集成流程示例: 业务操作 + 回调模拟 + 状态验证

    实际使用时，替换为你的业务 API 调用和断言。
    """

    def test_message_receive_flow(self, callback):
        """
        完整流程示例:
        1. (可选) 调用业务接口创建会话
        2. 模拟 WhatsApp 消息回调
        3. (可选) 查询业务接口验证消息已入库
        """
        # Step 1: 你的业务操作 (示例)
        # response = requests.post("https://your-api.com/conversations", json={...})
        # conversation_id = response.json()["id"]

        # Step 2: 模拟 WhatsApp 用户发来消息
        result = callback.fire(
            "whatsapp-message",
            sender_wa_id="8613800001111",
            message_body="用户回复的消息",
        )
        assert result["success"] is True

        # Step 3: 等待业务处理
        time.sleep(1)

        # Step 4: 验证业务状态 (示例)
        # response = requests.get(f"https://your-api.com/messages?from=8613800001111")
        # assert response.json()["total"] > 0
