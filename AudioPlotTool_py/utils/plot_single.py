from __future__ import annotations
# -*- coding: utf-8 -*-
"""
plot_single.py  –  单设备多音量模式绘图引擎
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from plot_style import (warm_cold_colors, apply_log_xaxis, style_axes,
                        auto_ymax, make_figure, clip)
from harman import load_harman, align_harman

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# metric 配置
METRIC_CFG = {
    "FR":  {"title": "Frequency Response", "x_lim": (50, 20000),   "y_min": 20,  "is_fr": True},
    "THD": {"title": "THD",                "x_lim": (100, 10000),  "y_min": 0,   "is_fr": False},
    "RB":  {"title": "Rub & Buzz",         "x_lim": (100, 10000),  "y_min": 0,   "is_fr": False},
}


def _get_data(d: dict, metric: str):
    """从数据字典中取出对应 metric 的频率轴和数据矩阵。"""
    m = metric.upper()
    if m == "FR":
        return d.get("freq_fr_l"), d.get("dat_fr_l"), \
               d.get("freq_fr_r"), d.get("dat_fr_r")
    elif m == "THD":
        return d.get("freq_thd_l"), d.get("dat_thd_l"), \
               d.get("freq_thd_r"), d.get("dat_thd_r")
    elif m == "RB":
        return d.get("freq_rb_l"), d.get("dat_rb_l"), \
               d.get("freq_rb_r"), d.get("dat_rb_r")


def _draw_metric(data: dict, metric: str, use_harman: bool):
    cfg       = METRIC_CFG[metric.upper()]
    title_str = f"{cfg['title']}  –  {data['proj_name']}"
    x_lim     = cfg["x_lim"]
    y_min     = cfg["y_min"]
    is_fr     = cfg["is_fr"]

    freq_l, dat_l, freq_r, dat_r = _get_data(data, metric)
    if freq_l is None or dat_l is None:
        print(f"  [警告] 缺少 {metric} L 数据，跳过。")
        return

    sort_idx  = data["sort_idx"]
    n_sweeps  = len(sort_idx)
    show_both = data["show_both"]
    colors    = warm_cold_colors(n_sweeps)

    fig, ax = make_figure(title_str)
    style_axes(ax)

    all_y_max    = y_min
    h_lines      = []
    legend_labels = []

    for k, orig_row in enumerate(sort_idx):
        col       = colors[k]
        vol_label = f"Volume {k}"

        # L 声道（实线）
        if dat_l is not None and orig_row < dat_l.shape[0]:
            xL, yL = clip(freq_l, dat_l[orig_row], x_lim)
            if len(xL) > 0:
                line, = ax.semilogx(xL, yL, color=col,
                                    linestyle="-", linewidth=2.0)
                all_y_max = max(all_y_max, np.nanmax(yL))
                h_lines.append(line)
                legend_labels.append(f"{vol_label}  (L)" if show_both else vol_label)

        # R 声道（虚线）
        if show_both and dat_r is not None and orig_row < dat_r.shape[0]:
            xR, yR = clip(freq_r, dat_r[orig_row], x_lim)
            if len(xR) > 0:
                line, = ax.semilogx(xR, yR, color=col,
                                    linestyle="--", linewidth=1.6)
                all_y_max = max(all_y_max, np.nanmax(yR))
                h_lines.append(line)
                legend_labels.append(f"{vol_label}  (R)")

    # Harman Target（仅 FR）
    if is_fr and use_harman:
        hf, hs = load_harman(SCRIPT_DIR)
        if hf is not None:
            ref_row = dat_l[sort_idx[-1]]   # 最高音量档对齐
            pf, ps  = align_harman(hf, hs, freq_l, ref_row, x_lim)
            line,   = ax.semilogx(pf, ps, color="black",
                                  linestyle="--", linewidth=1.6,
                                  label="Harman Target")
            h_lines.append(line)
            legend_labels.append("Harman Target")

    # Y 轴
    y_max = auto_ymax(all_y_max, is_fr)
    ax.set_ylim(y_min, y_max)
    ax.set_ylabel("SPL (dB)" if is_fr else "Level (%)", fontsize=13)
    # X 轴
    apply_log_xaxis(ax, x_lim)

    # Legend
    if h_lines:
        lgd = ax.legend(h_lines, legend_labels,
                        loc="lower left", fontsize=9, frameon=True)
        if show_both:
            lgd.set_title("实线 = L    虚线 = R", prop={"size": 8})

    fig.tight_layout()


def plot_single_device(data: dict, use_harman: bool):
    """绘制单设备的 FR / THD / RB 三张图。"""
    for metric in ["FR", "THD", "RB"]:
        _draw_metric(data, metric, use_harman)
