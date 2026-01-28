# Callback Tool

**自动化测试回调模拟服务** - 解决异步回调场景无法自动化测试的痛点。

## 解决什么问题？

在测试涉及第三方异步回调的业务流程时（如支付通知、WhatsApp 消息、物流状态），传统方式需要：
- 手动触发第三方操作
- 等待真实回调到达
- 无法控制回调时机和内容

**Callback Tool** 让你可以：
- ✅ 在自动化测试中模拟任意回调
- ✅ 精确控制回调内容和时机
- ✅ 无需依赖真实第三方服务
- ✅ 通过 YAML 配置管理所有回调场景

## 快速开始

### 1. 启动服务

```bash
git clone https://github.com/lizhangcheng123/callback-tool.git
cd callback-tool
./start.sh
```

### 2. 触发回调

```bash
# 使用默认参数
curl -X POST http://localhost:8000/api/callback/whatsapp-message

# 自定义参数
curl -X POST "http://localhost:8000/api/callback/whatsapp-message" \
  -H "Content-Type: application/json" \
  -d '{"sender_wa_id": "8613800001111", "message_body": "测试消息"}'

# 预览模式（不实际发送）
curl -X POST "http://localhost:8000/api/callback/whatsapp-message?dry_run=true"
```

### 3. 在 pytest 中使用

```python
from callback_client import CallbackClient

callback = CallbackClient("http://localhost:8000")

def test_message_flow():
    # 1. 执行业务操作
    # ...

    # 2. 模拟 WhatsApp 消息回调
    result = callback.fire(
        "whatsapp-message",
        sender_wa_id="8613800001111",
        message_body="用户回复",
    )
    assert result["success"] is True

    # 3. 验证业务状态
    # ...
```

## 配置场景

编辑 `scenes.yaml` 添加你的回调场景：

```yaml
scenes:
  my-callback:
    name: "我的回调场景"
    url: "https://your-api.com/webhook"
    method: POST
    headers:
      Content-Type: "application/json"
    body: |
      {
        "orderId": "{{orderId}}",
        "status": "{{status}}",
        "timestamp": "{{_timestamp}}"
      }
    defaults:
      orderId: "ORD001"
      status: "SUCCESS"
```

**内置变量：**
- `{{_now}}` - 当前时间 ISO 格式
- `{{_timestamp}}` - Unix 时间戳（秒）
- `{{_timestamp_ms}}` - Unix 时间戳（毫秒）

**变量优先级：** `defaults` < `环境变量` < `URL参数` < `JSON body`

## API 端点

| 端点 | 说明 |
|------|------|
| `POST /api/callback/{scene_id}` | 执行单个回调 |
| `POST /api/scenario/{scenario_id}` | 执行批量回调流程 |
| `GET /api/scenes` | 列出所有场景 |
| `GET /api/scenarios` | 列出所有批量场景 |
| `POST /api/scenes/reload` | 热加载配置 |

**交互式文档：** http://localhost:8000/docs

## 技术栈

- FastAPI + Uvicorn
- httpx (异步 HTTP 客户端)
- PyYAML (场景配置)
- 无数据库依赖，纯 YAML 配置

## License

MIT
