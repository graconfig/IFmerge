"""提示词配置模块"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from ebs_merger.runtime import resource_path


class PromptConfig:
    """从 YAML 文件加载 AI 提示词模板，支持占位符格式化。

    文件不存在或条目缺失时，get() 返回 None，由调用方回退到硬编码。
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self._templates: dict = {}
        # path 为 None 时解析打包/开发态下的默认 prompts.yaml(支持 PyInstaller)。
        config_path = Path(path) if path is not None else resource_path("prompts.yaml")
        if not config_path.exists():
            return
        try:
            with open(config_path, encoding="utf-8") as f:
                self._templates = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"警告：{config_path} の読み込みに失敗しました: {e}")

    def get(self, name: str, **kwargs) -> Optional[str]:
        """从模板中获取指定提示词并格式化。

        参数:
            name: 提示词名称（如 classify_interfaces）
            **kwargs: 传递给模板中占位符的值

        返回:
            格式化后的字符串，若模板不存在则返回 None
        """
        entry = self._templates.get(name)
        if not isinstance(entry, dict):
            return None
        template = entry.get("template")
        if not template:
            return None
        try:
            return template.format_map(kwargs)
        except Exception as e:
            print(f"警告：プロンプト '{name}' のフォーマットに失敗しました: {e}")
            return None
