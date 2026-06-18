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
