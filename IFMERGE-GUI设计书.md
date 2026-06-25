# IFMERGE-GUI 设计书

> 版本：v1.0
> 工程路径：`/data/HuangCX/IFmerge/`（分支 `feat/desktop-gui`）
> 编写日期：2026-06-25
> 参考：本社既存设计书 `/data/HuangCX/ifmerge-gui/IFMERGE-GUI设计书.md`（CAP 客户端版 v2.0）

---

## 1. 概述

本地桌面端,作为既存 CLI 工具 `ebs_merger`（EBS 接口设计书合并工具）的图形外壳。**单一「合并」功能**,把命令行 `EBSMergerCLI.run()` 的批处理流程包进一个 CustomTkinter 窗口。

**职责**：选含**抽出結果 Excel**(8 列)的文件夹 → 进程内调用 `ebs_merger` 各组件(读取 → IF 分组 → AI 分类 → 相似度计算 → 合并分组 → AI 命名 → 输出)→ 直连 **SAP AI Core** 做 LLM 推理 → 产出グルーピング結果 / 類似度マトリックス / 合并模板 xlsm。

**与本社参考工程(`ifmerge-gui`)的本质区别**：

| 维度 | 参考工程 `ifmerge-gui` | 本工程 `IFmerge` |
|---|---|---|
| 功能页 | 解析 + 合并 双页 | **仅合并**,单页(侧栏无导航按钮) |
| 后端 | 远程 **CAP REST** 服务,HTTP 轮询 Job | **进程内**直接调用 `ebs_merger` 组件,无服务器/HTTP |
| LLM | 经 CAP 后端,模型由后端 deployment 决定 | **GUI 直连 SAP AI Core**(converse API + tool calling) |
| 解析 | GUI 内做(调 `/analyze`) | 不做。本工程输入即抽出結果 Excel |
| 输出布局 | `output/merge/` 扁平 | **按源文件名分区**:`output/merge/<源文件名>/...` |
| 提示词 | 后端固化 | 前端可配置(`prompts.yaml`,见 §7.4) |

**技术栈**：

| 项 | 选择 |
|---|---|
| 语言 | Python 3.10+ |
| UI 框架 | **CustomTkinter ≥ 5.2** |
| 后台并发 | **`threading.Thread` + 回调**(经 `widget.after()` 调度回主线程) |
| Excel 读写 | openpyxl ≥ 3.1(**仅 `.xlsx`**) + pandas ≥ 2.0 |
| LLM | requests 直连 SAP AI Core(`/inference/deployments/{id}/converse`) |
| 配置 | python-dotenv(`.env`)+ PyYAML(`prompts.yaml`) |
| 多语言 | 自研轻量 i18n(JSON locale,中/日/英,默认中文) |

> 核心层(`ebs_merger/` 全包:data_loader/if_grouper/ai_classifier/similarity_calculator/merge_grouper/result_generator/ai_generator/matrix_exporter/template_filler/cli)**本次零改动**;GUI 仅在 `ifmerge_gui/` 内新增,并在 `MergeTask` 里**重新编排**(镜像自 `ebs_merger/cli.py`),不复用 `EBSMergerCLI`,以便穿插进度/取消/日志回调。

---

## 2. 项目结构

