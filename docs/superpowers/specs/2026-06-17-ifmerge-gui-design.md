# IFmerge 桌面 GUI 设计书

- 日期：2026-06-17
- 目标：为本地 CLI 工具 IFmerge 构建桌面 GUI，外观与交互对齐参考工程 `/data/HuangCX/ifmerge-gui`。

## 1. 背景与约束

- **参考工程 `ifmerge-gui`**：CustomTkinter 桌面应用，左侧导航 + 右侧两页（解析 / 合并），底部「日志」「设定」。后台用 `threading.Thread`，通过 `widget.after()` 把进度/日志回调到主线程。其 task 调用**远程 CAP REST 服务**并轮询作业进度。
- **本工程 `IFmerge`（`ebs_merger` 包）**：纯本地 CLI 批处理工具（`EBSMergerCLI`），在进程内完成「加载 Excel → 分组 → AI 分类 → 相似度 → 合并分组 → 输出」，直接调用 SAP AI Core。**无任何服务器/HTTP 端点**。

### 关键架构决策（已与用户确认）

1. **后端集成 = 进程内直接调用**。GUI 的后台 task 直接调用 `ebs_merger` 的组件，无服务器、无 HTTP 轮询。
2. **页面结构 = 沿用「解析 + 合并」两页**，与参考工程一致。
3. **编排方式 = GUI 内重新编排**。不修改 `ebs_merger` 任何代码；GUI 的 task 直接调用 `ebs_merger` 各组件，自行实现进度/取消编排（贴近参考工程 task 直接调用 core 的模式）。
4. **默认语言 = 中文（zh）**，同时内置 zh/ja/en，可在设定中切换。

## 2. 总体架构

新建 GUI 包 `ifmerge_gui/`，置于 IFmerge 仓库根目录，结构镜像参考工程。框架 = CustomTkinter ≥ 5.2。复用参考工程的 `BasePage` 线程编排契约（`_cb_progress / _cb_log / _cb_done / _cb_failed`，`task.cancel()` 标志位，文件夹输入，进度日志，落地 `.log`）。

唯一本质区别：task 内部把「REST 客户端调用 + 轮询」替换为「进程内调用 `ebs_merger` 组件」。

```
IFmerge/
├── ebs_merger/                 # 现有核心逻辑，本次不修改
├── ifmerge_gui/                # 新增 GUI 包
│   ├── __init__.py
│   ├── __main__.py             # `python -m ifmerge_gui` 入口
│   ├── config/
│   │   └── settings.py         # .env 读写（适配 IFmerge 的键）
│   ├── i18n/
│   │   ├── __init__.py         # Translator 单例 + t()
│   │   └── locales/{zh,ja,en}.json
│   ├── ui/
│   │   ├── app.py              # 主窗口 IFMergeApp + 左侧导航
│   │   ├── pages/
│   │   │   ├── base_page.py    # 复刻参考工程 BasePage（文件夹输入+输出+执行+进度日志+线程回调）
│   │   │   ├── analyze_page.py # 解析页
│   │   │   └── merge_page.py   # 合并页
│   │   ├── widgets/
│   │   │   ├── file_input.py   # 文件夹选择 + 递归扫描 .xlsx（跳过 ~$ 临时文件）
│   │   │   ├── file_output.py  # 显示输出目录 + 跨平台「打开文件夹」
│   │   │   └── progress_log.py # 进度条 + 阶段标签 + 只读日志框
│   │   ├── dialogs/
│   │   │   ├── settings_dialog.py
│   │   │   └── log_viewer.py
│   │   ├── tasks/
│   │   │   ├── analyze_task.py # 进程内：解析子流程
│   │   │   └── merge_task.py   # 进程内：完整合并流水线
│   │   └── utils/
│   │       └── phase_text.py   # 阶段 key → 本地化文本
│   └── utils/
│       └── logger.py
├── main.py                     # 便捷入口（= python -m ifmerge_gui）
└── requirements.txt            # 追加 customtkinter>=5.2
```

