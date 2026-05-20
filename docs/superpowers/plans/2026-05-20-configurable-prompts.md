# Configurable Prompts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 3 条硬编码 AI 提示词提取到 `prompts.yaml`，通过 `PromptConfig` 类加载，文件缺失时自动回退到硬编码。

**Architecture:** 新增 `ebs_merger/prompt_config.py`（`PromptConfig` 类，加载 YAML 并格式化占位符）。`AIClassifier` 和 `AIGenerator` 各自实例化一个 `PromptConfig`，在构建提示词时先调用 `prompt_config.get()`，返回 `None` 则使用原有硬编码字符串作为回退。新增 `prompts.yaml` 到项目根目录，内含 3 条默认模板。

**Tech Stack:** Python 3, pyyaml, pytest

---

## File Map

| 操作 | 文件 |
|------|------|
| 新增 | `ebs_merger/prompt_config.py` |
| 新增 | `tests/__init__.py` |
| 新增 | `tests/test_prompt_config.py` |
| 新增 | `prompts.yaml` |
| 修改 | `requirements.txt` |
| 修改 | `ebs_merger/ai_classifier.py` |
| 修改 | `ebs_merger/ai_generator.py` |

---

## Task 1: 添加 pyyaml 依赖

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: 在 requirements.txt 末尾追加 pyyaml**

  将 `requirements.txt` 修改为：

  ```
  pandas>=2.0.0
  openpyxl>=3.1.0
  hypothesis>=6.0.0
  pytest>=7.0.0
  pytest-cov>=4.0.0
  requests>=2.31.0
  python-dotenv>=1.0.0
  pyyaml>=6.0
  ```

- [ ] **Step 2: 安装依赖**

  ```bash
  pip install pyyaml>=6.0
  ```

  Expected: `Successfully installed pyyaml-...`

- [ ] **Step 3: Commit**

  ```bash
  git add requirements.txt
  git commit -m "chore: add pyyaml dependency for configurable prompts"
  ```

---

