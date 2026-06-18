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