```
IFmerge/
├── main.py                                ← 便捷入口(= python -m ifmerge_gui)
├── requirements.txt                       ← 追加 customtkinter>=5.2
├── .env / .env.example                    ← AI Core 凭证、路径、算法默认(设置弹窗写回这里)
├── prompts.yaml                           ← 可配置 AI 提示词模板(缺失则回退硬编码)
│
├── ifmerge_gui/                           ← 新增 GUI 包
│   ├── __main__.py                        入口:Settings.load → setup_logger → IFMergeApp.mainloop
│   │
│   ├── i18n/                              ← 多语言
│   │   ├── __init__.py                    Translator 单例 + 模块级 t()
│   │   └── locales/{zh,ja,en}.json        key → 文本(三语 key 一致,81 个)
│   │
│   ├── ui/                                ← CustomTkinter 界面层
│   │   ├── app.py                         IFMergeApp:侧栏(品牌 + 日志 + 设置)+ 合并页 + set_language
│   │   ├── pages/
│   │   │   ├── base_page.py               通用页(四行块 + 线程回调经 after 调度 + 日志落盘)
│   │   │   └── merge_page.py              合并页(绑定 MergeTask 与 output/merge)
│   │   ├── widgets/
│   │   │   ├── file_input.py              文件夹选择(递归找 .xlsx)
│   │   │   ├── file_output.py             输出路径 + 打开文件夹
│   │   │   └── progress_log.py            进度条(0–1) + 阶段标签 + 滚动日志框
│   │   ├── dialogs/
│   │   │   ├── settings_dialog.py         设置(CTkToplevel,精简 + 折叠高级 + 语言)
│   │   │   └── log_viewer.py              历史执行日志查看器
│   │   ├── tasks/
│   │   │   └── merge_task.py              合并后台任务(threading,编排镜像自 cli.py)
│   │   └── utils/
│   │       └── fs.py                      递归扫描 .xlsx + 跨平台打开文件夹
│   │
│   ├── core/
│   │   └── ai_factory.py                  build_ai_generator(settings):用 GUI 设置显式构造 AIGenerator
│   │
│   ├── config/settings.py                 .env 加载 + 写回(固定仓库根 .env)
│   └── utils/logger.py                    控制台 + 文件双输出 logger
│
├── ebs_merger/                            ← 既存核心逻辑(本次不修改)
│   ├── cli.py                             EBSMergerCLI(命令行批处理,GUI 编排的参照基准)
│   ├── data_loader.py                     读 .xlsx + 校验 8 必需列
│   ├── if_grouper.py                      按 IF名 分组 → IFInfo(field_pairs 等)
│   ├── ai_classifier.py                   AI 按 SAPモジュール/業務シナリオ 分类
│   ├── similarity_calculator.py           字段对相似度(max / avg)
│   ├── merge_grouper.py                   Union-Find 合并分组
│   ├── result_generator.py               グルーピング結果 行/根拠 生成
│   ├── ai_generator.py                    SAP AI Core 客户端(converse + tool calling)
│   ├── matrix_exporter.py                類似度マトリックス Excel
│   ├── template_filler.py                合并模板 xlsm(keep_vba)
│   └── prompt_config.py                   读取 prompts.yaml
│
├── template/IF_Template.xlsm              ← 合并模板(含 VBA)
├── input/                                 ← 默认输入文件夹
├── output/                                ← 默认输出(见 §8.3)
├── bat/                                   ← Windows 启动/安装脚本
└── docs/superpowers/{specs,plans}/        ← 设计/实现记录
```

> 与参考工程的结构差异:**无** `ui/pages/analyze_page.py`、`ui/tasks/analyze_task.py`、`ui/utils/phase_text.py`、`api/`(无 CAP 客户端);**新增** `core/ai_factory.py`(把 GUI 设置注入 `ebs_merger.AIGenerator`)。阶段文本不经独立的 `phase_text` 模块,直接走 `t("phase.*")`。

---

## 3. 布局

### 3.1 主窗口(侧栏 + 右侧四行块)

```
┌─────────────┬──────────────────────────────────────────────┐
│  IFmerge     │  ┌── 文件输入 ─────────────────────────────┐ │
│             │  │ 📁 选择文件夹   📁 C:\...\input            │ │
│             │  └─────────────────────────────────────────┘ │
│             │  ┌── 文件输出 ─────────────────────────────┐ │
│             │  │ 📂 打开文件夹   输出: output\merge         │ │
│             │  └─────────────────────────────────────────┘ │
│             │  ┌── 执行 ─────────────────────────────────┐ │
│             │  │ [▶ 开始合并]          [取消]               │ │
│             │  └─────────────────────────────────────────┘ │
│             │  ┌── 进度 / 日志 ──────────────────────────┐ │
│             │  │ ▓▓▓▓▓▓░░░░ 60% [2/3] 相似度计算          │ │
│  📜 日志     │  │ ──────────────────────────────────────── │ │
│  ⚙ 设置      │  │ [1/3] 正在处理文件: a.xlsx ...            │ │
│             │  └─────────────────────────────────────────┘ │
└─────────────┴──────────────────────────────────────────────┘
```

- **左侧栏(160px)**:品牌名「IFmerge」+ 底部「📜 日志」「⚙ 设置」两个灰色按钮。**因仅合并一页,侧栏无页面导航按钮**(与参考工程的「▶ 解析 / ▶ 合并」不同)。
- **右侧**:自上而下四个横向行块 —— 文件输入 / 文件输出 / 执行 / 进度·日志。
- **无结果预览**:结果只落地为 Excel,用「打开文件夹」查看。

