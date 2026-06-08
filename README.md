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
- ✅ 发送回调后自动查询 SLS 验证 callback 服务是否收到日志

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

# 发送回调并查询 SLS 验证
curl -X POST "http://localhost:8000/api/callback/whatsapp-message/verify?env=online" \
  -H "Content-Type: application/json" \
  -d '{"sender_wa_id": "8613806691206", "message_body": "测试消息"}'
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

def test_message_callback_with_sls_verify():
    result = callback.fire_and_verify(
        "whatsapp-message",
        env="online",
        sender_wa_id="8613806691206",
        message_body="用户回复",
    )
    assert result["success"] is True
    assert result["verification"]["count"] > 0
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
    verify:
      project: "{{sls_project|default:ycloud-k8s-service-test}}"
      logstore: "ycloud-attila-callback-root"
      query: "{{orderId}}"
      from_time: "5 minutes ago"
      to_time: "now"
      endpoint: "ap-southeast-1.log.aliyuncs.com"
      profile: "default"
      max_results: 20
      wait_seconds: 2
```

**内置变量：**
- `{{_now}}` - 当前时间 ISO 格式
- `{{_timestamp}}` - Unix 时间戳（秒）
- `{{_timestamp_ms}}` - Unix 时间戳（毫秒）

**变量优先级：** `defaults` < `环境变量` < `URL参数` < `JSON body`

## SLS 验证

`verify` 配置会在 `/api/callback/{scene_id}/verify` 中生效：

1. 按场景模板发送 callback。
2. 等待 `wait_seconds`，给日志采集一点时间。
3. 调用本机 `aliyunlog log get_log_all` 查询 SLS。
4. 命中日志则整体返回 `success=true`。

默认复用你本机的阿里云 CLI OAuth profile：

```bash
aliyun configure --mode OAuth --profile default
```

如果 `aliyunlog` 不在 PATH 中，可以指定路径：

```bash
export CALLBACK_TOOL_ALIYUNLOG="$HOME/.local/bin/aliyunlog"
```

也可以只查询日志，不发送 callback：

```bash
curl -X POST "http://localhost:8000/api/logs/query" \
  -H "Content-Type: application/json" \
  -d '{
    "project": "ycloud-k8s-service-online",
    "logstore": "ycloud-attila-callback-root",
    "query": "8613806691206",
    "from_time": "1 hour ago",
    "to_time": "now",
    "max_results": 20
  }'
```

## API 端点

| 端点 | 说明 |
|------|------|
| `POST /api/callback/{scene_id}` | 执行单个回调 |
| `POST /api/callback/{scene_id}/verify` | 执行单个回调并查询 SLS 验证 |
| `POST /api/logs/query` | 查询 SLS 日志 |
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