## 3. 主窗口与导航（`ui/app.py`）

复刻参考工程：
- 窗口标题 `IFmerge`，初始尺寸约 1100×720。
- 左侧导航栏（约 160px）：标题「IFmerge」、导航按钮「▶ 解析」「▶ 合併」（激活态高亮 `#1f6aa5`，非激活态灰），底部弹簧后放「📜 日志」「⚙ 設定」。
- 右侧主区域显示当前页（AnalyzePage / MergePage），网格 `(0,1, sticky="nsew")`。
- 跟随系统深浅色主题（CustomTkinter 默认）。

## 4. 两页与 IFmerge 流水线的映射

两页都以**输入 Excel 文件夹**为输入（`FileInput` 递归扫描 `.xlsx`、跳过 `~$` 临时文件），各自独立运行、互不依赖。

### 4.1 解析页（AnalyzeTask）→ `output/parse/`

逐文件执行轻量子流程，**不做分组/合并**：

1. `DataLoader.load_excel(file)` → DataFrame
2. `IFGrouper.group_by_if(df)` → `if_dict`
3. `AIClassifier.classify_interfaces(if_dict, df)` → categories（模块/业务场景）
4. `AIGenerator.generate_all_if_info(if_dict, df)` → 各 IF 的概要/代表项目

输出 `解析結果.xlsx`，每个 IF 一行，列：`No. / 文書管理番号 / IF名 / モジュール / 業務内容 / 項目数 / IF概要 / 代表項目名`。

阶段（phase）序列：`读み込み → グループ化 → AI分類 → AI概要生成 → 出力`。进度按「文件 idx/total」推进。

### 4.2 合并页（MergeTask）→ `output/merge/`

执行**完整流水线**，等价于现有 `EBSMergerCLI.run()` 的逻辑（在 task 内重新编排，调用同一批组件）。输出：
- `グルーピング結果.xlsx`（统一分组结果，列序同 `cli.py:_write_unified_output`）
- 各模块 `類似度マトリックス_<module>.xlsx`（`MatrixExporter.export_module_matrices`）
- 各模块文件夹下填充后的模板 `.xlsm`（`TemplateFiller.fill_merged_groups`）

编排镜像 `cli.py`：逐文件 → `load_excel` → `group_by_if` → `classify_interfaces` → `_organize_by_module` → 逐模块逐场景：`build_similarity_matrix` / `build_full_similarity_matrix` → `group_similar_ifs` → 连番分配 グルーピングID → 生成输出行（含 `generate_all_if_info` / `generate_merged_if_name`）→ `fill_merged_groups` → 模块级 `export_module_matrices` → 汇总写 `グルーピング結果.xlsx`。

阶段序列：`读み込み → グループ化 → AI分類 → 類似度計算 → グルーピング → マージ名生成 → テンプレート出力 → マトリックス出力`。进度按「文件 idx/total」为主、模块为辅推进。

### 4.3 取消与异常

- task 持有 `_cancel` 标志，`cancel()` 置位。在每文件、每模块循环起点检查；命中则记日志「取消されました」并提前返回（`on_done` 收尾，不报错）。注意：AI 调用为同步阻塞，取消粒度到「下一个文件/模块」之间，无法中断进行中的单次 AI 请求。
- 组件抛异常 → `on_failed(exc)`：进度条置失败态、日志追加错误、落地 `.log`、恢复按钮可用态。
- 单文件失败不应中断整批（与 `cli.py` 一致：记失败、计数、继续下个文件）。

## 5. 线程编排契约（复刻 `base_page.py`）

`BasePage(ctk.CTkFrame)` 提供：`FileInput`（`on_change` 启停「开始」按钮）+ `FileOutput` + 执行帧（开始/取消按钮，运行态互斥）+ `ProgressLog`。子类实现 `run_button_text()` / `output_dir()` / `log_kind()` / `create_task(files)`。