### 3.2 窗口尺寸

| 项 | 值 |
|---|---|
| 初始尺寸 | 1100 × 720(`app.py: geometry`) |
| 外观主题 | 跟随系统(CustomTkinter 默认,亮/暗自适应,文字颜色 `("gray10","gray90")` 双色) |
| 设置弹窗 | 560 × 560(模态 `grab_set`) |
| 日志查看器 | 840 × 560(模态) |

---

## 4. 界面组件设计

### 4.1 FileInput（widget,文件输入块）

| 控件 | 行为 |
|---|---|
| 「📁 选择文件夹」按钮 | `tkinter.filedialog.askdirectory` 选文件夹 |
| 路径标签 | 显示所选文件夹(未选时显示「未选择」) |

选中后**递归扫描**该文件夹及子目录下全部 `*.xlsx`(`fs.find_excel_files`,跳过 `~$` 临时锁文件),归一为 `list[Path]` 经 `on_change` 回调上报 `BasePage`;有文件时启用「开始合并」按钮。
> 注:`EXCEL_SUFFIXES = {".xlsx"}`,与 `ebs_merger.DataLoader`(openpyxl 引擎)一致,**不收 `.xls/.xlsm`**。tkinter 原生对话框无法同时选文件夹与文件,故只保留文件夹选择。

### 4.2 FileOutput（widget,文件输出块）

显示合并页输出目录(`output/merge`)+「📂 打开文件夹」按钮(跨平台:Windows `os.startfile` / macOS `open` / Linux `xdg-open`;目录不存在则先创建)。设置里改了输出目录,保存后 `app._on_settings_saved` 会刷新此标签。

### 4.3 ProgressLog（widget,进度/日志块）

| 控件 | 说明 |
|---|---|
| 进度条 | `CTkProgressBar`,值域 **0.0–1.0**(后台传 0–100,`set_progress` 除以 100) |
| 阶段标签 | 显示 `[idx/total] <阶段文本>`(宽 180,左对齐) |
| 日志框 | `CTkTextbox`(高 160),只读、只追加,自动滚到底 |

状态:待机 / ✓ 完成 / ✗ 失败,均通过 `t()` 本地化。

### 4.4 SettingsDialog（CTkToplevel）

| 区 | 项 | 控件 | 说明 |
|---|---|---|---|
| **主区** | 语言 / Language | `CTkOptionMenu` | 中文 / 日本語 / English,**选中即实时切换**(关闭弹窗后重建 UI) |
|  | AI Core Base URL | `CTkEntry` | |
|  | 测试连接 | `CTkButton` | 构造 `AIGenerator` 并调 `_get_access_token()`,弹消息框 |
| **折叠「高级设置」** | AI Core Auth URL / Client ID / Client Secret(密文) / Resource Group / Deployment ID | `CTkEntry` | SAP AI Core 凭证 |
|  | 输出目录 | `CTkEntry` | |
|  | 相似度阈值(0.5–1.0) | `CTkEntry` | |
|  | 相似度模式 | `CTkOptionMenu` | `max` / `avg` |
|  | 合并模板 xlsm / 日志级别 | `CTkEntry` | |
| **底部** | 保存 / 取消 | `CTkButton` | |

- **保存即持久化**:`_save` → `app._on_settings_saved` → `Settings.save()` 用 `dotenv.set_key` 逐键写回**仓库根 `.env`**(固定路径,见 §9),并重调 `setup_logger(level=...)` 使日志级别即时生效、刷新输出目录标签。
- **无「大模型选择」**:模型由 `AICORE_DEPLOYMENT_ID`(或 `AICORE_MODEL_NAME` 动态解析,见 §7.3)决定,前端不暴露独立的模型下拉。

### 4.5 LogViewerDialog（CTkToplevel,侧栏「📜 日志」）

扫描 `output/parse/logs/` 与 `output/merge/logs/` 下的 `*.log`,按修改时间倒序在左列列出,点击在右侧只读查看。每次合并执行结束(成功/失败/取消)由 `BasePage._save_log` 把本次完整日志写入 `output/merge/logs/merge_<YYYYmmdd_HHMMSS>.log`。
> 说明:查看器仍兼容扫描 `parse/logs`,但本工程无解析页,实际只会产出 `merge/logs`。

