from __future__ import annotations
# -*- coding: utf-8 -*-
"""
exporter.py  –  导出所有 figure 为 PNG
导出路径：桌面/Audio Test Export/X Devices Compare/时间戳/
"""

import os
import re
from datetime import datetime
import matplotlib.pyplot as plt


def sanitize(name: str) -> str:
    name = name.replace("&", "and")
    name = re.sub(r'[\\/:*?"<>|\s]+', "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "Untitled"


def export_all_figures(file_list: list[str]):
    desktop  = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.isdir(desktop):
        desktop = os.path.expanduser("~")

    n        = len(file_list)
    ts       = datetime.now().strftime("%Y%m%d_%H%M")
    out_dir  = os.path.join(desktop, "Audio Test Export",
                            f"{n} Devices Compare", ts)
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n导出目录：{out_dir}")

    figs = [plt.figure(num) for num in plt.get_fignums()]
    exported = 0
    for fig in figs:
        # 取标题
        axes = fig.get_axes()
        title = ""
        if axes:
            t = axes[0].get_title()
            if t:
                title = t
        if not title:
            if hasattr(fig.canvas, "manager") and fig.canvas.manager is not None:
                title = fig.canvas.manager.get_window_title()
            else:
                title = f"Figure_{fig.number}"

        # 文件名去重：已存在时加数字后缀
        stem     = sanitize(title)
        out_path = os.path.join(out_dir, stem + ".png")
        counter  = 1
        while os.path.exists(out_path):
            out_path = os.path.join(out_dir, f"{stem}_{counter}.png")
            counter += 1

        # 用高 DPI 导出，不修改已显示窗口的尺寸
        try:
            fig.savefig(out_path, dpi=200, bbox_inches="tight",
                        facecolor="white")
            print(f"  已导出：{out_path}")
            exported += 1
        except Exception as e:
            print(f"  [警告] 导出失败（{out_path}）：{e}")

    print(f"全部 {exported}/{len(figs)} 张图导出完成。")
