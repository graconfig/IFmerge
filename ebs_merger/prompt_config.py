"""提示词配置模块"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml


class PromptConfig:
    """从 YAML 文件加载 AI 提示词模板，支持占位符格式化。

    文件不存在或条目缺失时，get() 返回 None，由调用方回退到硬编码。
    """

    def __init__(self, path: str = "prompts.yaml") -> None:
        self._templates: dict = {}
        config_path = Path(path)
        if not config_path.exists():
            return
        try:
            with open(config_path, encoding="utf-8") as f:
                self._templates = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"警告：{path} の読み込みに失敗しました: {e}")

    def get(self, name: str, **kwargs) -> Optional[str]:
        """指定プロンプトをテンプレートから取得してフォーマット。

        Args:
            name: プロンプト名（classify_interfaces など）
            **kwargs: テンプレート内の占位符に渡す値

        Returns:
            フォーマット済み文字列、またはテンプレートが無い場合は None
        """
        entry = self._templates.get(name)
        if not entry:
            return None
        template = entry.get("template")
        if not template:
            return None
        try:
            return template.format_map(kwargs)
        except KeyError as e:
            print(f"警告：プロンプト '{name}' のフォーマットに失敗しました（{e} が不足）")
            return None