---

## 5. 线程模型

### 5.1 总体结构

CustomTkinter / tkinter **非线程安全**,后台线程不得直接操作控件。

```
┌────────── Main UI Thread (Tk mainloop) ──────────┐
│  渲染界面 / 响应操作 / 经 after() 应用回调结果       │
└──────────────┬─────────────────────────────────────┘
               │ task.start()
               ▼
   ┌──────────────────────────────────────────┐
   │  MergeTask (threading.Thread, daemon)      │
   │  ────────────────────────────────────────  │
   │  进程内调用 ebs_merger 组件 + 直连 AI Core, │
   │  通过回调上报:                              │
   │   on_progress(percent, phase)              │
   │   on_log(msg)                              │
   │   on_done(result) / on_failed(exc)         │
   └──────────────────────────────────────────┘
```

- **回调封送**:`BasePage` 的 `_cb_progress/_cb_log/_cb_done/_cb_failed` 内部统一 `self.after(0, lambda: …)`,把全部 UI 更新调度回主线程。
- **进度换算**:后台传 0–100,`ProgressLog.set_progress` 除以 100 适配 `CTkProgressBar` 的 0.0–1.0。进度以「文件 idx/total」为基准(`base = (idx-1)/total*100`),阶段文本叠加当前子阶段。
- **取消**:`MergeTask._cancel` 标志,`cancel()` 置位;在**每文件 / 每模块 / 每场景**循环起点检查,命中则记「已被用户取消」并 `on_done(None)` 收尾(不报错)。**注意:AI 调用为同步阻塞,取消粒度到「下一个文件/模块/场景」之间,无法中断进行中的单次 AI 请求**。
- **单文件失败不中断整批**:与 `cli.py` 一致 —— `_process_file` 抛异常则计入失败数、记日志、继续下个文件;只有任务级(组件初始化、AI 凭证缺失等)异常才走 `on_failed`。

### 5.2 任务回调

| 回调 | 参数 | 用途 |
|---|---|---|
| `on_progress` | `(int percent, str phase)` | 进度条 + 阶段标签 |
| `on_log` | `(str message)` | 日志框追加(并累积,结束时落盘) |
| `on_done` | `(result=None)` | 标记完成、保存日志、恢复按钮 |
| `on_failed` | `(Exception)` | 标记失败、记录 `✗ 失败: <类型>: <消息>`、保存日志 |

### 5.3 并发控制

| 规则 | 实现 |
|---|---|
| 运行中禁用「开始」、启用「取消」、禁用文件选择 | `BasePage._set_running` |
| 主线程不阻塞 | 所有 Excel/AI 调用在 Thread 内 |
| 切换语言会重建 UI | 清空当前已选文件/进度(已知取舍) |

---

## 6. 错误处理

### 6.1 错误分类与 UI 行为

| 错误类型 | 触发 | UI 行为 |
|---|---|---|
| **文件错误** | Excel 损坏 / 空文件 | `DataLoader` 抛 `ValueError` → 单文件失败计数,日志追加,继续下个文件 |
| **缺必需列** | 选的不是抽出結果 Excel | `validate_columns` 抛「缺少以下必需列:…」(8 列校验) |
| **AI 凭证缺失** | `.env` 未配 AICORE_* | `AIGenerator.__init__` 抛 `ValueError` → 任务级 `on_failed`,日志红字 |
| **AI 连接/认证失败** | token 获取失败 / 网络 | `_get_access_token` / converse 抛 `Exception` |
| **AI 内容生成失败** | LLM 未调用工具 / 超时 | 内部 `try/except` 降级:回退 `create_merged_if_name`(下划线连接)、IF概要留空,**不中断流程** |
| **AI 分类失败** | converse 异常 | 降级为单一分类「その他_未分類」(全 IF 归一类) |
| **模板缺失** | `template/IF_Template.xlsm` 不存在 | `TemplateFiller` 抛异常 → 单文件失败 |

### 6.2 降级与取消

- AI 三处调用(分类 / IF信息 / 合并命名)均包 `try/except` 并有确定性回退,保证「AI 不可用时仍能产出分组结果」。
- 测试连接独立于主流程,仅验证凭证可达。
- 任务级失败统一走 `on_failed` → 日志追加 `✗ 失败: <类型>: <消息>` 并落盘。

