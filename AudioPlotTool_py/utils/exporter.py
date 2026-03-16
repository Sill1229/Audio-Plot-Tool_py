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
    for fig in figs:
        # 取标题
        axes = fig.get_axes()
        title = ""
        if axes:
            t = axes[0].get_title()
            if t:
                title = t
        if not title:
            title = fig.canvas.manager.get_window_title() if hasattr(
                fig.canvas, "manager") else f"Figure_{fig.number}"

        fname   = sanitize(title) + ".png"
        out_path = os.path.join(out_dir, fname)

        # 临时放大到接近全屏
        orig_size = fig.get_size_inches()
        fig.set_size_inches(18, 10)
        fig.savefig(out_path, dpi=150, bbox_inches="tight",
                    facecolor="white")
        fig.set_size_inches(*orig_size)
        print(f"  已导出：{out_path}")

    print(f"全部 {len(figs)} 张图导出完成。")