task 是 `threading.Thread(daemon=True)`，构造时注入四个回调：`on_progress(percent:int, phase:str)`、`on_log(msg:str)`、`on_done(result)`、`on_failed(exc)`。所有回调经 `self.after(0, ...)` 调度回主线程，保证 Tk 线程安全。每次执行的日志行收集后落地 `output/<kind>/logs/<kind>_<时间戳>.log`。

## 6. 配置与设定弹窗（`config/settings.py` + `dialogs/settings_dialog.py`）

`Settings` dataclass 从 `.env`（固定指向仓库根，基于文件位置）加载/写回，适配 IFmerge 现有键：

| 字段 | .env 键 | 默认 |
|---|---|---|
| input_dir | INPUT_DIR | input |
| output_dir | OUTPUT_DIR | output |
| similarity_threshold | SIMILARITY_THRESHOLD | 0.8 |
| similarity_mode | SIMILARITY_MODE | max |
| merged_template_path | （新增）MERGED_TEMPLATE_PATH | template/IF_Template.xlsm |
| log_level | LOG_LEVEL | INFO |
| aicore_auth_url | AICORE_AUTH_URL | "" |
| aicore_client_id | AICORE_CLIENT_ID | "" |
| aicore_client_secret | AICORE_CLIENT_SECRET | "" |
| aicore_base_url | AICORE_BASE_URL | "" |
| aicore_resource_group | AICORE_RESOURCE_GROUP | default |
| aicore_deployment_id | AICORE_DEPLOYMENT_ID | "" |

设定弹窗（CTkToplevel 模态）：
- **基本**：SAP AI Core 连接（AICORE_* 凭据）+「接続テスト」按钮——调用 `AIGenerator._get_access_token()` 取 token、`_resolve_deployment_id()` 验证可达性，显示成功/失败。
- **高级（可折叠）**：输出目录、相似度阈值（0.5–1.0）、模式 max/avg、合并模板路径、日志级别。
- **语言选择器**：zh / 日本語 / English，切换后实时重建 UI。语言偏好持久化到 `~/.ifmerge/config.json`（与参考工程一致）。
- 保存写回 `.env`（逐键 `set_key`，保留其它内容）。

## 7. 日志查看器（`dialogs/log_viewer.py`）

复刻参考工程：扫描 `output/parse/logs` 与 `output/merge/logs` 的 `.log`，按修改时间倒序列于左栏；右栏只读显示选中内容。

## 8. 国际化（`i18n/`）

JSON 驱动的 `Translator` 单例 + `t(key, **kwargs)`，locales 含 `zh.json` / `ja.json` / `en.json`。默认 zh。key 覆盖导航、按钮、阶段文本、日志模板、设定项、对话框。阶段文本通过 `utils/phase_text.py` 由 phase key 映射到本地化串。

## 9. 启动方式

```bash
pip install -r requirements.txt   # 含 customtkinter>=5.2
python -m ifmerge_gui              # 或 python main.py
```

启动流程：`Settings.load()` → `setup_logger()` → `IFMergeApp(settings)` → `app.mainloop()`。

## 10. YAGNI 取舍

- 不引入 Web 框架/服务器，纯桌面进程内调用。
- 不修改 `ebs_merger`；GUI task 内重新编排（用户确认）。代价：合并编排逻辑与 `cli.py` 存在并行实现，需在实现时对照 `cli.py` 保持一致，并在该 task 文件注明「编排镜像自 ebs_merger/cli.py」。
- 合并页**不**复用解析页的中间产物（解析输出不含相似度所需的 `field_pairs` 集合，强行复用需额外序列化，得不偿失）；两页各自读源 Excel 独立运行，允许少量 AI 重算。
- 不做结果在线表格/矩阵预览；结果落地 Excel，经「打开文件夹」查看（与参考工程一致）。

## 11. 测试

- `tests/` 下为可纯逻辑测试的部分加单测：`Settings.load/save` 往返、i18n key 完整性（三语 key 集合一致）、`FileInput` 递归扫描过滤 `~$`、phase_text 映射完备。
- UI 线程编排与 AI 调用以手动验证为主（需真实 SAP AI Core 凭据），文档化手动验证清单。