---

## 7. AI(SAP AI Core)映射

### 7.1 用户操作 → AI Core 调用

| GUI 动作 | HTTP 调用 |
|---|---|
| 测试连接 | `POST {auth_url}/oauth/token`(client_credentials 取 token) |
| AI 分类 | `POST {base_url}/inference/deployments/{id}/converse`(`classify_interfaces` 工具) |
| 生成 IF 概要/代表项目 | 同上(`generate_all_if_info` 工具) |
| 生成合并后 IF 名 | 同上(`generate_merged_name` 工具) |
| (可选)按模型名解析 deployment | `GET {base_url}/lm/deployments?status=RUNNING` |

### 7.2 合并数据流(MergeTask,镜像 cli.py)

```
build_ai_generator(settings)            # 用 GUI 设置构造 AIGenerator,注入到 ResultGenerator/AIClassifier
└─ 逐 Excel 文件:
   1. DataLoader.load_excel            → df(校验 8 列)
   2. IFGrouper.group_by_if            → if_dict {IF名: IFInfo}
   3. AIClassifier.classify_interfaces → categories {模块_场景: (module, scenario, [IF名])}
   4. 按模块整理                       → {module: {scenario: (cat, if_dict, df)}}
   5. 逐模块、逐场景:
      a. SimilarityCalculator.build_similarity_matrix(>= threshold)   → similar_pairs
      b. build_full_similarity_matrix(全对,供矩阵)                   → all_pairs
      c. MergeGrouper.group_similar_ifs(Union-Find)                   → groups
      d. 连番分配グルーピングID(模块前缀,如 FI001,模块内递增)
      e. 生成输出行(AI: generate_all_if_info / generate_merged_if_name,失败回退)
      f. TemplateFiller.fill_merged_groups → 每个 size>1 的组 1 个 .xlsm
      g. 模块级 MatrixExporter.export_module_matrices → 類似度マトリックス_<module>.xlsx
   6. 写 グルーピング結果.xlsx(本源文件汇总,12 列)
```

**核心数据模型 `IFInfo`**(`if_grouper.py`):`if_name / doc_number(文書管理番号) / field_pairs: Set[(EBSテーブルID, 項目ID)] / item_count / representative_item`。

### 7.3 相似度算法(`similarity_calculator.py`)

- 特征 = `field_pairs`(去空白、去空值的 `(EBSテーブルID, 項目ID)` 集合)。
- `mode="max"`:`共通対数 / min(対数1, 対数2)`(默认)。
- `mode="avg"`:`(共通/対数1 + 共通/対数2) / 2`(双向一致率平均)。
- 默认阈值 `threshold = 0.8`;`>= threshold` 的对进入分组。
- **合并分组**:`MergeGrouper` 用 Union-Find 传递性合并(路径压缩 + 按秩合并)。`マージ要否 = ○`(组 size>1)/ `×`(独立)。
- **矩阵**:`build_full_similarity_matrix` 输出全部 IF 对(含 0),`MatrixExporter` 另算定向相似度(以各自字段数为分母)。

### 7.4 AI 调用与提示词

- **协议**:converse API + tool calling,`toolChoice: {any:{}}` 强制模型调用工具;`temperature=0.7`、`maxTokens=8192`。
- **三个工具**:`classify_interfaces`(模块+场景+IF列表)、`generate_all_if_info`(各 IF 概要 30–50 字 + 约 20% 代表项目)、`generate_merged_name`(合并后 IF 名 20–40 字)。
- **可配置提示词**:`PromptConfig` 读仓库根 `prompts.yaml`;命中 `classify_interfaces / generate_all_if_info / generate_merged_if_name` 模板则用之(`str.format_map` 注入 `if_info_block` 等占位符),**缺失或格式化失败则回退硬编码提示词**。
- **模型不在前端选择**:由 `AICORE_DEPLOYMENT_ID` 指定;若配 `AICORE_MODEL_NAME`,则 `_resolve_deployment_id` 调 `/lm/deployments` 动态解析 RUNNING deployment(失败回退 `AICORE_DEPLOYMENT_ID`)。

### 7.5 鉴权

