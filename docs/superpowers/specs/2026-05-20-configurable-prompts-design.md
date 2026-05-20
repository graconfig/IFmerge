# 提示词可配置化设计

**日期:** 2026-05-20  
**状态:** 待实现

## 背景

项目中有 3 条 AI 提示词硬编码在 Python 文件里：

| 提示词 | 文件 | 行号 |
|--------|------|------|
| `classify_interfaces` | `ebs_merger/ai_classifier.py` | 55–80 |
| `generate_all_if_info` | `ebs_merger/ai_generator.py` | 264–291 |
| `generate_merged_if_name` | `ebs_merger/ai_generator.py` | 400–409 |

用户需要在不修改源代码的情况下调整这些提示词（例如修改 SAP 模块分类标准、调整概要生成要求等）。

## 目标

- 将全部 3 条提示词提取到项目根目录的 `prompts.yaml` 文件中
- 配置文件不存在时，自动回退到代码中的硬编码提示词，行为不变
- 不引入任何新的依赖（PyYAML 已在项目中使用）

## 方案：单一 YAML + 占位符模板

### 配置文件结构

文件位置：`prompts.yaml`（项目根目录，与 `.env` 并列）

```yaml
# prompts.yaml
# 修改此文件中的模板以自定义 AI 提示词。
# 删除某个条目后，程序将使用内置默认提示词。

classify_interfaces:
  # 可用占位符:
  #   {count}         - 待分类的 IF 总数
  #   {if_info_block} - 每个 IF 的名称、文书番号、关联表、项目数等信息（自动生成）
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
  #   {count}         - IF 总数
  #   {if_info_block} - 每个 IF 的名称、文书番号、关联表、项目数、代表项目数、参考项目列表（自动生成）
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
  #   {if_info_block} - 待合并的 IF 名称及关联表列表（自动生成）
  template: |
    以下のマージ対象インターフェース情報に基づいて、新しい簡潔な日本語インターフェース名を生成してください（20-40文字）：

    {if_info_block}
    要件：
    1. 名前はすべてのインターフェースの共通機能を要約すること
    2. 日本語を使用すること
    3. 専門的かつ簡潔であること

    generate_merged_nameツールを使用して新しいインターフェース名を返してください。
```

### 新增组件：`ebs_merger/prompt_config.py`

```python
class PromptConfig:
    def __init__(self, path: str = "prompts.yaml"):
        # 尝试加载 YAML；文件不存在或解析失败时 _templates = {}
        
    def get(self, name: str, **kwargs) -> str | None:
        # 从 _templates[name]['template'] 取模板
        # 用 kwargs 格式化（str.format_map）
        # name 不存在 → 返回 None（调用方负责回退到硬编码）
        # 格式化失败（占位符缺失）→ 记录警告，返回 None
```

约 30 行，需添加 `pyyaml>=6.0` 到 `requirements.txt`。

### 改动范围

| 文件 | 改动说明 |
|------|---------|
| `ebs_merger/prompt_config.py` | **新增**，`PromptConfig` 类 |
| `ebs_merger/ai_classifier.py` | `classify_interfaces`：抽取 `if_info_block` 字符串构建逻辑，调用 `prompt_config.get()`，None 则用原硬编码 |
| `ebs_merger/ai_generator.py` | `generate_all_if_info` 和 `generate_merged_if_name` 同上 |
| `prompts.yaml` | **新增**，含全部 3 条默认模板 |
| `requirements.txt` | 添加 `pyyaml>=6.0` |

**不改动**：CLI、toolSpec 工具定义、`_call_claude_with_tools`、`.env` 结构、其他模块。

### 回退行为

```
prompts.yaml 存在且含该条目 → 使用 YAML 模板
prompts.yaml 存在但不含该条目 → 使用硬编码（静默）
prompts.yaml 不存在 → 所有提示词使用硬编码（静默）
YAML 模板占位符格式化失败 → 记录警告，使用硬编码
```

### PromptConfig 初始化时机

`AIClassifier.__init__` 和 `AIGenerator.__init__` 各自实例化一个 `PromptConfig`，从当前工作目录查找 `prompts.yaml`（与程序启动目录一致，即项目根）。

## 不在范围内

- UI 界面或交互式编辑
- 运行时热重载（修改后需重启程序）
- 工具定义（toolSpec）的可配置化
- `inferenceConfig`（temperature、maxTokens）的可配置化
