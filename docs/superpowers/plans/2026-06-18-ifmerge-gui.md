# IFmerge 桌面 GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为本地 CLI 工具 IFmerge 增加一个 CustomTkinter 桌面 GUI，外观/交互对齐参考工程 `ifmerge-gui`，后台进程内直接调用 `ebs_merger`。

**Architecture:** 新建 `ifmerge_gui/` 包（结构镜像参考工程）。左侧导航 + 解析/合并两页，后台 `threading.Thread` 通过 `widget.after()` 把进度/日志回调主线程。两页各自的 Task 直接调用 `ebs_merger` 组件（DataLoader/IFGrouper/AIClassifier/AIGenerator/SimilarityCalculator/MergeGrouper/ResultGenerator/TemplateFiller/MatrixExporter）完成编排——不修改 `ebs_merger` 任何代码。

**Tech Stack:** Python 3.10+，CustomTkinter ≥ 5.2，pandas/openpyxl（沿用 ebs_merger），python-dotenv，SAP AI Core（经 `ebs_merger.ai_generator.AIGenerator`）。

## Global Constraints

- 不修改 `ebs_merger/` 下任何文件（用户已确认：GUI 内重新编排）。
- 新增 GUI 全部代码位于新包 `ifmerge_gui/`，放在仓库根 `/data/HuangCX/IFmerge/`。
- 默认界面语言 = `zh`；内置 zh/ja/en，可在设定中切换并持久化到 `~/.ifmerge/config.json`。
- 配置读写仓库根 `.env`（固定路径，基于文件位置 `parents[2]`，与启动目录无关）。沿用 IFmerge 现有键名：`INPUT_DIR / OUTPUT_DIR / SIMILARITY_THRESHOLD / SIMILARITY_MODE / AICORE_AUTH_URL / AICORE_CLIENT_ID / AICORE_CLIENT_SECRET / AICORE_BASE_URL / AICORE_RESOURCE_GROUP / AICORE_DEPLOYMENT_ID / LOG_LEVEL`；新增键 `MERGED_TEMPLATE_PATH`。
- 进度回调签名固定：`on_progress(percent: int, phase: str)`、`on_log(msg: str)`、`on_done(result)`、`on_failed(exc: Exception)`。所有回调经 `self.after(0, ...)` 调度回主线程。
- UI 字符串一律走 `i18n` 的 `t(key, **kwargs)`，禁止硬编码可见文案。
- 涉及 Tk 的模块不写自动化测试（环境无显示）；测试只覆盖纯逻辑（Settings / i18n / fs / ai_factory）+ 一个导入冒烟测试。
- Excel 输入只认 `.xlsx`（与 `DataLoader` 用 openpyxl 读取一致），递归扫描，跳过 `~$` 临时锁文件。
- 提交粒度：每个 Task 末尾提交一次。

---

## File Structure

```
IFmerge/
├── ebs_merger/                         # 不改
├── ifmerge_gui/
│   ├── __init__.py                     # Task 1
│   ├── __main__.py                     # Task 8
│   ├── config/
│   │   ├── __init__.py                 # Task 1
│   │   └── settings.py                 # Task 1
│   ├── utils/
│   │   ├── __init__.py                 # Task 1
│   │   └── logger.py                   # Task 1
│   ├── i18n/
│   │   ├── __init__.py                 # Task 2
│   │   └── locales/{zh,ja,en}.json     # Task 2
│   ├── core/
│   │   ├── __init__.py                 # Task 5
│   │   └── ai_factory.py               # Task 5
│   └── ui/
│       ├── __init__.py                 # Task 4
│       ├── utils/
│       │   ├── __init__.py             # Task 3
│       │   └── fs.py                   # Task 3
│       ├── widgets/
│       │   ├── __init__.py             # Task 4
│       │   ├── file_input.py           # Task 4
│       │   ├── file_output.py          # Task 4
│       │   └── progress_log.py         # Task 4
│       ├── pages/
│       │   ├── __init__.py             # Task 4
│       │   ├── base_page.py            # Task 4
│       │   ├── analyze_page.py         # Task 5
│       │   └── merge_page.py           # Task 6
│       ├── tasks/
│       │   ├── __init__.py             # Task 5
│       │   ├── analyze_task.py         # Task 5
│       │   └── merge_task.py           # Task 6
│       ├── dialogs/
│       │   ├── __init__.py             # Task 7
│       │   ├── settings_dialog.py      # Task 7
│       │   └── log_viewer.py           # Task 7
│       └── app.py                      # Task 8
├── main.py                             # Task 8
├── requirements.txt                    # Task 1 (modify)
└── tests/
    ├── test_gui_settings.py            # Task 1
    ├── test_gui_i18n.py                # Task 2
    ├── test_gui_fs.py                  # Task 3
    ├── test_gui_ai_factory.py          # Task 5
    └── test_gui_imports.py             # Task 8
```

---

### Task 1: 脚手架 + 依赖 + 日志 + Settings

**Files:**
- Create: `ifmerge_gui/__init__.py`, `ifmerge_gui/config/__init__.py`, `ifmerge_gui/config/settings.py`, `ifmerge_gui/utils/__init__.py`, `ifmerge_gui/utils/logger.py`
- Modify: `requirements.txt`
- Test: `tests/test_gui_settings.py`

**Interfaces:**
- Produces: `ifmerge_gui.config.settings.Settings` dataclass with fields `input_dir, output_dir, merged_template_path, default_threshold, default_mode, aicore_auth_url, aicore_client_id, aicore_client_secret, aicore_base_url, aicore_resource_group, aicore_deployment_id, aicore_model_name, log_level`; classmethod `Settings.load() -> Settings`; method `Settings.save() -> str`.
- Produces: `ifmerge_gui.utils.logger.setup_logger(level: str = "INFO", log_file: str = "output/ifmerge_gui.log") -> logging.Logger`.

- [ ] **Step 1: 创建空包标记文件**

Create `ifmerge_gui/__init__.py`, `ifmerge_gui/config/__init__.py`, `ifmerge_gui/utils/__init__.py` — each containing exactly:

```python
```
(empty file)

- [ ] **Step 2: 写 logger**

Create `ifmerge_gui/utils/logger.py`:

```python
"""日志器封装。控制台 + 文件双输出。"""

import logging
import sys
from pathlib import Path


def setup_logger(level: str = "INFO", log_file: str = "output/ifmerge_gui.log"):
    """初始化全局 logger（root = 'ifmerge_gui'），重复调用安全。"""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")

    root = logging.getLogger("ifmerge_gui")
    root.setLevel(level)
    for h in list(root.handlers):
        root.removeHandler(h)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    root.addHandler(sh)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)
    root.addHandler(fh)

    return root
```

- [ ] **Step 3: 写失败测试**

Create `tests/test_gui_settings.py`:

```python
import importlib
from pathlib import Path

import ifmerge_gui.config.settings as settings_mod
from ifmerge_gui.config.settings import Settings


def test_defaults():
    s = Settings()
    assert s.input_dir == "input"
    assert s.output_dir == "output"
    assert s.default_threshold == 0.8
    assert s.default_mode == "max"
    assert s.merged_template_path == "template/IF_Template.xlsm"
    assert s.aicore_resource_group == "default"


def test_save_load_roundtrip(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    monkeypatch.setattr(settings_mod, "_ENV_PATH", env)
    s = Settings(
        output_dir="out2", default_threshold=0.9, default_mode="avg",
        aicore_client_id="cid", aicore_deployment_id="dep1",
    )
    path = s.save()
    assert Path(path) == env
    loaded = Settings.load()
    assert loaded.output_dir == "out2"
    assert loaded.default_threshold == 0.9
    assert loaded.default_mode == "avg"
    assert loaded.aicore_client_id == "cid"
    assert loaded.aicore_deployment_id == "dep1"
```

- [ ] **Step 4: 运行测试，确认失败**

Run: `python -m pytest tests/test_gui_settings.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'ifmerge_gui.config.settings'` 或 import 错误）。

- [ ] **Step 5: 写 Settings**

Create `ifmerge_gui/config/settings.py`:

```python
"""应用配置（从仓库根 .env 加载/写回）。"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv, set_key

# .env 固定指向仓库根:settings.py 位于 <root>/ifmerge_gui/config/settings.py
# parents[2] = <root>，与当前工作目录无关。
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


@dataclass
class Settings:
    # 路径
    input_dir: str = "input"
    output_dir: str = "output"
    merged_template_path: str = "template/IF_Template.xlsm"

    # 算法默认
    default_threshold: float = 0.8
    default_mode: str = "max"

    # SAP AI Core
    aicore_auth_url: str = ""
    aicore_client_id: str = ""
    aicore_client_secret: str = ""
    aicore_base_url: str = ""
    aicore_resource_group: str = "default"
    aicore_deployment_id: str = ""
    aicore_model_name: str = ""

    # 运行
    log_level: str = "INFO"

    @classmethod
    def load(cls) -> "Settings":
        # override=True:.env 为权威来源，覆盖残留系统环境变量。
        load_dotenv(_ENV_PATH, override=True)
        return cls(
            input_dir=os.getenv("INPUT_DIR", "input"),
            output_dir=os.getenv("OUTPUT_DIR", "output"),
            merged_template_path=os.getenv(
                "MERGED_TEMPLATE_PATH", "template/IF_Template.xlsm"),
            default_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.8")),
            default_mode=os.getenv("SIMILARITY_MODE", "max"),
            aicore_auth_url=os.getenv("AICORE_AUTH_URL", ""),
            aicore_client_id=os.getenv("AICORE_CLIENT_ID", ""),
            aicore_client_secret=os.getenv("AICORE_CLIENT_SECRET", ""),
            aicore_base_url=os.getenv("AICORE_BASE_URL", ""),
            aicore_resource_group=os.getenv("AICORE_RESOURCE_GROUP", "default"),
            aicore_deployment_id=os.getenv("AICORE_DEPLOYMENT_ID", ""),
            aicore_model_name=os.getenv("AICORE_MODEL_NAME", ""),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    def save(self) -> str:
        """逐键写回 .env（保留其它内容），返回写入的文件路径。"""
        path = str(_ENV_PATH)
        if not _ENV_PATH.exists():
            _ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
            _ENV_PATH.touch()
        pairs = {
            "INPUT_DIR": self.input_dir,
            "OUTPUT_DIR": self.output_dir,
            "MERGED_TEMPLATE_PATH": self.merged_template_path,
            "SIMILARITY_THRESHOLD": str(self.default_threshold),
            "SIMILARITY_MODE": self.default_mode,
            "AICORE_AUTH_URL": self.aicore_auth_url,
            "AICORE_CLIENT_ID": self.aicore_client_id,
            "AICORE_CLIENT_SECRET": self.aicore_client_secret,
            "AICORE_BASE_URL": self.aicore_base_url,
            "AICORE_RESOURCE_GROUP": self.aicore_resource_group,
            "AICORE_DEPLOYMENT_ID": self.aicore_deployment_id,
            "AICORE_MODEL_NAME": self.aicore_model_name,
            "LOG_LEVEL": self.log_level,
        }
        for key, value in pairs.items():
            set_key(path, key, value or "")
        return path
```