`AIGenerator`:`client_credentials`(`auth=(client_id, client_secret)`)取 token 缓存于实例;每次 converse 带 `Authorization: Bearer` + `AI-Resource-Group`。凭证来自设置(`.env`,见 §9),由 `core/ai_factory.build_ai_generator` 把 GUI `Settings` 显式传入(使设置成为权威来源;空值传 `None` 则 `AIGenerator` 回退环境变量)。

---

## 8. Excel 格式

### 8.1 输入

| 项 | 要求 |
|---|---|
| 扩展名 | **仅 `.xlsx`**(openpyxl) |
| 输入 | 含**抽出結果 Excel** 的文件夹(递归,跳过 `~$`) |
| 必需列(8) | `No., 文書管理番号, IF名, EBSテーブル名, EBSテーブルID, 項目ID, 項目名, 桁数` |
| 校验 | 缺任一列即抛错(`DataLoader.validate_columns`);空文件抛错 |

### 8.2 输出产物(3 类)

| # | 产物 | 文件 | 复用代码 |
|---|---|---|---|
| ① | グルーピング結果 Excel | `output/merge/<源文件名>/グルーピング結果.xlsx`(每源文件 1 个,12 列) | `merge_task.py`(行) |
| ② | 類似度マトリックス Excel | `output/merge/<源文件名>/<module>/類似度マトリックス_<module>.xlsx`(每模块 1 个,场景分 sheet) | `matrix_exporter.py` |
| ③ | 合并模板 xlsm | `output/merge/<源文件名>/<module>/<グルーピングID>_<合并名>.xlsm`(每个需合并组 1 个) | `template_filler.py` |

- ① 列(12,列序固定):`No., 文書管理番号, IF名, モジュール, 業務内容, 項目数, IF概要, 代表項目名, グルーピングID, マージ要否, グルーピング後のIF名, グルーピングの根拠`。
- ① `マージ要否`:`○`(组内 >1 IF)/ `×`(独立);`グルーピングの根拠`:列出与同组 IF 的相似度(如「「IFx」と類似度85%」),无直接关系则「推移性によるマージ」。
- ③ 依赖 `template/IF_Template.xlsm`(含 VBA,`load_workbook(keep_vba=True)`,sheet「エクスポート項目」);抽出項目从第 28 行起、每项 2 行,超过模板自带 10 项时复制第 10 项行格式与合并单元格;按 `(EBSテーブルID, 項目ID)` 去重。

### 8.3 输出目录布局(按源文件名分区)

```
output/
└── merge/
    ├── <源文件名A>/                      ← input_file.stem
    │   ├── グルーピング結果.xlsx          (12 列汇总,本文件全模块)
    │   └── <module>/                     ← 如 FI / SD(特殊字符替换为 _)
    │       ├── 類似度マトリックス_<module>.xlsx
    │       └── <module>NNN_<合并名>.xlsm  (每个需合并组,グルーピングID 模块内连番)
    ├── <源文件名B>/...
    └── logs/merge_<ts>.log               ← 每次合并执行日志
```

> 与参考工程的扁平 `output/merge/グルーピング結果.xlsx` 不同:本工程**每个源 Excel 一个独立子文件夹**(`out_dir = output/merge/<input_file.stem>`),避免多文件批处理时互相覆盖。GUI 进程自身日志另写 `output/ifmerge_gui.log`(`utils/logger.py`)。

### 8.4 模板与默认目录

| 路径 | 用途 |
|---|---|
| `template/IF_Template.xlsm` | 合并模板(VBA),产物 ③;路径可在设置改(`MERGED_TEMPLATE_PATH`) |
| `input/` | 默认输入文件夹(用户实际可选任意文件夹) |
| `output/` | 默认输出根(合并产物落到 `output/merge/`) |

---

## 9. 配置与持久化

- **加载**:`Settings.load()` 用 `load_dotenv(_ENV_PATH, override=True)`,`_ENV_PATH = <仓库根>/.env`(基于 `settings.py` 文件位置 `parents[2]`,**与当前工作目录无关**)。`override=True` 让 `.env` 成为权威来源,覆盖残留系统环境变量。
- **写回**:`Settings.save()` 用 `dotenv.set_key` 把全部字段逐键写回**同一个** `_ENV_PATH`(保留其它内容)。设置弹窗保存即调用,重启保留。
- **优先级**:`.env` 文件 > 系统环境变量 > 代码默认。
- **`.env` 键 ↔ Settings 字段**:

