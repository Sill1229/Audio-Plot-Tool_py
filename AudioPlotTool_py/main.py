from __future__ import annotations
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AudioPlotTool  –  主入口
单文件 → 单设备多音量模式
多文件 → 多设备对比模式
"""

import sys
import os
import matplotlib
try:
    matplotlib.use("TkAgg")
    import tkinter as _tk_test   # 验证 tkinter 可用
    del _tk_test
except ImportError:
    matplotlib.use("Agg")        # 无 Tk 环境时降级到非交互后端
import matplotlib.pyplot as plt

# 把 utils 加入搜索路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "utils"))

from dialogs          import ask_files, ask_export_png, ask_harman, ask_channel_mode, ask_normalize, ask_volume_mode
from reader           import read_ap_sheet, SHEET_NAMES
from project_builder  import build_single_device, build_multi_device
from plot_single      import plot_single_device
from plot_compare     import plot_compare
from exporter         import export_all_figures


def main():
    # ── 1. 选文件 ───────────────────────────────────────────
    file_list = ask_files()
    if not file_list:
        print("未选择任何文件，程序退出。")
        return

    is_single = len(file_list) == 1
    mode_str  = "单设备多音量模式" if is_single else f"多设备对比模式（{len(file_list)} 个文件）"
    print(f"\n检测到 {len(file_list)} 个文件 → 进入【{mode_str}】")

    # ── 2. 通用选项 ─────────────────────────────────────────
    do_export  = ask_export_png()
    use_harman = ask_harman()

    # ── 3. 分支处理 ─────────────────────────────────────────
    if is_single:
        show_both = ask_channel_mode()
        data      = build_single_device(file_list[0], SHEET_NAMES, show_both)
        if data is None:
            print("数据读取失败，程序退出。")
            return
        plot_single_device(data, use_harman)

    else:
        show_both      = False
        normalize      = ask_normalize()
        use_max_volume = ask_volume_mode()
        projects       = build_multi_device(file_list, SHEET_NAMES, use_max_volume)
        if not projects:
            print("没有找到任何可用的项目数据，请检查 Excel 文件格式。")
            return
        plot_compare(projects, use_harman, normalize)

    # ── 4. 导出 ─────────────────────────────────────────────
    if do_export:
        export_all_figures(file_list)

    print("\n全部完成。")
    plt.show()


if __name__ == "__main__":
    main()