- [ ] **Step 6: 运行测试，确认通过**

Run: `python -m pytest tests/test_gui_settings.py -v`
Expected: PASS（2 passed）。

注意 `test_save_load_roundtrip` 里 `Settings.load()` 用模块级 `_ENV_PATH`，已被 monkeypatch 改为 tmp 路径，且 `load()` 内 `load_dotenv(_ENV_PATH, ...)` 引用同一模块变量——确认两处都解析到被 patch 的值（`load()` 内是 `load_dotenv(_ENV_PATH, override=True)`，读的是模块全局，patch 生效）。

- [ ] **Step 7: 追加依赖**

Modify `requirements.txt` — 在文件末尾追加一行：

```
customtkinter>=5.2.0
```

- [ ] **Step 8: 安装并提交**

Run: `pip install "customtkinter>=5.2.0"`
Expected: 安装成功（或已满足）。

```bash
git add ifmerge_gui/__init__.py ifmerge_gui/config/ ifmerge_gui/utils/ requirements.txt tests/test_gui_settings.py
git commit -m "feat(gui): scaffold ifmerge_gui package with Settings and logger"
```

---

### Task 2: i18n（Translator + zh/ja/en locale）

**Files:**
- Create: `ifmerge_gui/i18n/__init__.py`, `ifmerge_gui/i18n/locales/zh.json`, `ifmerge_gui/i18n/locales/ja.json`, `ifmerge_gui/i18n/locales/en.json`
- Test: `tests/test_gui_i18n.py`

**Interfaces:**
- Produces: `ifmerge_gui.i18n.translator`（Translator 单例）、`ifmerge_gui.i18n.t(key, **kwargs) -> str`、`ifmerge_gui.i18n.AVAILABLE`（`{"zh":"中文","ja":"日本語","en":"English"}`）、`translator.set_language(lang)`、`translator.current()`。
- 所有 locale 文件含**完全一致**的 key 集合。

- [ ] **Step 1: 写失败测试**

Create `tests/test_gui_i18n.py`:

```python
import json
from pathlib import Path

import ifmerge_gui.i18n as i18n

LOCALES = Path(i18n.__file__).parent / "locales"


def _load(name):
    return json.loads((LOCALES / f"{name}.json").read_text(encoding="utf-8"))


def test_locale_key_parity():
    zh = set(_load("zh").keys())
    ja = set(_load("ja").keys())
    en = set(_load("en").keys())
    assert zh == ja == en, f"key mismatch: zh-ja={zh ^ ja}, zh-en={zh ^ en}"


def test_default_language_is_zh():
    # 全新单例（无 ~/.ifmerge/config.json 时）默认 zh
    from ifmerge_gui.i18n import Translator
    tr = Translator(config_path=Path("/nonexistent/xyz/config.json"))
    assert tr.current() == "zh"


def test_t_formats_kwargs():
    from ifmerge_gui.i18n import Translator
    tr = Translator(config_path=Path("/nonexistent/xyz/config.json"))
    msg = tr.t("log.start_file", name="a.xlsx")
    assert "a.xlsx" in msg


def test_required_keys_present():
    zh = _load("zh")
    for key in ["app.title", "sidebar.analyze", "sidebar.merge",
                "page.run_analyze", "page.run_merge", "phase.read",
                "phase.classify", "settings.title", "logviewer.title"]:
        assert key in zh, f"missing {key}"
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python -m pytest tests/test_gui_i18n.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'ifmerge_gui.i18n'`）。

- [ ] **Step 3: 写 Translator**

Create `ifmerge_gui/i18n/__init__.py`:

```python
"""多语言(i18n):Translator 单例 + JSON locale + 用户配置持久化。"""

import json
from pathlib import Path

_LOCALES_DIR = Path(__file__).parent / "locales"
_CONFIG_PATH = Path.home() / ".ifmerge" / "config.json"
_DEFAULT_LANG = "zh"
AVAILABLE = {"zh": "中文", "ja": "日本語", "en": "English"}


class Translator:
    def __init__(self, locales_dir=_LOCALES_DIR, config_path=_CONFIG_PATH,
                 default_lang=_DEFAULT_LANG):
        self._locales_dir = Path(locales_dir)
        self._config_path = Path(config_path)
        self._default = default_lang
        self._cache: dict[str, dict] = {}
        self._lang = self._load_saved_language()

    def current(self) -> str:
        return self._lang

    def available(self) -> dict:
        return dict(AVAILABLE)

    def t(self, key: str, **kwargs) -> str:
        s = self._locale(self._lang).get(key)
        if s is None:
            s = self._locale(self._default).get(key, key)
        if kwargs:
            try:
                return s.format(**kwargs)
            except Exception:
                return s
        return s

    def set_language(self, lang: str) -> None:
        if lang not in AVAILABLE:
            return
        self._lang = lang
        self._save_language(lang)

    def _locale(self, lang: str) -> dict:
        if lang not in self._cache:
            path = self._locales_dir / f"{lang}.json"
            try:
                self._cache[lang] = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                self._cache[lang] = {}
        return self._cache[lang]

    def _load_saved_language(self) -> str:
        try:
            cfg = json.loads(self._config_path.read_text(encoding="utf-8"))
            if cfg.get("language") in AVAILABLE:
                return cfg["language"]
        except Exception:
            pass
        return self._default

    def _save_language(self, lang: str) -> None:
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            self._config_path.write_text(
                json.dumps({"language": lang}), encoding="utf-8")
        except Exception:
            pass


translator = Translator()


def t(key: str, **kwargs) -> str:
    return translator.t(key, **kwargs)
```

- [ ] **Step 4: 写 zh.json**

Create `ifmerge_gui/i18n/locales/zh.json`:

```json
{
  "app.title": "IFmerge — EBS 接口设计书 解析・合并工具",
  "sidebar.analyze": "▶ 解析",
  "sidebar.merge": "▶ 合并",
  "sidebar.logs": "📜 日志",
  "sidebar.settings": "⚙ 设置",
  "page.run_analyze": "▶ 开始解析",
  "page.run_merge": "▶ 开始合并",
  "page.cancel": "取消",
  "input.title": "文件输入",
  "input.choose_folder": "📁 选择文件夹",
  "input.unselected": "未选择",
  "input.folder_fmt": "📁 {path}",
  "input.dialog_title": "选择 EBS 接口设计书文件夹",
  "output.title": "文件输出",
  "output.open": "📂 打开文件夹",
  "output.prefix": "输出: {dir}",
  "progress.title": "进度 / 日志",
  "progress.idle": "待机",
  "progress.done": "✓ 完成",
  "progress.failed": "✗ 失败",
  "phase.read": "读取中",
  "phase.group": "IF 分组",
  "phase.classify": "AI 分类",
  "phase.gen_info": "AI 概要生成",
  "phase.similarity": "相似度计算",
  "phase.grouping": "分组合并",
  "phase.merged_name": "合并名生成",
  "phase.template": "模板输出",
  "phase.matrix": "矩阵输出",
  "phase.output": "结果输出",
  "phase.done": "完成",
  "log.start_file": "开始处理 {name}",
  "log.loaded": "{name}: 读取 {rows} 行数据",
  "log.if_found": "发现 {n} 个 IF",
  "log.classified": "AI 分类完成: {n} 个分类",
  "log.gen_info_ok": "IF 信息一括生成: {n} 件",
  "log.analyze_excel": "解析结果 Excel: {path}",
  "log.module": "正在处理模块 {module}",
  "log.scenario": "场景 {scenario}: {ifs} 个 IF, {rows} 行",
  "log.similar_pairs": "发现 {n} 组相似 IF",
  "log.groups": "生成 {n} 个分组",
  "log.grouping_ok": "グルーピング結果: {path}",
  "log.matrix_ok": "類似度マトリックス: {path}",
  "log.template_ok": "模板输出完成: 模块 {module}",
  "log.file_done": "✓ {name} 处理成功",
  "log.file_fail": "✗ {name} 处理失败: {error}",
  "log.cancelled": "已被用户取消",
  "log.saved": "📜 日志已保存: {path}",
  "log.save_fail": "⚠ 日志保存失败: {error}",
  "log.failed": "✗ 失败: {type}: {error}",
  "settings.title": "设置",
  "settings.language": "语言 / Language",
  "settings.aicore_base_url": "AI Core Base URL",
  "settings.test_conn": "测试连接",
  "settings.test_ok": "✓ 连接成功",
  "settings.test_fail": "✗ 连接失败: {error}",
  "settings.advanced_show": "▸ 高级设置",
  "settings.advanced_hide": "▾ 高级设置",
  "settings.aicore_auth_url": "AI Core Auth URL",
  "settings.aicore_client_id": "Client ID",
  "settings.aicore_client_secret": "Client Secret",
  "settings.aicore_resource_group": "Resource Group",
  "settings.aicore_deployment_id": "Deployment ID",
  "settings.output_dir": "输出目录",
  "settings.threshold": "相似度阈值 (0.5–1.0)",
  "settings.mode": "相似度模式",
  "settings.merged_template": "合并模板 xlsm",
  "settings.log_level": "日志级别",
  "settings.save": "保存",
  "settings.cancel": "取消",
  "logviewer.title": "执行日志",
  "logviewer.history": "历史日志(新→旧)",
  "logviewer.empty": "(暂无日志)",
  "logviewer.read_fail": "读取失败: {error}"
}
```

- [ ] **Step 5: 写 ja.json**

Create `ifmerge_gui/i18n/locales/ja.json`:

```json
{
  "app.title": "IFmerge — EBS 設計書 解析・マージツール",
  "sidebar.analyze": "▶ 解析",
  "sidebar.merge": "▶ マージ",
  "sidebar.logs": "📜 ログ",
  "sidebar.settings": "⚙ 設定",
  "page.run_analyze": "▶ 解析開始",
  "page.run_merge": "▶ マージ開始",
  "page.cancel": "キャンセル",
  "input.title": "ファイル入力",
  "input.choose_folder": "📁 フォルダ選択",
  "input.unselected": "未選択",
  "input.folder_fmt": "📁 {path}",
  "input.dialog_title": "EBS 設計書フォルダを選択",
  "output.title": "ファイル出力",
  "output.open": "📂 フォルダを開く",
  "output.prefix": "出力: {dir}",
  "progress.title": "進捗 / ログ",
  "progress.idle": "待機中",
  "progress.done": "✓ 完了",
  "progress.failed": "✗ 失敗",
  "phase.read": "読み込み中",
  "phase.group": "IF グループ化",
  "phase.classify": "AI 分類",
  "phase.gen_info": "AI 概要生成",
  "phase.similarity": "類似度計算",
  "phase.grouping": "グルーピング",
  "phase.merged_name": "マージ名生成",
  "phase.template": "テンプレート出力",
  "phase.matrix": "マトリックス出力",
  "phase.output": "結果出力",
  "phase.done": "完了",
  "log.start_file": "{name} の処理を開始",
  "log.loaded": "{name}: {rows} 行を読み込み",
  "log.if_found": "{n} 個の IF を発見",
  "log.classified": "AI 分類完了: {n} 分類",
  "log.gen_info_ok": "IF 情報を一括生成: {n} 件",
  "log.analyze_excel": "解析結果 Excel: {path}",
  "log.module": "モジュール {module} を処理中",
  "log.scenario": "シナリオ {scenario}: IF {ifs} 個, {rows} 行",
  "log.similar_pairs": "{n} 組の類似 IF を発見",
  "log.groups": "{n} 個のグループを生成",
  "log.grouping_ok": "グルーピング結果: {path}",
  "log.matrix_ok": "類似度マトリックス: {path}",
  "log.template_ok": "テンプレート出力完了: モジュール {module}",
  "log.file_done": "✓ {name} 処理成功",
  "log.file_fail": "✗ {name} 処理失敗: {error}",
  "log.cancelled": "ユーザーによりキャンセルされました",
  "log.saved": "📜 ログを保存: {path}",
  "log.save_fail": "⚠ ログ保存失敗: {error}",
  "log.failed": "✗ 失敗: {type}: {error}",
  "settings.title": "設定",
  "settings.language": "言語 / Language",
  "settings.aicore_base_url": "AI Core Base URL",
  "settings.test_conn": "接続テスト",
  "settings.test_ok": "✓ 接続成功",
  "settings.test_fail": "✗ 接続失敗: {error}",
  "settings.advanced_show": "▸ 詳細設定",
  "settings.advanced_hide": "▾ 詳細設定",
  "settings.aicore_auth_url": "AI Core Auth URL",
  "settings.aicore_client_id": "Client ID",
  "settings.aicore_client_secret": "Client Secret",
  "settings.aicore_resource_group": "Resource Group",
  "settings.aicore_deployment_id": "Deployment ID",
  "settings.output_dir": "出力ディレクトリ",
  "settings.threshold": "類似度閾値 (0.5–1.0)",
  "settings.mode": "類似度モード",
  "settings.merged_template": "マージテンプレート xlsm",
  "settings.log_level": "ログレベル",
  "settings.save": "保存",
  "settings.cancel": "キャンセル",
  "logviewer.title": "実行ログ",
  "logviewer.history": "履歴ログ(新→旧)",
  "logviewer.empty": "(ログなし)",
  "logviewer.read_fail": "読み込み失敗: {error}"
}
```

- [ ] **Step 6: 写 en.json**

Create `ifmerge_gui/i18n/locales/en.json`:

```json
{
  "app.title": "IFmerge — EBS Interface Spec Analyze/Merge Tool",
  "sidebar.analyze": "▶ Analyze",
  "sidebar.merge": "▶ Merge",
  "sidebar.logs": "📜 Logs",
  "sidebar.settings": "⚙ Settings",
  "page.run_analyze": "▶ Start Analyze",
  "page.run_merge": "▶ Start Merge",
  "page.cancel": "Cancel",
  "input.title": "Input",
  "input.choose_folder": "📁 Choose Folder",
  "input.unselected": "Not selected",
  "input.folder_fmt": "📁 {path}",
  "input.dialog_title": "Select EBS interface spec folder",
  "output.title": "Output",
  "output.open": "📂 Open Folder",
  "output.prefix": "Output: {dir}",
  "progress.title": "Progress / Log",
  "progress.idle": "Idle",
  "progress.done": "✓ Done",
  "progress.failed": "✗ Failed",
  "phase.read": "Reading",
  "phase.group": "Grouping IFs",
  "phase.classify": "AI Classify",
  "phase.gen_info": "AI Summaries",
  "phase.similarity": "Similarity",
  "phase.grouping": "Merge Grouping",
  "phase.merged_name": "Merged Names",
  "phase.template": "Template Output",
  "phase.matrix": "Matrix Output",
  "phase.output": "Output",
  "phase.done": "Done",
  "log.start_file": "Processing {name}",
  "log.loaded": "{name}: loaded {rows} rows",
  "log.if_found": "Found {n} IFs",
  "log.classified": "AI classify done: {n} categories",
  "log.gen_info_ok": "Generated IF info: {n} items",
  "log.analyze_excel": "Analyze result Excel: {path}",
  "log.module": "Processing module {module}",
  "log.scenario": "Scenario {scenario}: {ifs} IFs, {rows} rows",
  "log.similar_pairs": "Found {n} similar IF pairs",
  "log.groups": "Generated {n} groups",
  "log.grouping_ok": "Grouping result: {path}",
  "log.matrix_ok": "Similarity matrix: {path}",
  "log.template_ok": "Template output done: module {module}",
  "log.file_done": "✓ {name} succeeded",
  "log.file_fail": "✗ {name} failed: {error}",
  "log.cancelled": "Cancelled by user",
  "log.saved": "📜 Log saved: {path}",
  "log.save_fail": "⚠ Log save failed: {error}",
  "log.failed": "✗ Failed: {type}: {error}",
  "settings.title": "Settings",
  "settings.language": "Language",
  "settings.aicore_base_url": "AI Core Base URL",
  "settings.test_conn": "Test Connection",
  "settings.test_ok": "✓ Connected",
  "settings.test_fail": "✗ Connection failed: {error}",
  "settings.advanced_show": "▸ Advanced",
  "settings.advanced_hide": "▾ Advanced",
  "settings.aicore_auth_url": "AI Core Auth URL",
  "settings.aicore_client_id": "Client ID",
  "settings.aicore_client_secret": "Client Secret",
  "settings.aicore_resource_group": "Resource Group",
  "settings.aicore_deployment_id": "Deployment ID",
  "settings.output_dir": "Output Dir",
  "settings.threshold": "Similarity Threshold (0.5-1.0)",
  "settings.mode": "Similarity Mode",
  "settings.merged_template": "Merge Template xlsm",
  "settings.log_level": "Log Level",
  "settings.save": "Save",
  "settings.cancel": "Cancel",
  "logviewer.title": "Execution Logs",
  "logviewer.history": "History (new→old)",
  "logviewer.empty": "(no logs)",
  "logviewer.read_fail": "Read failed: {error}"
}
```

- [ ] **Step 7: 运行测试，确认通过**

Run: `python -m pytest tests/test_gui_i18n.py -v`
Expected: PASS（4 passed）。若 `test_locale_key_parity` 失败，按差异集补齐缺失 key。

- [ ] **Step 8: 提交**

```bash
git add ifmerge_gui/i18n/ tests/test_gui_i18n.py
git commit -m "feat(gui): add i18n translator with zh/ja/en locales"
```

---

### Task 3: 文件系统工具（find_excel_files / open_folder）

**Files:**
- Create: `ifmerge_gui/ui/__init__.py`, `ifmerge_gui/ui/utils/__init__.py`, `ifmerge_gui/ui/utils/fs.py`
- Test: `tests/test_gui_fs.py`

**Interfaces:**
- Produces: `ifmerge_gui.ui.utils.fs.find_excel_files(folder: Path) -> list[Path]`（递归 `.xlsx`，跳过 `~$`，按路径排序）；`open_folder(folder: Path) -> None`（跨平台打开，目录不存在则创建）。

- [ ] **Step 1: 创建包标记**

Create `ifmerge_gui/ui/__init__.py` and `ifmerge_gui/ui/utils/__init__.py` — both empty.

- [ ] **Step 2: 写失败测试**

Create `tests/test_gui_fs.py`:

```python
from pathlib import Path

from ifmerge_gui.ui.utils.fs import find_excel_files


def test_finds_nested_xlsx_skips_lock_and_nonxlsx(tmp_path):
    (tmp_path / "a.xlsx").write_text("x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.xlsx").write_text("x")
    (tmp_path / "~$temp.xlsx").write_text("x")   # Excel 锁文件，应跳过
    (tmp_path / "note.txt").write_text("x")        # 非 Excel，应跳过
    (tmp_path / "old.xls").write_text("x")         # .xls 不收（只认 .xlsx）

    found = find_excel_files(tmp_path)
    names = sorted(p.name for p in found)
    assert names == ["a.xlsx", "b.xlsx"]


def test_empty_folder_returns_empty(tmp_path):
    assert find_excel_files(tmp_path) == []
```

- [ ] **Step 3: 运行测试，确认失败**

Run: `python -m pytest tests/test_gui_fs.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'ifmerge_gui.ui.utils.fs'`）。

- [ ] **Step 4: 写 fs.py**

Create `ifmerge_gui/ui/utils/fs.py`:

