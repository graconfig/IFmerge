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
