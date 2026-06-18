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
