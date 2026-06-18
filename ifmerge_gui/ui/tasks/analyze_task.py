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
                    self.on_log(t("log.file_done"))
                except Exception as e:
                    logger.exception("analyze file failed")
                    self.on_log(t("log.file_fail", error=e))

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
        self.on_log(t("log.loaded", rows=len(df)))

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
