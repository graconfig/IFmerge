"""把核心 ebs_merger 抛出的硬编码中/日文异常,翻译为当前界面语言。

ebs_merger 是 CLI 共享核心,其异常文案为硬编码(部分中文、部分日文),
不随界面语言变化。GUI 端在此按已知消息特征识别,翻译"框架文案",
保留技术细节(路径、HTTP 状态、缺失列名等)为 {detail}/{path}/{columns}。
无法识别的异常回退到原始消息文本(语言中立),由调用方决定外层框架。

注意:下方特征字符串镜像自 ebs_merger 中的硬编码异常消息;
若核心异常文案变更,需同步更新此处。
"""

import re

from ifmerge_gui.i18n import t


def localize_error(exc: Exception) -> str:
    """返回按当前语言翻译的错误正文;无法识别时回退到原始消息。"""
    msg = str(exc)

    # --- ebs_merger/data_loader.py ---
    if "找不到输入文件" in msg:
        m = re.search(r"'(.+?)'", msg)
        return t("err.file_not_found", path=m.group(1) if m else msg)
    if "无法读取Excel文件" in msg:
        detail = msg.split("详细信息：", 1)[-1] if "详细信息：" in msg else msg
        return t("err.excel_read_fail", detail=detail)
    if "不包含任何数据行" in msg:
        return t("err.no_data_rows")
    if "缺少以下必需列" in msg:
        cols = msg.split("缺少以下必需列：", 1)[-1]
        return t("err.missing_columns", columns=cols)

    # --- ebs_merger/result_generator.py ---
    if "无法写入输出文件" in msg:
        detail = msg.split("无法写入输出文件", 1)[-1].strip()
        return t("err.write_fail", detail=detail or msg)

    # --- ebs_merger/ai_generator.py ---
    if "アクセストークンの取得に失敗" in msg:
        detail = msg.split(":", 1)[-1].strip() if ":" in msg else msg
        return t("err.ai_token_fail", detail=detail)
    if "モデルの呼び出しに失敗" in msg:
        detail = msg.split(":", 1)[-1].strip() if ":" in msg else msg
        return t("err.ai_model_fail", detail=detail)
    if "SAP AI Core設定が不足" in msg:
        return t("err.config_missing")
    if "デプロイメントIDを取得できませんでした" in msg:
        return t("err.deployment_missing")

    # 未识别:回退到原始消息(语言中立)
    return msg