```python
"""文件系统工具:递归扫描 Excel、跨平台打开文件夹。"""

import os
import subprocess
import sys
from pathlib import Path

EXCEL_SUFFIXES = {".xlsx"}  # 与 ebs_merger.DataLoader (openpyxl) 一致


def find_excel_files(folder: Path) -> list[Path]:
    """递归扫描文件夹下所有 .xlsx,跳过 Excel 临时锁文件(~$ 前缀)。"""
    folder = Path(folder)
    result = []
    for p in sorted(folder.rglob("*")):
        if (p.is_file()
                and p.suffix.lower() in EXCEL_SUFFIXES
                and not p.name.startswith("~$")):
            result.append(p)
    return result


def open_folder(folder: Path) -> None:
    """用系统资源管理器打开文件夹(跨平台);目录不存在则创建。"""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    if sys.platform.startswith("win"):
        os.startfile(str(folder))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(folder)], check=False)
    else:
        subprocess.run(["xdg-open", str(folder)], check=False)
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `python -m pytest tests/test_gui_fs.py -v`
Expected: PASS（2 passed）。

- [ ] **Step 6: 提交**

```bash
git add ifmerge_gui/ui/__init__.py ifmerge_gui/ui/utils/ tests/test_gui_fs.py
git commit -m "feat(gui): add fs utils (recursive xlsx scan, open folder)"
```

---

### Task 4: 控件（FileInput/FileOutput/ProgressLog）+ BasePage

**Files:**
- Create: `ifmerge_gui/ui/widgets/__init__.py`, `ifmerge_gui/ui/widgets/file_input.py`, `ifmerge_gui/ui/widgets/file_output.py`, `ifmerge_gui/ui/widgets/progress_log.py`, `ifmerge_gui/ui/pages/__init__.py`, `ifmerge_gui/ui/pages/base_page.py`

**Interfaces:**
- Consumes: `ifmerge_gui.ui.utils.fs.find_excel_files / open_folder`（Task 3）；`ifmerge_gui.i18n.t`（Task 2）。
- Produces:
  - `FileInput(master, on_change: Callable[[list[Path]], None])` with `.files()`, `.set_enabled(bool)`.
  - `FileOutput(master, output_dir: Path)` with `.set_output_dir(Path)`.
  - `ProgressLog(master)` with `.reset()`, `.set_progress(int, str)`, `.append_log(str)`, `.set_finished()`, `.set_failed()`.
  - `BasePage(ctk.CTkFrame)`，构造 `(master, app)`；暴露 `self.file_output`、回调 `self._cb_progress / _cb_log / _cb_done / _cb_failed`；抽象方法 `run_button_text() -> str`、`output_dir() -> Path`、`log_kind() -> str`、`create_task(files) -> threading.Thread`（带 `.start()`/`.cancel()`）。

> 注:本任务全是 Tk 控件,无自动化测试;正确性在 Task 8 启动后手动验证。本任务仅保证可 import(由 Task 8 的导入冒烟测试覆盖)。

- [ ] **Step 1: 创建 widgets 包标记**

Create `ifmerge_gui/ui/widgets/__init__.py` and `ifmerge_gui/ui/pages/__init__.py` — both empty.

- [ ] **Step 2: 写 FileInput**

Create `ifmerge_gui/ui/widgets/file_input.py`:

```python
"""文件输入块:选择文件夹,递归扫描其下所有 Excel。"""

from pathlib import Path
from tkinter import filedialog
from typing import Callable, List

import customtkinter as ctk

from ifmerge_gui.i18n import t
from ifmerge_gui.ui.utils.fs import find_excel_files


class FileInput(ctk.CTkFrame):

    def __init__(self, master, on_change: Callable[[List[Path]], None]):
        super().__init__(master)
        self._on_change = on_change
        self._files: List[Path] = []

        ctk.CTkLabel(self, text=t("input.title"), anchor="w",
                     font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=8, pady=(6, 0))
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=6)
        self.btn = ctk.CTkButton(row, text=t("input.choose_folder"), width=130,
                                 command=self._choose_folder)
        self.btn.pack(side="left")
        self.lbl_path = ctk.CTkLabel(row, text=t("input.unselected"), anchor="w")
        self.lbl_path.pack(side="left", fill="x", expand=True, padx=8)

    def _choose_folder(self):
        path = filedialog.askdirectory(title=t("input.dialog_title"))
        if not path:
            return
        folder = Path(path)
        self._files = find_excel_files(folder)
        self.lbl_path.configure(text=t("input.folder_fmt", path=folder))
        self._on_change(self._files)

    def files(self) -> List[Path]:
        return list(self._files)

    def set_enabled(self, enabled: bool):
        self.btn.configure(state="normal" if enabled else "disabled")
```

- [ ] **Step 3: 写 FileOutput**

Create `ifmerge_gui/ui/widgets/file_output.py`:

```python
"""文件输出块:显示输出目录路径 + 打开文件夹按钮。"""

from pathlib import Path

import customtkinter as ctk

from ifmerge_gui.i18n import t
from ifmerge_gui.ui.utils.fs import open_folder


class FileOutput(ctk.CTkFrame):

    def __init__(self, master, output_dir: Path):
        super().__init__(master)
        self._output_dir = Path(output_dir)

        ctk.CTkLabel(self, text=t("output.title"), anchor="w",
                     font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=8, pady=(6, 0))
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=6)
        ctk.CTkButton(row, text=t("output.open"), width=130,
                      command=self._open).pack(side="left")
        self.lbl = ctk.CTkLabel(row, text=t("output.prefix", dir=self._output_dir), anchor="w")
        self.lbl.pack(side="left", fill="x", expand=True, padx=8)

    def _open(self):
        open_folder(self._output_dir)

    def set_output_dir(self, output_dir: Path):
        self._output_dir = Path(output_dir)
        self.lbl.configure(text=t("output.prefix", dir=self._output_dir))
```

- [ ] **Step 4: 写 ProgressLog**

Create `ifmerge_gui/ui/widgets/progress_log.py`:

```python
"""进度 / 日志块:进度条 + 阶段文本 + 滚动日志。"""

import customtkinter as ctk

from ifmerge_gui.i18n import t


class ProgressLog(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text=t("progress.title"), anchor="w",
                     font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=8, pady=(6, 0))

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=4)
        self.bar = ctk.CTkProgressBar(top)
        self.bar.set(0)
        self.bar.pack(side="left", fill="x", expand=True)
        self.lbl_phase = ctk.CTkLabel(top, text=t("progress.idle"), width=180, anchor="w")
        self.lbl_phase.pack(side="left", padx=8)

        self.log = ctk.CTkTextbox(self, height=160)
        self.log.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.log.configure(state="disabled")

    def reset(self):
        self.bar.set(0)
        self.lbl_phase.configure(text=t("progress.idle"))
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def set_progress(self, percent: int, phase: str):
        self.bar.set(max(0.0, min(1.0, percent / 100.0)))
        if phase:
            self.lbl_phase.configure(text=phase)

    def append_log(self, msg: str):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def set_finished(self):
        self.bar.set(1.0)
        self.lbl_phase.configure(text=t("progress.done"))

    def set_failed(self):
        self.lbl_phase.configure(text=t("progress.failed"))
```

- [ ] **Step 5: 写 BasePage**

Create `ifmerge_gui/ui/pages/base_page.py`:

```python
"""页面抽象基类:文件输入 + 文件输出 + 执行 + 进度日志,统一线程编排。"""

from datetime import datetime
from pathlib import Path
from typing import List

import customtkinter as ctk

from ifmerge_gui.i18n import t
from ifmerge_gui.ui.widgets.file_input import FileInput
from ifmerge_gui.ui.widgets.file_output import FileOutput
from ifmerge_gui.ui.widgets.progress_log import ProgressLog


class BasePage(ctk.CTkFrame):
    """子类需重写 run_button_text() / output_dir() / log_kind() / create_task(files)。"""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._task = None
        self._files: List[Path] = []
        self._log_lines: List[str] = []

        self.file_input = FileInput(self, on_change=self._on_selection_change)
        self.file_input.pack(fill="x", padx=10, pady=(10, 4))

        self.file_output = FileOutput(self, output_dir=self.output_dir())
        self.file_output.pack(fill="x", padx=10, pady=4)

        exec_frame = ctk.CTkFrame(self)
        exec_frame.pack(fill="x", padx=10, pady=4)
        self.btn_run = ctk.CTkButton(exec_frame, text=self.run_button_text(),
                                     command=self._start, state="disabled")
        self.btn_run.pack(side="left", padx=8, pady=8)
        self.btn_cancel = ctk.CTkButton(exec_frame, text=t("page.cancel"), width=80,
                                        command=self._cancel, state="disabled")
        self.btn_cancel.pack(side="left", pady=8)

        self.progress_log = ProgressLog(self)
        self.progress_log.pack(fill="both", expand=True, padx=10, pady=(4, 10))

    # ── 子类重写 ──
    def run_button_text(self) -> str:
        raise NotImplementedError

    def output_dir(self) -> Path:
        raise NotImplementedError

    def log_kind(self) -> str:
        raise NotImplementedError

    def create_task(self, files: List[Path]):
        raise NotImplementedError

    # ── 内部 ──
    def _on_selection_change(self, files: List[Path]):
        self._files = files
        self.btn_run.configure(state="normal" if files else "disabled")

    def _start(self):
        if not self._files:
            return
        self._log_lines = []
        self.progress_log.reset()
        self._set_running(True)
        self._task = self.create_task(self._files)
        self._task.start()

    def _save_log(self):
        if not self._log_lines:
            return
        log_dir = self.output_dir() / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = log_dir / f"{self.log_kind()}_{ts}.log"
            path.write_text("\n".join(self._log_lines) + "\n", encoding="utf-8")
            self.progress_log.append_log(t("log.saved", path=path))
        except Exception as e:
            self.progress_log.append_log(t("log.save_fail", error=e))

    def _cancel(self):
        if self._task is not None:
            self._task.cancel()

    def _set_running(self, running: bool):
        self.btn_run.configure(state="disabled" if running else "normal")
        self.btn_cancel.configure(state="normal" if running else "disabled")
        self.file_input.set_enabled(not running)

    # ── 线程安全回调(经 after 调度回主线程)──
    def _cb_progress(self, percent: int, phase: str):
        self.after(0, lambda: self.progress_log.set_progress(percent, phase))

    def _cb_log(self, msg: str):
        def add():
            self._log_lines.append(msg)
            self.progress_log.append_log(msg)
        self.after(0, add)

    def _cb_done(self, result):
        def finish():
            self.progress_log.set_finished()
            self._save_log()
            self._set_running(False)
        self.after(0, finish)

    def _cb_failed(self, exc: Exception):
        def fail():
            self.progress_log.set_failed()
            msg = t("log.failed", type=type(exc).__name__, error=exc)
            self._log_lines.append(msg)
            self.progress_log.append_log(msg)
            self._save_log()
            self._set_running(False)
        self.after(0, fail)
```

- [ ] **Step 6: 提交**

```bash
git add ifmerge_gui/ui/widgets/ ifmerge_gui/ui/pages/
git commit -m "feat(gui): add widgets (file input/output, progress log) and BasePage"
```

---

### Task 5: AI 工厂 + 解析 Task + 解析页

**Files:**
- Create: `ifmerge_gui/core/__init__.py`, `ifmerge_gui/core/ai_factory.py`, `ifmerge_gui/ui/tasks/__init__.py`, `ifmerge_gui/ui/tasks/analyze_task.py`, `ifmerge_gui/ui/pages/analyze_page.py`
- Test: `tests/test_gui_ai_factory.py`

**Interfaces:**
- Consumes: `ebs_merger.ai_generator.AIGenerator`、`ebs_merger.data_loader.DataLoader`、`ebs_merger.if_grouper.IFGrouper`、`ebs_merger.ai_classifier.AIClassifier`；`ifmerge_gui.config.settings.Settings`；`BasePage`。
- Produces:
  - `ifmerge_gui.core.ai_factory.build_ai_generator(settings: Settings) -> AIGenerator`（用 settings 显式构造，使 GUI 设置成为权威来源；`deployment_id`/`model_name` 为空时传 `None`，让 AIGenerator 回退到环境变量/抛错）。
  - `AnalyzeTask(files, output_dir, settings, on_progress, on_log, on_done, on_failed)`（`threading.Thread`，含 `cancel()`）。
  - `AnalyzePage(BasePage)`。

- [ ] **Step 1: 创建 core 包标记**

Create `ifmerge_gui/core/__init__.py` and `ifmerge_gui/ui/tasks/__init__.py` — both empty.

- [ ] **Step 2: 写 ai_factory 失败测试**

Create `tests/test_gui_ai_factory.py`:

```python
from ifmerge_gui.config.settings import Settings
from ifmerge_gui.core.ai_factory import build_ai_generator


