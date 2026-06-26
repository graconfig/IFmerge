"""IFmerge GUI 程序入口:python -m ifmerge_gui"""

from ebs_merger.runtime import app_data_dir
from ifmerge_gui.config.settings import Settings
from ifmerge_gui.ui.app import IFMergeApp
from ifmerge_gui.utils.logger import setup_logger


def main():
    settings = Settings.load()
    # 日志锚定到可写数据目录,避免打包后相对当前工作目录写入失败。
    log_file = str(app_data_dir() / "output" / "ifmerge_gui.log")
    setup_logger(level=settings.log_level, log_file=log_file)
    app = IFMergeApp(settings)
    app.mainloop()


if __name__ == "__main__":
    main()
