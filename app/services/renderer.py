"""简单模板渲染器 - 替代 Jinja2"""
import re
from datetime import datetime
from typing import Any


class Renderer:
    """基于正则的简单模板渲染器

    支持:
    - {{var}} - 变量替换
    - {{var|default:value}} - 带默认值的变量
    - {{_now}} - 当前时间 ISO 格式
    - {{_timestamp}} - Unix 时间戳 (秒)
    - {{_timestamp_ms}} - Unix 时间戳 (毫秒)
    """

    # 匹配 {{var}} 或 {{var|default:value}}
    PATTERN = re.compile(r'\{\{(\w+)(?:\|default:([^}]*))?\}\}')

    def _get_builtins(self) -> dict[str, Any]:
        """获取内置变量"""
        now = datetime.now()
        return {
            "_now": now.isoformat(),
            "_timestamp": int(now.timestamp()),
            "_timestamp_ms": int(now.timestamp() * 1000),
        }

    def render(self, template: str, variables: dict[str, Any]) -> str:
        """渲染模板字符串

        Args:
            template: 模板字符串
            variables: 变量字典

        Returns:
            渲染后的字符串
        """
        if not template:
            return ""

        # 合并内置变量和用户变量
        context = {**self._get_builtins(), **variables}

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            default_value = match.group(2)

            if var_name in context:
                value = context[var_name]
                # 保持数值类型
                if isinstance(value, (int, float)):
                    return str(value)
                return str(value)
            elif default_value is not None:
                return default_value
            else:
                # 未找到变量且无默认值，保留原样
                return match.group(0)

        return self.PATTERN.sub(replacer, template)

    def render_dict(self, data: dict[str, str], variables: dict[str, Any]) -> dict[str, str]:
        """渲染字典中的所有值

        Args:
            data: 待渲染的字典
            variables: 变量字典

        Returns:
            渲染后的字典
        """
        if not data:
            return {}
        return {k: self.render(v, variables) for k, v in data.items()}


# 全局实例
renderer = Renderer()