def test_build_passes_settings_through_without_network():
    # 提供 deployment_id 时,AIGenerator.__init__ 不会发起网络请求。
    s = Settings(
        aicore_auth_url="https://auth.example",
        aicore_client_id="cid",
        aicore_client_secret="secret",
        aicore_base_url="https://api.example/v2",
        aicore_resource_group="rg1",
        aicore_deployment_id="dep-123",
    )
    gen = build_ai_generator(s)
    assert gen.auth_url == "https://auth.example"
    assert gen.client_id == "cid"
    assert gen.base_url == "https://api.example/v2"
    assert gen.resource_group == "rg1"
    assert gen.deployment_id == "dep-123"
```

- [ ] **Step 3: 运行测试，确认失败**

Run: `python -m pytest tests/test_gui_ai_factory.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'ifmerge_gui.core.ai_factory'`）。

- [ ] **Step 4: 写 ai_factory**

Create `ifmerge_gui/core/ai_factory.py`:

```python
"""用 GUI Settings 显式构造 ebs_merger 的 AIGenerator(使设置成为权威来源)。"""

from ebs_merger.ai_generator import AIGenerator

from ifmerge_gui.config.settings import Settings


def build_ai_generator(settings: Settings) -> AIGenerator:
    """根据 settings 构造 AIGenerator。

    deployment_id / model_name 为空时传 None:AIGenerator 会回退到
    环境变量 AICORE_DEPLOYMENT_ID,仍为空则抛 ValueError(由调用方捕获)。
    """
    return AIGenerator(
        auth_url=settings.aicore_auth_url or None,
        client_id=settings.aicore_client_id or None,
        client_secret=settings.aicore_client_secret or None,
        base_url=settings.aicore_base_url or None,
        resource_group=settings.aicore_resource_group or "default",
        deployment_id=settings.aicore_deployment_id or None,
        model_name=settings.aicore_model_name or None,
    )
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `python -m pytest tests/test_gui_ai_factory.py -v`
Expected: PASS（1 passed）。

> 若环境无 `.env` 凭据,该测试仍通过——因为传入了显式参数且 `deployment_id` 非空,`AIGenerator.__init__` 不读环境也不发网络请求。

- [ ] **Step 6: 写 AnalyzeTask**

Create `ifmerge_gui/ui/tasks/analyze_task.py`:

```python
"""解析后台任务(进程内调用 ebs_merger)。

流程:逐文件 load_excel -> group_by_if -> AI 分类 -> AI 概要生成
     -> 写 解析結果.xlsx(每个 IF 一行,不分组)。
"""

import logging
import threading
from pathlib import Path
from typing import Callable, List

import pandas as pd

from ebs_merger.ai_classifier import AIClassifier
from ebs_merger.data_loader import DataLoader
from ebs_merger.if_grouper import IFGrouper

from ifmerge_gui.config.settings import Settings
from ifmerge_gui.core.ai_factory import build_ai_generator
from ifmerge_gui.i18n import t

logger = logging.getLogger("ifmerge_gui.ui.tasks.analyze")

_COLUMNS = ["No.", "文書管理番号", "IF名", "モジュール", "業務内容",
            "項目数", "IF概要", "代表項目名"]


class AnalyzeTask(threading.Thread):

    def __init__(self, files: List[Path], output_dir: Path, settings: Settings,
                 on_progress: Callable[[int, str], None],
                 on_log: Callable[[str], None],
                 on_done: Callable[[object], None],
                 on_failed: Callable[[Exception], None]):
        super().__init__(daemon=True)
        self.files = [Path(f) for f in files]
        self.output_dir = Path(output_dir)
        self.settings = settings
        self.on_progress = on_progress
        self.on_log = on_log
        self.on_done = on_done
        self.on_failed = on_failed
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            gen = build_ai_generator(self.settings)
            loader = DataLoader()
            grouper = IFGrouper()
            classifier = AIClassifier(ai_generator=gen)

            total = len(self.files)
            all_rows = []
            for idx, input_file in enumerate(self.files, 1):
                if self._cancel:
                    self.on_log(t("log.cancelled"))
                    break
                base = int((idx - 1) / total * 100) if total else 0
                self.on_progress(base, f"[{idx}/{total}] " + t("phase.read"))
                self.on_log(t("log.start_file", name=input_file.name))
                try:
                    rows = self._process_file(input_file, base, idx, total,
                                              gen, loader, grouper, classifier)
                    all_rows.extend(rows)
                    self.on_log(t("log.file_done", name=input_file.name))
                except Exception as e:
                    logger.exception("analyze file failed")
                    self.on_log(t("log.file_fail", name=input_file.name, error=e))

            if self._cancel:
                self.on_done(None)
                return

            if all_rows:
                for i, r in enumerate(all_rows, 1):
                    r["No."] = i
                path = self.output_dir / "解析結果.xlsx"
                pd.DataFrame(all_rows)[_COLUMNS].to_excel(
                    path, index=False, engine="openpyxl")
                self.on_log(t("log.analyze_excel", path=path))

            self.on_progress(100, t("phase.done"))
            self.on_done(all_rows)
        except Exception as e:
            logger.exception("analyze task failed")
            self.on_failed(e)

    def _process_file(self, input_file, base, idx, total, gen, loader, grouper, classifier):
        df = loader.load_excel(str(input_file))
        self.on_log(t("log.loaded", name=input_file.name, rows=len(df)))

        self.on_progress(base, f"[{idx}/{total}] " + t("phase.group"))
        if_dict = grouper.group_by_if(df)
        self.on_log(t("log.if_found", n=len(if_dict)))

        self.on_progress(base, f"[{idx}/{total}] " + t("phase.classify"))
        categories = classifier.classify_interfaces(if_dict, df)
        self.on_log(t("log.classified", n=len(categories)))

        # IF -> (module, scenario) 查找表
        if_to_modscn = {}
        for _cat, (module, scenario, if_names) in categories.items():
            for name in if_names:
                if_to_modscn[name] = (module, scenario)

        self.on_progress(base, f"[{idx}/{total}] " + t("phase.gen_info"))
        try:
            all_if_info = gen.generate_all_if_info(if_dict, df)
            self.on_log(t("log.gen_info_ok", n=len(all_if_info)))
        except Exception:
            all_if_info = {}

        rows = []
        for if_name in sorted(if_dict.keys()):
            info = if_dict[if_name]
            module, scenario = if_to_modscn.get(if_name, ("その他", "未分類"))
            summary = all_if_info.get(if_name, {}).get("summary", "")
            rep = all_if_info.get(if_name, {}).get(
                "representative_item", info.representative_item)
            rows.append({
                "文書管理番号": info.doc_number,
                "IF名": if_name,
                "モジュール": module,
                "業務内容": scenario,
                "項目数": info.item_count,
                "IF概要": summary,
                "代表項目名": rep,
            })
        return rows
```

- [ ] **Step 7: 写 AnalyzePage**

Create `ifmerge_gui/ui/pages/analyze_page.py`:

```python
"""解析页。"""

from pathlib import Path
from typing import List

from ifmerge_gui.i18n import t
from ifmerge_gui.ui.pages.base_page import BasePage
from ifmerge_gui.ui.tasks.analyze_task import AnalyzeTask


class AnalyzePage(BasePage):

    def run_button_text(self) -> str:
        return t("page.run_analyze")

    def log_kind(self) -> str:
        return "parse"

    def output_dir(self) -> Path:
        return Path(self.app.settings.output_dir) / "parse"

    def create_task(self, files: List[Path]):
        return AnalyzeTask(
            files=files, output_dir=self.output_dir(),
            settings=self.app.settings,
            on_progress=self._cb_progress, on_log=self._cb_log,
            on_done=self._cb_done, on_failed=self._cb_failed,
        )
```

- [ ] **Step 8: 提交**

```bash
git add ifmerge_gui/core/ ifmerge_gui/ui/tasks/__init__.py ifmerge_gui/ui/tasks/analyze_task.py ifmerge_gui/ui/pages/analyze_page.py tests/test_gui_ai_factory.py
git commit -m "feat(gui): add AI factory, analyze task and analyze page"
```

---

### Task 6: 合并 Task + 合并页

**Files:**
- Create: `ifmerge_gui/ui/tasks/merge_task.py`, `ifmerge_gui/ui/pages/merge_page.py`

**Interfaces:**
- Consumes: `ebs_merger`（DataLoader/IFGrouper/SimilarityCalculator/MergeGrouper/ResultGenerator/TemplateFiller/MatrixExporter/AIClassifier）；`build_ai_generator`；`BasePage`。
- Produces:
  - `MergeTask(files, output_dir, threshold, mode, settings, on_progress, on_log, on_done, on_failed)`（`threading.Thread`，含 `cancel()`）。每个输入文件输出到 `output_dir/<file_stem>/`：`グルーピング結果.xlsx` + 各模块子文件夹（`類似度マトリックス_<module>.xlsx` + 填充模板 `.xlsm`）。
  - `MergePage(BasePage)`。

> 编排镜像自 `ebs_merger/cli.py` 的 `process_single_file` / `process_module` / `_generate_output_rows` / `_get_merged_if_names` / `_write_unified_output`,改动:(1) 加 `on_progress/on_log` 与 `_cancel` 检查;(2) 每个输入文件写入独立子目录 `output_dir/<stem>/`(避免多文件互相覆盖,优于 cli.py 的扁平覆盖)。无自动化测试(依赖真实 AI 凭据),由导入冒烟 + 手动验证覆盖。

- [ ] **Step 1: 写 MergeTask**

Create `ifmerge_gui/ui/tasks/merge_task.py`:

```python
"""合并后台任务(进程内调用 ebs_merger,编排镜像自 ebs_merger/cli.py)。"""

import logging
import threading
from collections import defaultdict
from pathlib import Path
from typing import Callable, List

import pandas as pd

from ebs_merger.ai_classifier import AIClassifier
from ebs_merger.data_loader import DataLoader
from ebs_merger.if_grouper import IFGrouper
from ebs_merger.matrix_exporter import MatrixExporter
from ebs_merger.merge_grouper import MergeGrouper
from ebs_merger.result_generator import ResultGenerator
from ebs_merger.similarity_calculator import SimilarityCalculator
from ebs_merger.template_filler import TemplateFiller

from ifmerge_gui.config.settings import Settings
from ifmerge_gui.core.ai_factory import build_ai_generator
from ifmerge_gui.i18n import t

logger = logging.getLogger("ifmerge_gui.ui.tasks.merge")

_COLUMNS = ["No.", "文書管理番号", "IF名", "モジュール", "業務内容", "項目数",
            "IF概要", "代表項目名", "グルーピングID", "マージ要否",
            "グルーピング後のIF名", "グルーピングの根拠"]


class MergeTask(threading.Thread):

    def __init__(self, files: List[Path], output_dir: Path,
                 threshold: float, mode: str, settings: Settings,
                 on_progress: Callable[[int, str], None],
                 on_log: Callable[[str], None],
                 on_done: Callable[[object], None],
                 on_failed: Callable[[Exception], None]):
        super().__init__(daemon=True)
        self.files = [Path(f) for f in files]
        self.output_dir = Path(output_dir)
        self.threshold = threshold
        self.mode = mode
        self.settings = settings
        self.on_progress = on_progress
        self.on_log = on_log
        self.on_done = on_done
        self.on_failed = on_failed
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            gen = build_ai_generator(self.settings)
            self.loader = DataLoader()
            self.grouper = IFGrouper()
            self.calc = SimilarityCalculator()
            self.mgrouper = MergeGrouper()
            self.result_gen = ResultGenerator(use_ai=True)
            self.result_gen.ai_generator = gen  # 注入由 settings 构造的 generator
            self.template_filler = TemplateFiller(
                template_path=self.settings.merged_template_path)
            self.matrix_exporter = MatrixExporter()
            self.classifier = AIClassifier(ai_generator=gen)

            total = len(self.files)
            for idx, input_file in enumerate(self.files, 1):
                if self._cancel:
                    self.on_log(t("log.cancelled"))
                    break
                base = int((idx - 1) / total * 100) if total else 0
                self.on_progress(base, f"[{idx}/{total}] " + t("phase.read"))
                self.on_log(t("log.start_file", name=input_file.name))
                try:
                    self._process_file(input_file, base, idx, total)
                    self.on_log(t("log.file_done", name=input_file.name))
                except Exception as e:
                    logger.exception("merge file failed")
                    self.on_log(t("log.file_fail", name=input_file.name, error=e))

            if self._cancel:
                self.on_done(None)
                return
            self.on_progress(100, t("phase.done"))
            self.on_done(None)
        except Exception as e:
            logger.exception("merge task failed")
            self.on_failed(e)

    def _process_file(self, input_file, base, idx, total):
        out_dir = self.output_dir / input_file.stem
        out_dir.mkdir(parents=True, exist_ok=True)

        df = self.loader.load_excel(str(input_file))
        self.on_log(t("log.loaded", name=input_file.name, rows=len(df)))

        self.on_progress(base, f"[{idx}/{total}] " + t("phase.group"))
        if_dict = self.grouper.group_by_if(df)
        self.on_log(t("log.if_found", n=len(if_dict)))

        self.on_progress(base, f"[{idx}/{total}] " + t("phase.classify"))
        categories = self.classifier.classify_interfaces(if_dict, df)
        self.on_log(t("log.classified", n=len(categories)))

        # 按模块组织:{module: {scenario: (category_name, if_dict, df)}}
        module_data = defaultdict(dict)
        for category_name, (module, scenario, if_names) in categories.items():
            cat_if_dict = {n: if_dict[n] for n in if_names if n in if_dict}
            cat_df = df[df["IF名"].isin(if_names)]
            module_data[module][scenario] = (category_name, cat_if_dict, cat_df)

        all_rows = []
        for module_name, scenarios in module_data.items():
            if self._cancel:
                return
            self.on_log(t("log.module", module=module_name))
            all_rows.extend(self._process_module(
                module_name, scenarios, out_dir, base, idx, total))

        for i, r in enumerate(all_rows, 1):
            r["No."] = i
        path = out_dir / "グルーピング結果.xlsx"
        pd.DataFrame(all_rows)[_COLUMNS].to_excel(
            path, index=False, engine="openpyxl")
        self.on_log(t("log.grouping_ok", path=path))

    def _process_module(self, module_name, scenarios, out_dir, base, idx, total):
        safe = module_name.replace("/", "_").replace("\\", "_").replace(":", "_")
        module_dir = out_dir / safe
        module_dir.mkdir(parents=True, exist_ok=True)

        all_module_rows = []
        module_matrix_data = {}
        group_id_counter = 1

        for scenario, (category_name, if_dict, df) in scenarios.items():
            if self._cancel:
                return all_module_rows
            self.on_progress(base, f"[{idx}/{total}] " + t("phase.similarity"))
            self.on_log(t("log.scenario", scenario=scenario,
                          ifs=len(if_dict), rows=len(df)))
            similar_pairs = self.calc.build_similarity_matrix(
                if_dict, self.threshold, self.mode)
            self.on_log(t("log.similar_pairs", n=len(similar_pairs)))
            all_similarity_pairs = self.calc.build_full_similarity_matrix(
                if_dict, self.mode)

            self.on_progress(base, f"[{idx}/{total}] " + t("phase.grouping"))
            groups = self.mgrouper.group_similar_ifs(if_dict, similar_pairs)
            group_assignments = {}
            for group_members in groups.values():
                formatted_id = f"{safe}{group_id_counter:03d}"
                for if_name in group_members:
                    group_assignments[if_name] = formatted_id
                group_id_counter += 1
            self.on_log(t("log.groups", n=len(groups)))

            self.on_progress(base, f"[{idx}/{total}] " + t("phase.merged_name"))
            rows = self._generate_output_rows(
                if_dict, group_assignments, similar_pairs, df,
                module_name, scenario)
            all_module_rows.extend(rows)
            module_matrix_data[scenario] = (category_name, if_dict, all_similarity_pairs)

            self.on_progress(base, f"[{idx}/{total}] " + t("phase.template"))
            merged_if_names = self._get_merged_if_names(
                if_dict, group_assignments, df)
            self.template_filler.fill_merged_groups(
                if_dict, group_assignments, similar_pairs, df,
                str(module_dir), merged_if_names)
            self.on_log(t("log.template_ok", module=module_name))

        self.on_progress(base, f"[{idx}/{total}] " + t("phase.matrix"))
        matrix_path = module_dir / f"類似度マトリックス_{safe}.xlsx"
        self.matrix_exporter.export_module_matrices(
            module_matrix_data, str(matrix_path), module_name)
        self.on_log(t("log.matrix_ok", path=matrix_path))
        return all_module_rows

    def _generate_output_rows(self, if_dict, group_assignments, similar_pairs,
                              df, module_name, scenario):
        groups = {}
        for if_name, group_id in group_assignments.items():
            groups.setdefault(group_id, []).append(if_name)

        merged_if_names_cache = {}
        all_if_info = {}
        try:
            all_if_info = self.result_gen.ai_generator.generate_all_if_info(if_dict, df)
        except Exception:
            pass
        for group_id, group_members in groups.items():
            if len(group_members) > 1:
                try:
                    merged_if_names_cache[group_id] = \
                        self.result_gen.ai_generator.generate_merged_if_name(
                            group_members, if_dict, df)
                except Exception:
                    merged_if_names_cache[group_id] = \
                        self.result_gen.create_merged_if_name(sorted(group_members))

        output_rows = []
        for if_name in sorted(if_dict.keys()):
            if_info = if_dict[if_name]
            group_id = group_assignments[if_name]
            group_members = groups[group_id]
            merge_required = "○" if len(group_members) > 1 else "×"
            if if_name in all_if_info:
                if_summary = all_if_info[if_name].get("summary", "")
                representative_item = all_if_info[if_name].get(
                    "representative_item", if_info.representative_item)
            else:
                if_summary = ""
                representative_item = if_info.representative_item
            merged_if_name = merged_if_names_cache.get(
                group_id, self.result_gen.create_merged_if_name(sorted(group_members)))
            grouping_reason = self.result_gen.create_grouping_reason(
                if_name, group_members, similar_pairs)
            output_rows.append({
                "文書管理番号": if_info.doc_number,
                "IF名": if_name,
                "モジュール": module_name,
                "業務内容": scenario,
                "項目数": if_info.item_count,
                "IF概要": if_summary,
                "代表項目名": representative_item,
                "グルーピングID": group_id,
                "マージ要否": merge_required,
                "グルーピング後のIF名": merged_if_name,
                "グルーピングの根拠": grouping_reason,
            })
        return output_rows

    def _get_merged_if_names(self, if_dict, group_assignments, df):
        groups = {}
        for if_name, group_id in group_assignments.items():
            groups.setdefault(group_id, []).append(if_name)
        merged_if_names = {}
        for group_id, group_members in groups.items():
            if len(group_members) > 1:
                try:
                    merged_if_names[group_id] = \
                        self.result_gen.ai_generator.generate_merged_if_name(
                            group_members, if_dict, df)
                except Exception:
                    merged_if_names[group_id] = \
                        self.result_gen.create_merged_if_name(sorted(group_members))
        return merged_if_names
```

- [ ] **Step 2: 写 MergePage**

Create `ifmerge_gui/ui/pages/merge_page.py`:

```python
"""合并页。"""

from pathlib import Path
from typing import List

from ifmerge_gui.i18n import t
from ifmerge_gui.ui.pages.base_page import BasePage
from ifmerge_gui.ui.tasks.merge_task import MergeTask


class MergePage(BasePage):

    def run_button_text(self) -> str:
        return t("page.run_merge")

    def log_kind(self) -> str:
        return "merge"

    def output_dir(self) -> Path:
        return Path(self.app.settings.output_dir) / "merge"

    def create_task(self, files: List[Path]):
        return MergeTask(
            files=files, output_dir=self.output_dir(),
            threshold=self.app.settings.default_threshold,
            mode=self.app.settings.default_mode,
            settings=self.app.settings,
            on_progress=self._cb_progress, on_log=self._cb_log,
            on_done=self._cb_done, on_failed=self._cb_failed,
        )
```

- [ ] **Step 3: 提交**

```bash
git add ifmerge_gui/ui/tasks/merge_task.py ifmerge_gui/ui/pages/merge_page.py
git commit -m "feat(gui): add merge task (mirrors cli.py) and merge page"
```

---

### Task 7: 设置对话框 + 日志查看器

**Files:**
- Create: `ifmerge_gui/ui/dialogs/__init__.py`, `ifmerge_gui/ui/dialogs/settings_dialog.py`, `ifmerge_gui/ui/dialogs/log_viewer.py`