## Task 2: 创建 PromptConfig（TDD）

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_prompt_config.py`
- Create: `ebs_merger/prompt_config.py`

- [ ] **Step 1: 创建 tests 目录**

  创建 `tests/__init__.py`（空文件）。

- [ ] **Step 2: 编写失败测试**

  创建 `tests/test_prompt_config.py`：

  ```python
  import pytest
  from ebs_merger.prompt_config import PromptConfig


  def test_get_returns_none_when_file_not_found():
      config = PromptConfig("nonexistent_file_xyz.yaml")
      assert config.get("any_prompt", count=1, if_info_block="x") is None


  def test_get_returns_none_when_prompt_key_missing(tmp_path):
      yaml_file = tmp_path / "prompts.yaml"
      yaml_file.write_text("other_key:\n  template: hello\n", encoding="utf-8")
      config = PromptConfig(str(yaml_file))
      assert config.get("missing_key") is None


  def test_get_formats_template(tmp_path):
      yaml_file = tmp_path / "prompts.yaml"
      yaml_file.write_text(
          "my_prompt:\n  template: 'Count={count}, Block={if_info_block}'\n",
          encoding="utf-8",
      )
      config = PromptConfig(str(yaml_file))
      result = config.get("my_prompt", count=3, if_info_block="data")
      assert result == "Count=3, Block=data"


  def test_get_returns_none_on_missing_placeholder(tmp_path):
      yaml_file = tmp_path / "prompts.yaml"
      yaml_file.write_text(
          "my_prompt:\n  template: 'Need {missing_key}'\n",
          encoding="utf-8",
      )
      config = PromptConfig(str(yaml_file))
      assert config.get("my_prompt", count=1) is None


  def test_get_returns_none_on_invalid_yaml(tmp_path):
      yaml_file = tmp_path / "prompts.yaml"
      yaml_file.write_text("key:\n  bad: : yaml:\n", encoding="utf-8")
      config = PromptConfig(str(yaml_file))
      assert config.get("key") is None
  ```

- [ ] **Step 3: 运行测试，确认失败**

  ```bash
  cd d:/Users/PC/Projects/IFmerge && python -m pytest tests/test_prompt_config.py -v
  ```

  Expected: `ModuleNotFoundError: No module named 'ebs_merger.prompt_config'`

- [ ] **Step 4: 实现 PromptConfig**

  创建 `ebs_merger/prompt_config.py`：

  ```python
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
  ```

- [ ] **Step 5: 运行测试，确认全部通过**

  ```bash
  python -m pytest tests/test_prompt_config.py -v
  ```

  Expected: `5 passed`

- [ ] **Step 6: Commit**

  ```bash
  git add tests/__init__.py tests/test_prompt_config.py ebs_merger/prompt_config.py
  git commit -m "feat: add PromptConfig class with YAML-based prompt loading"
  ```

---

## Task 3: 集成到 AIClassifier

**Files:**
- Modify: `ebs_merger/ai_classifier.py:1-22` (imports + `__init__`)
- Modify: `ebs_merger/ai_classifier.py:54-80` (prompt building in `classify_interfaces`)

- [ ] **Step 1: 在 ai_classifier.py 顶部添加 import**

  在 `from ebs_merger.ai_generator import AIGenerator` 这行后面添加：

  ```python
  from ebs_merger.prompt_config import PromptConfig
  ```

- [ ] **Step 2: 在 AIClassifier.__init__ 中实例化 PromptConfig**

  将 `__init__` 方法：

  ```python
      def __init__(self, ai_generator: AIGenerator = None):
          """初始化分类器
          
          参数:
              ai_generator: AI生成器实例（可选）
          """
          self.ai_generator = ai_generator or AIGenerator()
  ```

  改为：

  ```python
      def __init__(self, ai_generator: AIGenerator = None):
          """初始化分类器
          
          参数:
              ai_generator: AI生成器实例（可选）
          """
          self.ai_generator = ai_generator or AIGenerator()
          self._prompt_config = PromptConfig()
  ```

- [ ] **Step 3: 重构 classify_interfaces 中的提示词构建**

  将 `classify_interfaces` 方法中的提示词构建部分（当前 54–80 行）：

  ```python
          # プロンプトの構築
          prompt = f"""以下の{len(if_info_list)}個の日本語インターフェース（IF）を分析し、SAPモジュールと業務シナリオに基づいてグループ化してください。

インターフェース情報：
"""
          for idx, info in enumerate(if_info_list, 1):
              prompt += f"""
{idx}. IF名: {info['if_name']}
   文書管理番号: {info['doc_number']}
   関連テーブル: {', '.join(info['tables'])}
   項目総数: {info['item_count']}
   サンプル項目: {', '.join(info['items'][:5])}
"""
          
          prompt += """
以下の観点でインターフェースをグループ化してください：
1. SAPモジュール（例：SD、MM、PP、WM、FI、CO、HRなど）
2. 業務シナリオ（例：受注処理、在庫管理、出荷管理、購買管理など）

グループ化要件：
- 各インターフェースは1つのグループにのみ属する
- SAPモジュールと業務シナリオを別々のフィールドで指定
- **モジュール名は必ず単一のSAPモジュールコードのみを指定すること（例：「SD」「MM」「WM」）。複数モジュールの組み合わせ（例：「SD/WM」「SD_WM」）は絶対に使用しないこと**
- インターフェースが複数モジュールにまたがる場合は、最も主要なモジュールを1つ選択すること
- 明確に分類できない場合は、module: "その他"、scenario: "未分類"を使用

classify_interfacesツールを使用して分類結果を返してください。"""
  ```

  替换为：

  ```python
          # if_info_block の構築（設定テンプレートとハードコードの両方で共通）
          if_info_lines = []
          for idx, info in enumerate(if_info_list, 1):
              if_info_lines.append(
                  f"\n{idx}. IF名: {info['if_name']}\n"
                  f"   文書管理番号: {info['doc_number']}\n"
                  f"   関連テーブル: {', '.join(info['tables'])}\n"
                  f"   項目総数: {info['item_count']}\n"
                  f"   サンプル項目: {', '.join(info['items'][:5])}\n"
              )
          if_info_block = "".join(if_info_lines)

          prompt = self._prompt_config.get(
              "classify_interfaces",
              count=len(if_info_list),
              if_info_block=if_info_block,
          )
          if prompt is None:
              prompt = (
                  f"以下の{len(if_info_list)}個の日本語インターフェース（IF）を分析し、"
                  "SAPモジュールと業務シナリオに基づいてグループ化してください。\n\n"
                  "インターフェース情報：\n"
                  + if_info_block
                  + "\n以下の観点でインターフェースをグループ化してください：\n"
                  "1. SAPモジュール（例：SD、MM、PP、WM、FI、CO、HRなど）\n"
                  "2. 業務シナリオ（例：受注処理、在庫管理、出荷管理、購買管理など）\n\n"
                  "グループ化要件：\n"
                  "- 各インターフェースは1つのグループにのみ属する\n"
                  "- SAPモジュールと業務シナリオを別々のフィールドで指定\n"
                  "- **モジュール名は必ず単一のSAPモジュールコードのみを指定すること"
                  "（例：「SD」「MM」「WM」）。複数モジュールの組み合わせ（例：「SD/WM」「SD_WM」）は絶対に使用しないこと**\n"
                  "- インターフェースが複数モジュールにまたがる場合は、最も主要なモジュールを1つ選択すること\n"
                  "- 明確に分類できない場合は、module: \"その他\"、scenario: \"未分類\"を使用\n\n"
                  "classify_interfacesツールを使用して分類結果を返してください。"
              )
  ```

- [ ] **Step 4: 运行全部测试，确认无回归**

  ```bash
  python -m pytest tests/ -v
  ```

  Expected: `5 passed`

- [ ] **Step 5: Commit**

  ```bash
  git add ebs_merger/ai_classifier.py
  git commit -m "feat: integrate PromptConfig into AIClassifier"
  ```

---

## Task 4: 集成到 AIGenerator.generate_all_if_info

**Files:**
- Modify: `ebs_merger/ai_generator.py:1-17` (import)
- Modify: `ebs_merger/ai_generator.py` (`__init__` 末尾)
- Modify: `ebs_merger/ai_generator.py:263-291` (prompt building in `generate_all_if_info`)

- [ ] **Step 1: 在 ai_generator.py 顶部添加 import**

  在 `from ebs_merger.if_grouper import IFInfo` 这行后面添加：

  ```python
  from ebs_merger.prompt_config import PromptConfig
  ```

- [ ] **Step 2: 在 AIGenerator.__init__ 末尾实例化 PromptConfig**

  在 `__init__` 方法中，`if not self.deployment_id:` 的 `raise ValueError(...)` 块之后添加：

  ```python
          self._prompt_config = PromptConfig()
  ```

  （即在 `__init__` 最后一行）

- [ ] **Step 3: 重构 generate_all_if_info 中的提示词构建**

  将 `generate_all_if_info` 中当前的提示词构建部分（第 263–291 行）：

  ```python
          # プロンプトの構築
          prompt = f"""以下の{len(if_info_list)}個の日本語インターフェース（IF）の情報を分析し、各インターフェースの概要を生成し、代表項目名を選択してください。

インターフェース情報：
"""
          for idx, info in enumerate(if_info_list, 1):
              # 限制显示的项目数量，避免提示词过长
              sample_items = info['items'][:20]  # 最多显示20个项目作为参考
              prompt += f"""
{idx}. IF名: {info['if_name']}
   文書管理番号: {info['doc_number']}
   関連テーブル: {', '.join(info['tables'])}
   項目総数: {info['item_count']}
   選択すべき代表項目数: {info['top_20_percent_count']}個（項目総数の約20%）
   参考項目（最初の{len(sample_items)}個）: {', '.join(sample_items)}
"""
          
          prompt += """
提供されたツールを使用して、各インターフェースの情報を生成してください。要件：

1. IF概要：日本語で簡潔な機能説明を生成（30-50文字）、インターフェースの主な機能と用途を要約

2. 代表項目名：各インターフェースの項目総数の約20%に相当する代表的な項目名を選択してください。選択基準：
   ① SAP系統における重要性：項目名がSAPシステムで一般的に使用されるキー項目（例：伝票番号、品目コード、顧客コード、注文番号、会計年度、会社コード、プラントコード、在庫組織、勘定科目など）であるかを優先的に考慮
   ② 業務シナリオとの関連性：IF名から推測される業務シナリオにおいて、最も代表的で重要な項目を選択（例：「出荷指示」というIF名の場合、出荷関連の項目を優先）
   
   選択した項目名をカンマで区切って返してください（例：項目総数が50個の場合、約10個の項目名を選択）

generate_all_if_infoツールを呼び出して、すべてのインターフェースの情報を一度に返してください。"""
  ```

  替换为：

  ```python
          # if_info_block の構築
          if_info_lines = []
          for idx, info in enumerate(if_info_list, 1):
              sample_items = info['items'][:20]
              if_info_lines.append(
                  f"\n{idx}. IF名: {info['if_name']}\n"
                  f"   文書管理番号: {info['doc_number']}\n"
                  f"   関連テーブル: {', '.join(info['tables'])}\n"
                  f"   項目総数: {info['item_count']}\n"
                  f"   選択すべき代表項目数: {info['top_20_percent_count']}個（項目総数の約20%）\n"
                  f"   参考項目（最初の{len(sample_items)}個）: {', '.join(sample_items)}\n"
              )
          if_info_block = "".join(if_info_lines)

          prompt = self._prompt_config.get(
              "generate_all_if_info",
              count=len(if_info_list),
              if_info_block=if_info_block,
          )
          if prompt is None:
              prompt = (
                  f"以下の{len(if_info_list)}個の日本語インターフェース（IF）の情報を分析し、"
                  "各インターフェースの概要を生成し、代表項目名を選択してください。\n\n"
                  "インターフェース情報：\n"
                  + if_info_block
                  + "\n提供されたツールを使用して、各インターフェースの情報を生成してください。要件：\n\n"
                  "1. IF概要：日本語で簡潔な機能説明を生成（30-50文字）、インターフェースの主な機能と用途を要約\n\n"
                  "2. 代表項目名：各インターフェースの項目総数の約20%に相当する代表的な項目名を選択してください。選択基準：\n"
                  "   ① SAP系統における重要性：項目名がSAPシステムで一般的に使用されるキー項目"
                  "（例：伝票番号、品目コード、顧客コード、注文番号、会計年度、会社コード、プラントコード、在庫組織、勘定科目など）であるかを優先的に考慮\n"
                  "   ② 業務シナリオとの関連性：IF名から推測される業務シナリオにおいて、最も代表的で重要な項目を選択"
                  "（例：「出荷指示」というIF名の場合、出荷関連の項目を優先）\n\n"
                  "   選択した項目名をカンマで区切って返してください（例：項目総数が50個の場合、約10個の項目名を選択）\n\n"
                  "generate_all_if_infoツールを呼び出して、すべてのインターフェースの情報を一度に返してください。"
              )
  ```

- [ ] **Step 4: 运行全部测试，确认无回归**

  ```bash
  python -m pytest tests/ -v
  ```

  Expected: `5 passed`

- [ ] **Step 5: Commit**

  ```bash
  git add ebs_merger/ai_generator.py
  git commit -m "feat: integrate PromptConfig into AIGenerator.generate_all_if_info"
  ```

---

## Task 5: 集成到 AIGenerator.generate_merged_if_name

**Files:**
- Modify: `ebs_merger/ai_generator.py:393-409` (prompt building in `generate_merged_if_name`)

- [ ] **Step 1: 重构 generate_merged_if_name 中的提示词构建**

  将 `generate_merged_if_name` 中当前的提示词构建部分（第 393–409 行）：

  ```python
          # すべてのIFの情報を収集
          if_info_list = []
          for if_name in group_members:
              if_data = input_df[input_df['IF名'] == if_name]
              tables = if_data['EBSテーブル名'].unique().tolist()
              if_info_list.append(f"- {if_name}（関連テーブル：{', '.join(tables[:3])}）")
          
          prompt = f"""以下のマージ対象インターフェース情報に基づいて、新しい簡潔な日本語インターフェース名を生成してください（20-40文字）：

{chr(10).join(if_info_list)}

要件：
1. 名前はすべてのインターフェースの共通機能を要約すること
2. 日本語を使用すること
3. 専門的かつ簡潔であること

generate_merged_nameツールを使用して新しいインターフェース名を返してください。"""
  ```

  替换为：

  ```python
          # すべてのIFの情報を収集
          if_info_lines = []
          for if_name in group_members:
              if_data = input_df[input_df['IF名'] == if_name]
              tables = if_data['EBSテーブル名'].unique().tolist()
              if_info_lines.append(f"- {if_name}（関連テーブル：{', '.join(tables[:3])}）")
          if_info_block = "\n".join(if_info_lines)

          prompt = self._prompt_config.get(
              "generate_merged_if_name",
              if_info_block=if_info_block,
          )
          if prompt is None:
              prompt = (
                  "以下のマージ対象インターフェース情報に基づいて、"
                  "新しい簡潔な日本語インターフェース名を生成してください（20-40文字）：\n\n"
                  + if_info_block
                  + "\n\n要件：\n"
                  "1. 名前はすべてのインターフェースの共通機能を要約すること\n"
                  "2. 日本語を使用すること\n"
                  "3. 専門的かつ簡潔であること\n\n"
                  "generate_merged_nameツールを使用して新しいインターフェース名を返してください。"
              )
  ```

- [ ] **Step 2: 运行全部测试，确认无回归**

  ```bash
  python -m pytest tests/ -v
  ```

  Expected: `5 passed`

- [ ] **Step 3: Commit**

  ```bash
  git add ebs_merger/ai_generator.py
  git commit -m "feat: integrate PromptConfig into AIGenerator.generate_merged_if_name"
  ```

---

## Task 6: 创建 prompts.yaml 默认模板

**Files:**
- Create: `prompts.yaml`

- [ ] **Step 1: 创建 prompts.yaml**

  在项目根目录（与 `.env` 并列）创建 `prompts.yaml`：

  ```yaml
  # prompts.yaml — AI 提示词配置
  # 修改此文件中的模板以自定义 AI 提示词，无需修改源代码。
  # 删除某个条目后，程序将使用内置默认提示词（行为不变）。
  # 修改生效需重启程序。

  classify_interfaces:
    # 可用占位符:
    #   {count}         - 待分类的 IF 总数（整数）
    #   {if_info_block} - 每个 IF 的编号、名称、文书番号、关联表、项目数、サンプル项目（自动生成）
    template: |
      以下の{count}個の日本語インターフェース（IF）を分析し、SAPモジュールと業務シナリオに基づいてグループ化してください。

      インターフェース情報：
      {if_info_block}
      以下の観点でインターフェースをグループ化してください：
      1. SAPモジュール（例：SD、MM、PP、WM、FI、CO、HRなど）
      2. 業務シナリオ（例：受注処理、在庫管理、出荷管理、購買管理など）

      グループ化要件：
      - 各インターフェースは1つのグループにのみ属する
      - SAPモジュールと業務シナリオを別々のフィールドで指定
      - **モジュール名は必ず単一のSAPモジュールコードのみを指定すること（例：「SD」「MM」「WM」）。複数モジュールの組み合わせ（例：「SD/WM」「SD_WM」）は絶対に使用しないこと**
      - インターフェースが複数モジュールにまたがる場合は、最も主要なモジュールを1つ選択すること
      - 明確に分類できない場合は、module: "その他"、scenario: "未分類"を使用

      classify_interfacesツールを使用して分類結果を返してください。

  generate_all_if_info:
    # 可用占位符:
    #   {count}         - IF 总数（整数）
    #   {if_info_block} - 每个 IF 的编号、名称、文书番号、关联表、项目数、代表项目数、参考项目列表（自动生成）
    template: |
      以下の{count}個の日本語インターフェース（IF）の情報を分析し、各インターフェースの概要を生成し、代表項目名を選択してください。

      インターフェース情報：
      {if_info_block}
      提供されたツールを使用して、各インターフェースの情報を生成してください。要件：

      1. IF概要：日本語で簡潔な機能説明を生成（30-50文字）、インターフェースの主な機能と用途を要約

      2. 代表項目名：各インターフェースの項目総数の約20%に相当する代表的な項目名を選択してください。選択基準：
         ① SAP系統における重要性：項目名がSAPシステムで一般的に使用されるキー項目（例：伝票番号、品目コード、顧客コード、注文番号、会計年度、会社コード、プラントコード、在庫組織、勘定科目など）であるかを優先的に考慮
         ② 業務シナリオとの関連性：IF名から推測される業務シナリオにおいて、最も代表的で重要な項目を選択（例：「出荷指示」というIF名の場合、出荷関連の項目を優先）

         選択した項目名をカンマで区切って返してください（例：項目総数が50個の場合、約10個の項目名を選択）

      generate_all_if_infoツールを呼び出して、すべてのインターフェースの情報を一度に返してください。

  generate_merged_if_name:
    # 可用占位符:
    #   {if_info_block} - 待合并的 IF 名称及关联表列表，格式为 "- IF名（関連テーブル：...）"（自动生成）
    template: |
      以下のマージ対象インターフェース情報に基づいて、新しい簡潔な日本語インターフェース名を生成してください（20-40文字）：

      {if_info_block}

      要件：
      1. 名前はすべてのインターフェースの共通機能を要約すること
      2. 日本語を使用すること
      3. 専門的かつ簡潔であること

      generate_merged_nameツールを使用して新しいインターフェース名を返してください。
  ```

- [ ] **Step 2: 验证 YAML 文件可正确被 PromptConfig 加载**

  在项目根目录运行：

  ```bash
  python -c "
  from ebs_merger.prompt_config import PromptConfig
  cfg = PromptConfig('prompts.yaml')
  result = cfg.get('classify_interfaces', count=3, if_info_block='TEST_BLOCK')
  assert result is not None, 'テンプレートの読み込みに失敗'
  assert 'TEST_BLOCK' in result, 'if_info_block が展開されていない'
  assert '3' in result, 'count が展開されていない'
  print('OK: prompts.yaml の読み込みと展開に成功')
  "
  ```

  Expected: `OK: prompts.yaml の読み込みと展開に成功`

- [ ] **Step 3: 运行全部测试，确认无回归**

  ```bash
  python -m pytest tests/ -v
  ```

  Expected: `5 passed`

- [ ] **Step 4: Commit**

  ```bash
  git add prompts.yaml
  git commit -m "feat: add prompts.yaml with default configurable prompt templates"
  ```

---

## 验收检查

全部 Task 完成后运行：

```bash
python -m pytest tests/ -v
```

Expected: `5 passed, 0 failed`

---

## 使用说明（供参考，不属于实现步骤）

用户编辑 `prompts.yaml` 即可修改提示词，例如将 `classify_interfaces` 中的 SAP 模块列表扩展为包含 `PS`、`PM` 等，保存后重启程序生效。删除某个条目则该提示词回退到内置默认。
