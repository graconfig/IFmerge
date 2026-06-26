# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 —— IFmerge 桌面 GUI(Windows)。

构建(在 Windows 上,仓库根目录执行):
    pip install -r requirements.txt
    pip install pyinstaller
    pyinstaller ifmerge.spec

产物:dist/IFmerge/IFmerge.exe(onedir,默认)。
切换单文件:见文件末尾 onefile 说明。

资源约定(与 ebs_merger/runtime.py 的 resource_path() 对应):
    prompts.yaml                       -> <bundle>/prompts.yaml
    template/IF_Template.xlsm          -> <bundle>/template/IF_Template.xlsm
    ifmerge_gui/i18n/locales/*.json    -> <bundle>/ifmerge_gui/i18n/locales/
可写文件(.env / input / output / 日志)运行时写到 exe 同级目录(app_data_dir())。
"""

import os
from PyInstaller.utils.hooks import collect_data_files

# SPECPATH 由 PyInstaller 注入,指向本 spec 所在目录(= 仓库根)。
ROOT = SPECPATH

# ---- 只读资源:打进 bundle,保持 resource_path() 期望的相对结构 ----
datas = [
    (os.path.join(ROOT, "prompts.yaml"), "."),
    (os.path.join(ROOT, "template", "IF_Template.xlsm"), "template"),
]

# i18n 语言文件(逐个收集,目标目录与 resource_path 对应)
_locales_dir = os.path.join(ROOT, "ifmerge_gui", "i18n", "locales")
for _name in os.listdir(_locales_dir):
    if _name.endswith(".json"):
        datas.append((os.path.join(_locales_dir, _name),
                      os.path.join("ifmerge_gui", "i18n", "locales")))

# customtkinter 自带主题/字体等数据文件 —— 不收集会导致界面崩溃(最常见的坑)。
datas += collect_data_files("customtkinter")

# pandas / openpyxl / requests 由 PyInstaller 内置 hook 处理,通常无需手动添加。
# 若运行时报 "No module named ..." 再按需补到这里。
hiddenimports = []

# ---- 可选图标:存在则使用(放 assets/IFmerge.ico) ----
_icon = os.path.join(ROOT, "assets", "IFmerge.ico")
icon = _icon if os.path.exists(_icon) else None


a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 测试/构建期依赖不进运行时包,减小体积。
    excludes=["pytest", "hypothesis", "_pytest", "pluggy"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,        # onedir:二进制交给 COLLECT
    name="IFmerge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                # GUI 模式,不弹控制台黑窗
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="IFmerge",
)

# ---- 切换为单文件(onefile)发布 ----
# 注释掉上面的 exe(exclude_binaries=True) 与整个 COLLECT,改用:
#
# exe = EXE(
#     pyz, a.scripts, a.binaries, a.datas, [],
#     name="IFmerge", debug=False, strip=False, upx=True,
#     console=False, icon=icon,
# )
#
# 注意:onefile 启动较慢(每次解压到临时目录),建议先用 onedir 调通再切换。
