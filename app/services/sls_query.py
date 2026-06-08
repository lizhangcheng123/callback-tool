"""SLS 查询服务。

复用本机 aliyunlog CLI 和已配置的 aliyun profile，避免在工具内重复实现
OAuth/STS token 刷新逻辑。
"""
import json
import os
import shutil
import subprocess
from typing import Optional

from app.models.schemas import LogEntry, LogQueryResponse, LogVerifyConfig


class SlsQueryService:
    """SLS 日志查询封装"""

    def __init__(self, cli_path: Optional[str] = None):
        self.cli_path = cli_path or os.getenv("CALLBACK_TOOL_ALIYUNLOG", "aliyunlog")

    def _resolve_cli(self) -> str:
        """查找 aliyunlog 可执行文件。"""
        candidates = [
            self.cli_path,
            os.path.expanduser("~/.local/bin/aliyunlog"),
        ]

        for candidate in candidates:
            if not candidate:
                continue
            if os.path.isabs(candidate) and os.path.exists(candidate):
                return candidate
            resolved = shutil.which(candidate)
            if resolved:
                return resolved

        raise FileNotFoundError(
            "aliyunlog CLI not found. Install aliyun-log-cli or set CALLBACK_TOOL_ALIYUNLOG."
        )

    def _parse_output(self, output: str) -> list[dict]:
        """解析 aliyunlog 输出。

        get_log_all 可能连续输出多个 JSON 数组，例如 `[...]\n[]\n`。
        标准 json.loads 无法处理这种拼接格式，所以这里逐段 raw_decode。
        """
        decoder = json.JSONDecoder()
        index = 0
        records: list[dict] = []
        text = output.strip()

        while index < len(text):
            while index < len(text) and text[index].isspace():
                index += 1
            if index >= len(text):
                break

            value, next_index = decoder.raw_decode(text, index)
            if isinstance(value, list):
                records.extend(item for item in value if isinstance(item, dict))
            elif isinstance(value, dict):
                if value.get("errorCode"):
                    raise RuntimeError(f"{value.get('errorCode')}: {value.get('errorMessage')}")
                records.append(value)
            index = next_index

        return records

    def query(self, config: LogVerifyConfig) -> LogQueryResponse:
        """执行 SLS 查询。"""
        try:
            cli = self._resolve_cli()
            cmd = [
                cli,
                "log",
                "get_log_all",
                "--project",
                config.project,
                "--logstore",
                config.logstore,
                "--from_time",
                config.from_time,
                "--to_time",
                config.to_time,
                "--query",
                config.query,
                "--reverse",
                "true",
                "--region-endpoint",
                config.endpoint,
                "--profile",
                config.profile,
                "--format-output",
                "json",
            ]

            completed = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if completed.returncode != 0:
                message = completed.stderr.strip() or completed.stdout.strip()
                return LogQueryResponse(
                    success=False,
                    message=message or f"aliyunlog exited with {completed.returncode}",
                    project=config.project,
                    logstore=config.logstore,
                    query=config.query,
                    from_time=config.from_time,
                    to_time=config.to_time,
                )

            records = self._parse_output(completed.stdout or "[]")
            logs = [
                LogEntry(
                    time=record.get("__time__"),
                    pod=record.get("__tag__:_pod_name_"),
                    path=record.get("__tag__:__path__"),
                    content=record.get("content", ""),
                    raw=record,
                )
                for record in records[: config.max_results]
            ]

            return LogQueryResponse(
                success=len(logs) > 0,
                message="matched logs found" if logs else "no matched logs",
                project=config.project,
                logstore=config.logstore,
                query=config.query,
                from_time=config.from_time,
                to_time=config.to_time,
                count=len(logs),
                logs=logs,
            )
        except Exception as exc:
            return LogQueryResponse(
                success=False,
                message=str(exc),
                project=config.project,
                logstore=config.logstore,
                query=config.query,
                from_time=config.from_time,
                to_time=config.to_time,
            )


sls_query_service = SlsQueryService()