**Interfaces:**
- Consumes: `Settings`、`i18n`、`ebs_merger.ai_generator.AIGenerator`（用于测试连接）。
- Produces:
  - `SettingsDialog(master, settings: Settings, on_saved: Callable[[Settings], None])`（`CTkToplevel` 模态）。基本=AI Core Base URL + 测试连接；高级（折叠）=Auth URL/Client ID/Secret/Resource Group/Deployment ID、输出目录、阈值、模式、合并模板、日志级别；语言选择器调用 `master.set_language(code)`。
  - `LogViewerDialog(master, output_dir: Path)`（`CTkToplevel` 模态）。
- `master`（=`IFMergeApp`）须提供 `set_language(code: str)`（Task 8 实现）。

> Tk 对话框,无自动化测试;由导入冒烟 + 手动验证覆盖。

- [ ] **Step 1: 创建 dialogs 包标记**

Create `ifmerge_gui/ui/dialogs/__init__.py` — empty.

- [ ] **Step 2: 写 SettingsDialog**

Create `ifmerge_gui/ui/dialogs/settings_dialog.py`:

```python
"""设置对话框(CTkToplevel):精简项 + 折叠高级设置。"""

from tkinter import messagebox

import customtkinter as ctk

from ifmerge_gui.config.settings import Settings
from ifmerge_gui.i18n import AVAILABLE, t, translator


class SettingsDialog(ctk.CTkToplevel):

    def __init__(self, master, settings: Settings, on_saved):
        super().__init__(master)
        self.settings = settings
        self._on_saved = on_saved
        self.title(t("settings.title"))
        self.geometry("560x560")
        self.grab_set()
        self._advanced_visible = False
        self._build()

    def _row(self, parent, label, value, show=None):
        ctk.CTkLabel(parent, text=label, anchor="w",
                     text_color=("gray10", "gray90")).pack(fill="x", padx=12, pady=(8, 0))
        entry = ctk.CTkEntry(parent, show=show)
        entry.insert(0, value or "")
        entry.pack(fill="x", padx=12)
        return entry

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # 语言(改动即实时切换整个 UI)
        ctk.CTkLabel(scroll, text=t("settings.language"), anchor="w",
                     text_color=("gray10", "gray90")).pack(fill="x", padx=12, pady=(8, 0))
        self._lang_codes = list(AVAILABLE.keys())
        self._lang_names = list(AVAILABLE.values())
        self.opt_lang = ctk.CTkOptionMenu(
            scroll, values=self._lang_names, command=self._on_language_change)
        self.opt_lang.set(AVAILABLE[translator.current()])
        self.opt_lang.pack(fill="x", padx=12)

        # 基本:AI Core Base URL + 测试连接
        self.ed_base = self._row(scroll, t("settings.aicore_base_url"),
                                 self.settings.aicore_base_url)
        ctk.CTkButton(scroll, text=t("settings.test_conn"), command=self._test).pack(
            anchor="w", padx=12, pady=6)

        # 折叠高级
        self.btn_adv = ctk.CTkButton(scroll, text=t("settings.advanced_show"),
                                     fg_color="transparent", anchor="w",
                                     text_color=("gray10", "gray90"),
                                     hover_color=("gray80", "gray30"),
                                     command=self._toggle_advanced)
        self.btn_adv.pack(fill="x", padx=12, pady=(12, 0))
        self.adv = ctk.CTkFrame(scroll)
        self.ed_auth = self._row(self.adv, t("settings.aicore_auth_url"),
                                 self.settings.aicore_auth_url)
        self.ed_cid = self._row(self.adv, t("settings.aicore_client_id"),
                                self.settings.aicore_client_id)
        self.ed_secret = self._row(self.adv, t("settings.aicore_client_secret"),
                                   self.settings.aicore_client_secret, show="*")
        self.ed_rg = self._row(self.adv, t("settings.aicore_resource_group"),
                               self.settings.aicore_resource_group)
        self.ed_dep = self._row(self.adv, t("settings.aicore_deployment_id"),
                                self.settings.aicore_deployment_id)
        self.ed_output = self._row(self.adv, t("settings.output_dir"),
                                   self.settings.output_dir)
        self.ed_threshold = self._row(self.adv, t("settings.threshold"),
                                      str(self.settings.default_threshold))
        ctk.CTkLabel(self.adv, text=t("settings.mode"), anchor="w",
                     text_color=("gray10", "gray90")).pack(fill="x", padx=12, pady=(8, 0))
        self.ed_mode = ctk.CTkOptionMenu(self.adv, values=["max", "avg"])
        self.ed_mode.set(self.settings.default_mode)
        self.ed_mode.pack(fill="x", padx=12)
        self.ed_merged = self._row(self.adv, t("settings.merged_template"),
                                   self.settings.merged_template_path)
        self.ed_log = self._row(self.adv, t("settings.log_level"),
                                self.settings.log_level)

        # 按钮
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(btns, text=t("settings.save"), command=self._save).pack(
            side="right", padx=4)
        ctk.CTkButton(btns, text=t("settings.cancel"), command=self.destroy,
                      fg_color="gray").pack(side="right", padx=4)

    def _on_language_change(self, display_name: str):
        code = self._lang_codes[self._lang_names.index(display_name)]
        self.destroy()
        self.master.set_language(code)

    def _toggle_advanced(self):
        self._advanced_visible = not self._advanced_visible
        if self._advanced_visible:
            self.adv.pack(fill="x", padx=12, pady=6)
            self.btn_adv.configure(text=t("settings.advanced_hide"))
        else:
            self.adv.pack_forget()
            self.btn_adv.configure(text=t("settings.advanced_show"))

    def _test(self):
        from ebs_merger.ai_generator import AIGenerator
        try:
            gen = AIGenerator(
                auth_url=self.ed_auth.get() or None,
                client_id=self.ed_cid.get() or None,
                client_secret=self.ed_secret.get() or None,
                base_url=self.ed_base.get() or None,
                resource_group=self.ed_rg.get() or "default",
                deployment_id=self.ed_dep.get() or None,
            )
            gen._get_access_token()
            messagebox.showinfo(t("settings.test_conn"), t("settings.test_ok"))
        except Exception as e:
            messagebox.showwarning(t("settings.test_conn"),
                                   t("settings.test_fail", error=e))

    def _save(self):
        s = self.settings
        s.aicore_base_url = self.ed_base.get()
        s.aicore_auth_url = self.ed_auth.get()
        s.aicore_client_id = self.ed_cid.get()
        s.aicore_client_secret = self.ed_secret.get()
        s.aicore_resource_group = self.ed_rg.get()
        s.aicore_deployment_id = self.ed_dep.get()
        s.output_dir = self.ed_output.get()
        s.default_threshold = float(self.ed_threshold.get())
        s.default_mode = self.ed_mode.get()
        s.merged_template_path = self.ed_merged.get()
        s.log_level = self.ed_log.get()
        self._on_saved(s)
        self.destroy()
```

- [ ] **Step 3: 写 LogViewerDialog**

Create `ifmerge_gui/ui/dialogs/log_viewer.py`:

```python
"""日志查看器:列出 output/parse/logs 与 output/merge/logs 下的 *.log 并查看。"""

from pathlib import Path

import customtkinter as ctk

from ifmerge_gui.i18n import t


class LogViewerDialog(ctk.CTkToplevel):

    def __init__(self, master, output_dir: Path):
        super().__init__(master)
        self.title(t("logviewer.title"))
        self.geometry("840x560")
        self.grab_set()
        base = Path(output_dir)
        self._dirs = [base / "parse" / "logs", base / "merge" / "logs"]
        self._files = self._scan()
        self._build()

    def _scan(self) -> list[Path]:
        files: list[Path] = []
        for d in self._dirs:
            if d.is_dir():
                files.extend(d.glob("*.log"))
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkScrollableFrame(self, width=280, label_text=t("logviewer.history"))
        left.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.text = ctk.CTkTextbox(self)
        self.text.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)
        self.text.configure(state="disabled")

        if not self._files:
            ctk.CTkLabel(left, text=t("logviewer.empty"), text_color="gray").pack(pady=8)
            return
        for p in self._files:
            ctk.CTkButton(left, text=p.name, anchor="w", fg_color="transparent",
                          text_color=("gray10", "gray90"),
                          hover_color=("gray80", "gray30"),
                          command=lambda fp=p: self._show(fp)).pack(fill="x", pady=2)
        self._show(self._files[0])

    def _show(self, path: Path):
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            content = t("logviewer.read_fail", error=e)
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", content)
        self.text.configure(state="disabled")
```

- [ ] **Step 4: 提交**

```bash
git add ifmerge_gui/ui/dialogs/
git commit -m "feat(gui): add settings dialog and log viewer"
```

---

### Task 8: 主窗口 + 入口 + 导入冒烟 + 手动验证

**Files:**
- Create: `ifmerge_gui/ui/app.py`, `ifmerge_gui/__main__.py`, `main.py`
- Test: `tests/test_gui_imports.py`

**Interfaces:**
- Consumes: `Settings`、`setup_logger`、`AnalyzePage`、`MergePage`、`SettingsDialog`、`LogViewerDialog`、`i18n`。
- Produces: `IFMergeApp(ctk.CTk)`，方法 `show_page(name)`、`set_language(lang)`（设置对话框语言切换回调）、`_on_settings_saved(settings)`；`ifmerge_gui.__main__.main()`。

- [ ] **Step 1: 写 app.py**

Create `ifmerge_gui/ui/app.py`:

```python
"""CTk 主应用:侧栏导航(解析/合并)+ 页面切换 + 日志 + 设置入口。"""

import logging
from pathlib import Path

import customtkinter as ctk

from ifmerge_gui.config.settings import Settings
from ifmerge_gui.i18n import t, translator
from ifmerge_gui.ui.dialogs.log_viewer import LogViewerDialog
from ifmerge_gui.ui.dialogs.settings_dialog import SettingsDialog
from ifmerge_gui.ui.pages.analyze_page import AnalyzePage
from ifmerge_gui.ui.pages.merge_page import MergePage
from ifmerge_gui.utils.logger import setup_logger

logger = logging.getLogger("ifmerge_gui.ui.app")


class IFMergeApp(ctk.CTk):

    _NAV_ACTIVE = ("#1f6aa5", "#1f6aa5")
    _NAV_INACTIVE = ("gray75", "gray30")

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings

        self.title(t("app.title"))
        self.geometry("1100x720")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._current_page = "analyze"
        self._build_sidebar()
        self._build_pages()
        self.show_page("analyze")

    def _build_sidebar(self):
        bar = ctk.CTkFrame(self, width=160, corner_radius=0)
        bar.grid(row=0, column=0, sticky="nsew")
        bar.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(bar, text="IFmerge", font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=0, padx=16, pady=(16, 12))
        self.btn_analyze = ctk.CTkButton(bar, text=t("sidebar.analyze"),
                                         command=lambda: self.show_page("analyze"))
        self.btn_analyze.grid(row=1, column=0, padx=16, pady=6, sticky="ew")
        self.btn_merge = ctk.CTkButton(bar, text=t("sidebar.merge"),
                                       command=lambda: self.show_page("merge"))
        self.btn_merge.grid(row=2, column=0, padx=16, pady=6, sticky="ew")

        ctk.CTkButton(bar, text=t("sidebar.logs"), fg_color="gray",
                      command=self._open_logs
                      ).grid(row=4, column=0, padx=16, pady=(16, 4), sticky="ew")
        ctk.CTkButton(bar, text=t("sidebar.settings"), fg_color="gray",
                      command=self._open_settings
                      ).grid(row=5, column=0, padx=16, pady=(4, 16), sticky="ew")

    def _build_pages(self):
        self.pages = {
            "analyze": AnalyzePage(self, self),
            "merge": MergePage(self, self),
        }

    def show_page(self, name: str):
        self._current_page = name
        for p in self.pages.values():
            p.grid_forget()
        self.pages[name].grid(row=0, column=1, sticky="nsew")
        self._highlight_nav(name)

    def set_language(self, lang: str):
        """切换语言:持久化 + 实时重建侧栏/页面(当前选择/进度会清空)。"""
        translator.set_language(lang)
        for child in self.winfo_children():
            child.destroy()
        self.title(t("app.title"))
        self._build_sidebar()
        self._build_pages()
        self.show_page(self._current_page)

    def _highlight_nav(self, name: str):
        buttons = {"analyze": self.btn_analyze, "merge": self.btn_merge}
        for key, btn in buttons.items():
            btn.configure(fg_color=self._NAV_ACTIVE if key == name
                          else self._NAV_INACTIVE)

    def _open_logs(self):
        LogViewerDialog(self, Path(self.settings.output_dir))

    def _open_settings(self):
        SettingsDialog(self, self.settings, on_saved=self._on_settings_saved)

    def _on_settings_saved(self, settings: Settings):
        self.settings = settings
        self.settings.save()                            # 持久化到 .env
        setup_logger(level=self.settings.log_level)      # 日志级别即时生效
        self.pages["analyze"].file_output.set_output_dir(
            self.pages["analyze"].output_dir())
        self.pages["merge"].file_output.set_output_dir(
            self.pages["merge"].output_dir())
```

- [ ] **Step 2: 写 __main__.py**

Create `ifmerge_gui/__main__.py`:

```python
"""IFmerge GUI 程序入口:python -m ifmerge_gui"""

from ifmerge_gui.config.settings import Settings
from ifmerge_gui.ui.app import IFMergeApp
from ifmerge_gui.utils.logger import setup_logger


def main():
    settings = Settings.load()
    setup_logger(level=settings.log_level)
    app = IFMergeApp(settings)
    app.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 写 main.py**

Create `main.py` (仓库根):

```python
"""根目录便捷启动脚本。等价于 `python -m ifmerge_gui`。"""

from ifmerge_gui.__main__ import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 写导入冒烟测试**

Create `tests/test_gui_imports.py`:

```python
"""导入冒烟:确保所有 GUI 模块可 import(捕获语法/导入错误)。

注意:仅 import,不实例化任何 Tk 对象(环境可能无显示)。
"""

import importlib

import pytest

MODULES = [
    "ifmerge_gui.config.settings",
    "ifmerge_gui.utils.logger",
    "ifmerge_gui.i18n",
    "ifmerge_gui.ui.utils.fs",
    "ifmerge_gui.core.ai_factory",
    "ifmerge_gui.ui.widgets.file_input",
    "ifmerge_gui.ui.widgets.file_output",
    "ifmerge_gui.ui.widgets.progress_log",
    "ifmerge_gui.ui.pages.base_page",
    "ifmerge_gui.ui.tasks.analyze_task",
    "ifmerge_gui.ui.pages.analyze_page",
    "ifmerge_gui.ui.tasks.merge_task",
    "ifmerge_gui.ui.pages.merge_page",
    "ifmerge_gui.ui.dialogs.settings_dialog",
    "ifmerge_gui.ui.dialogs.log_viewer",
    "ifmerge_gui.ui.app",
    "ifmerge_gui.__main__",
]


@pytest.mark.parametrize("mod", MODULES)
def test_import(mod):
    importlib.import_module(mod)
```

- [ ] **Step 5: 运行导入冒烟，确认通过**

Run: `python -m pytest tests/test_gui_imports.py -v`
Expected: PASS（17 passed）。

> 若失败：常见为 customtkinter 未安装（`pip install "customtkinter>=5.2.0"`），或 import 链有拼写错误——按 traceback 修正。`import customtkinter` 本身不需要显示器。

- [ ] **Step 6: 跑全部测试**

Run: `python -m pytest tests/test_gui_settings.py tests/test_gui_i18n.py tests/test_gui_fs.py tests/test_gui_ai_factory.py tests/test_gui_imports.py -v`
Expected: 全部 PASS。

- [ ] **Step 7: 手动启动验证（需图形界面环境）**

Run: `python -m ifmerge_gui`

逐项确认（参照参考工程外观）：
1. 窗口标题为「IFmerge — …」，左侧导航有「▶ 解析」「▶ 合并」「📜 日志」「⚙ 设置」，解析按钮高亮蓝色。
2. 点「合并」→ 切到合并页且按钮高亮切换；点「解析」切回。
3. 解析页点「📁 选择文件夹」选 `input/`，含 `.xlsx` 时「▶ 开始解析」由禁用变可用；输出区显示 `输出: output/parse`。
4. 点「⚙ 设置」→ 弹模态框；展开「▸ 高级设置」可见 Auth URL/Client ID/Secret/RG/Deployment ID/输出目录/阈值/模式/合并模板/日志级别；语言切到「日本語」→ 整个 UI 实时变日文；切回「中文」。
5. （有真实 AI Core 凭据时）设置里填好 Base URL 等，点「测试连接」→ 成功弹「✓ 连接成功」，错误凭据弹「✗ 连接失败: …」。
6. （有凭据 + input 有 `.xlsx`）解析页点「开始解析」→ 进度条推进、日志逐行刷新、结束显示「✓ 完成」，`output/parse/解析結果.xlsx` 与 `output/parse/logs/parse_*.log` 生成。
7. 合并页同样跑通 → `output/merge/<文件名>/グルーピング結果.xlsx`、模块子文件夹下 `類似度マトリックス_*.xlsx` 与填充模板 `.xlsm` 生成。
8. 运行中点「取消」→ 在下一个文件/模块边界停止，按钮恢复。
9. 点「📜 日志」→ 列出历史 `.log`，点击可在右侧查看内容。

若无图形环境，记录「手动验证待业务侧执行」并把第 5 步起的清单写入 PR 描述。

- [ ] **Step 8: 提交**

```bash
git add ifmerge_gui/ui/app.py ifmerge_gui/__main__.py main.py tests/test_gui_imports.py
git commit -m "feat(gui): add main window, entry points and import smoke test"
```

---

## Self-Review

**1. Spec coverage（对照 `2026-06-17-ifmerge-gui-design.md`）：**
- §2 总体架构 / 目录结构 → Task 1-8 完整建出镜像结构。✓
- §3 主窗口与导航 → Task 8 app.py。✓
- §4.1 解析页映射（load→group→classify→gen_info→解析結果.xlsx）→ Task 5。✓
- §4.2 合并页完整流水线（grouping/matrix/template）→ Task 6（镜像 cli.py）。✓
- §4.3 取消与异常（边界检查、单文件失败不中断、on_failed）→ Task 5/6 run() + _process_file try/except。✓
- §5 线程编排契约（BasePage + _cb_*）→ Task 4。✓
- §6 配置与设定弹窗（AICORE_* + 阈值/模式/模板/日志级别 + 语言 + 测试连接）→ Task 1 Settings + Task 7 SettingsDialog。✓
- §7 日志查看器 → Task 7。✓
- §8 i18n zh/ja/en 默认 zh → Task 2。✓
- §9 启动方式 python -m ifmerge_gui / main.py → Task 8。✓
- §10 YAGNI（不动 ebs_merger、不复用中间产物、无在线预览）→ 全程遵守；合并 per-file 子目录是对 cli.py 覆盖 quirk 的安全改良，已在 Task 6 注明。✓
- §11 测试（Settings/i18n/fs round-trip + 手动验证）→ Task 1/2/3/5 单测 + Task 8 导入冒烟 + 手动清单。✓
- 说明：设计书 §2 曾列 `ui/utils/phase_text.py`；实现改为在 task 内直接用 `t("phase.*")` 本地化串（无后端 phase 代码需正则翻译），属 YAGNI 简化，phase_text 模块不再需要。

**2. Placeholder scan：** 无 TBD/TODO；每个代码步骤含完整代码；测试步骤含完整断言与命令。✓

**3. Type consistency：**
- `Settings` 字段名在 Task 1 定义，Task 5/6/7/8 引用一致（`default_threshold`/`default_mode`/`aicore_*`/`merged_template_path`/`output_dir`）。✓
- 回调签名 `on_progress/on_log/on_done/on_failed` 在 BasePage(Task4)、AnalyzeTask(Task5)、MergeTask(Task6)、页面 create_task 一致。✓
- `build_ai_generator(settings)` 在 Task 5 定义，Task 5/6 使用一致。✓
- `set_language(code)` 由 SettingsDialog(Task7) 调用、IFMergeApp(Task8) 实现一致。✓
- ebs_merger 调用签名核对：`DataLoader.load_excel(str)`、`IFGrouper.group_by_if(df)`、`AIClassifier(ai_generator=).classify_interfaces(if_dict, df)`、`AIGenerator.generate_all_if_info(if_dict, df)` / `.generate_merged_if_name(members, if_dict, df)` / `._get_access_token()`、`SimilarityCalculator.build_similarity_matrix(if_dict, threshold, mode)` / `.build_full_similarity_matrix(if_dict, mode)`、`MergeGrouper.group_similar_ifs(if_dict, similar_pairs)`、`ResultGenerator(use_ai=True).create_merged_if_name/create_grouping_reason`、`TemplateFiller(template_path=).fill_merged_groups(if_dict, group_assignments, similar_pairs, df, output_dir, merged_if_names)`、`MatrixExporter.export_module_matrices(module_data, path, module_name)` —— 均与源码一致。✓
