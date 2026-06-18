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
