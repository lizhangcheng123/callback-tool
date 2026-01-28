"""YAML 场景加载器"""
import os
from typing import Optional
import yaml

from app.models.schemas import Scene, Scenario, SceneStep, ScenesConfig


class SceneLoader:
    """场景配置加载器"""

    def __init__(self):
        self._config: Optional[ScenesConfig] = None
        self._file_path: str = ""

    def load(self, file_path: str = "scenes.yaml") -> ScenesConfig:
        """加载场景配置文件

        Args:
            file_path: YAML 文件路径

        Returns:
            场景配置对象

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式错误
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"场景配置文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        self._file_path = file_path
        self._config = self._parse_config(data)
        return self._config

    def reload(self) -> ScenesConfig:
        """重新加载配置文件

        Returns:
            场景配置对象
        """
        if not self._file_path:
            raise RuntimeError("尚未加载过配置文件，请先调用 load()")
        return self.load(self._file_path)

    def _parse_config(self, data: dict) -> ScenesConfig:
        """解析配置数据

        Args:
            data: YAML 解析后的字典

        Returns:
            场景配置对象
        """
        # 解析环境配置
        environments = data.get("environments", {})

        # 解析场景
        scenes_data = data.get("scenes", {})
        scenes = {}
        for scene_id, scene_data in scenes_data.items():
            scenes[scene_id] = Scene(
                id=scene_id,
                name=scene_data.get("name", scene_id),
                description=scene_data.get("description", ""),
                url=scene_data.get("url", ""),
                method=scene_data.get("method", "POST").upper(),
                headers=scene_data.get("headers", {}),
                body=scene_data.get("body", ""),
                defaults=scene_data.get("defaults", {}),
            )

        # 解析批量场景
        scenarios_data = data.get("scenarios", {})
        scenarios = {}
        for scenario_id, scenario_data in scenarios_data.items():
            steps = []
            for step_data in scenario_data.get("steps", []):
                steps.append(SceneStep(
                    scene=step_data.get("scene", ""),
                    delay_after=step_data.get("delay_after", 0.0),
                ))
            scenarios[scenario_id] = Scenario(
                id=scenario_id,
                name=scenario_data.get("name", scenario_id),
                description=scenario_data.get("description", ""),
                steps=steps,
            )

        return ScenesConfig(
            environments=environments,
            scenes=scenes,
            scenarios=scenarios,
        )

    @property
    def config(self) -> Optional[ScenesConfig]:
        """获取当前配置"""
        return self._config

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """获取指定场景

        Args:
            scene_id: 场景 ID

        Returns:
            场景对象，不存在返回 None
        """
        if not self._config:
            return None
        return self._config.scenes.get(scene_id)

    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """获取指定批量场景

        Args:
            scenario_id: 批量场景 ID

        Returns:
            批量场景对象，不存在返回 None
        """
        if not self._config:
            return None
        return self._config.scenarios.get(scenario_id)

    def get_env_variables(self, env: str) -> dict:
        """获取指定环境的变量

        Args:
            env: 环境名称

        Returns:
            环境变量字典
        """
        if not self._config:
            return {}
        return self._config.environments.get(env, {})

    def list_scenes(self) -> list[Scene]:
        """列出所有场景"""
        if not self._config:
            return []
        return list(self._config.scenes.values())

    def list_scenarios(self) -> list[Scenario]:
        """列出所有批量场景"""
        if not self._config:
            return []
        return list(self._config.scenarios.values())


# 全局实例
scene_loader = SceneLoader()