| Settings 字段 | `.env` 键 | 默认 |
|---|---|---|
| input_dir | INPUT_DIR | input |
| output_dir | OUTPUT_DIR | output |
| merged_template_path | MERGED_TEMPLATE_PATH | template/IF_Template.xlsm |
| default_threshold | SIMILARITY_THRESHOLD | 0.8 |
| default_mode | SIMILARITY_MODE | max |
| aicore_auth_url | AICORE_AUTH_URL | "" |
| aicore_client_id | AICORE_CLIENT_ID | "" |
| aicore_client_secret | AICORE_CLIENT_SECRET | "" |
| aicore_base_url | AICORE_BASE_URL | "" |
| aicore_resource_group | AICORE_RESOURCE_GROUP | default |
| aicore_deployment_id | AICORE_DEPLOYMENT_ID | "" |
| aicore_model_name | AICORE_MODEL_NAME | "" |
| log_level | LOG_LEVEL | INFO |

- **提示词配置**:`prompts.yaml`(仓库根)与 `.env` 分离;由 `ebs_merger.PromptConfig` 读取,GUI 不直接编辑(见 §7.4)。

---

## 10. 多语言(i18n)

- **存储**:`i18n/locales/{zh,ja,en}.json`,key→文本,三语 key 一致(约 83 个)。
- **API**:`Translator` 单例 + 模块级 `t(key, **kwargs)`(支持 `str.format` 插值);缺 key 回退默认语言(zh)再回退 key 本身;格式化异常回退原串。
- **持久化**:选中语言写到 `~/.ifmerge/config.json`,启动时读取,默认中文(`zh`)。
- **实时切换**:设置里选语言 → 关闭弹窗 → `app.set_language()` 持久化 + 销毁并重建侧栏/页面(无需重启;会清空当前页已选文件与进度)。
- **覆盖范围**:界面文字、按钮、阶段文本(`phase.*`)、运行日志模板(`log.*`,镜像 `cli.py` 原始输出)、设置项、对话框全部走 `t()`。

---

## 11. 启动与运行

```bash
pip install -r requirements.txt   # 含 customtkinter>=5.2
python -m ifmerge_gui              # 或 python main.py
# Windows 也可用 bat/ 下的 quick_start.bat / run_merge.bat
```

启动流程:`Settings.load()` → `setup_logger(level)` → `IFMergeApp(settings)` → `app.mainloop()`。
**前置条件**:`.env` 配好 SAP AI Core 凭证(`AICORE_*`),否则首次合并会因 `AIGenerator` 凭证校验失败而报错。

---

## 12. 设计取舍(YAGNI)

- **不引入服务器/HTTP**:纯桌面进程内调用 `ebs_merger`,直连 AI Core。相比参考工程的 CAP 客户端,少一层后端运维。
- **不修改 `ebs_merger`**:GUI 在 `MergeTask` 内**重新编排**(镜像 `cli.py`),代价是合并编排存在并行实现,需对照 `cli.py` 保持一致(该 task 文件已注明「编排镜像自 ebs_merger/cli.py」)。换来可在每步穿插进度/取消/日志回调。
- **仅合并、单页**:解析(抽出)由上游 CLI/人工完成;本工程输入即抽出結果 Excel(参考工程 v1.0 的解析页本工程不实现)。
- **AI 失败可降级**:三处 AI 调用都有确定性回退,保证产出分组结果(可能 IF 名/概要质量下降),而非整批失败。
- **不做在线表格/矩阵预览**:结果落地 Excel,经「打开文件夹」查看。
- **取消是粗粒度**:无法中断进行中的单次同步 AI 请求,只能在文件/模块/场景边界停。

---

## 13. 测试与验证

- **可纯逻辑单测**(`tests/`):`Settings.load/save` 往返;i18n 三语 key 集合一致;`fs.find_excel_files` 递归 + 过滤 `~$`/非 `.xlsx`;`SimilarityCalculator` max/avg 与边界(空 field_pairs → 0);`MergeGrouper` Union-Find 传递性。
- **手动验证**(需真实 SAP AI Core 凭证):设置「测试连接」成功;选含抽出結果 Excel 的文件夹 → 合并 → 校验 `output/merge/<源文件名>/` 下三类产物;取消在文件/模块边界生效;日志查看器列出 `merge_<ts>.log`;三语切换即时生效。
