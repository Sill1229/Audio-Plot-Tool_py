from __future__ import annotations
# -*- coding: utf-8 -*-
"""
plot_compare.py  –  多设备对比模式绘图引擎
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from plot_style import (COMPARE_COLORS, apply_log_xaxis, style_axes,
                        auto_ymax, make_figure, clip)
from harman import load_harman, align_harman

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

METRIC_CFG = {
    "FR":  {"title": "Frequency Response", "x_lim": (50, 20000),  "y_min": 20,  "is_fr": True},
    "THD": {"title": "THD",                "x_lim": (100, 10000), "y_min": 0,   "is_fr": False},
    "RB":  {"title": "Rub & Buzz",         "x_lim": (100, 10000), "y_min": 0,   "is_fr": False},
}


def _get_proj_data(proj: dict, metric: str):
    m = metric.upper()
    if m == "FR":
        return proj.get("freq_fr"),  proj.get("data_fr")
    elif m == "THD":
        return proj.get("freq_thd"), proj.get("data_thd")
    elif m == "RB":
        return proj.get("freq_rb"),  proj.get("data_rb")


def _normalize_to_ref(y: np.ndarray, freq: np.ndarray,
                      ref_mean: float,
                      band: tuple = (500, 2000)) -> np.ndarray:
    """将曲线的 500–2000 Hz 均值平移对齐到 ref_mean。"""
    mask = (freq >= band[0]) & (freq <= band[1])
    cur_mean = np.nanmean(y[mask])
    if np.isnan(cur_mean):
        return y
    return y + (ref_mean - cur_mean)


def _draw_metric(projects: list[dict], metric: str,
                 use_harman: bool, normalize: bool):
    cfg       = METRIC_CFG[metric.upper()]
    x_lim     = cfg["x_lim"]
    y_min     = cfg["y_min"]
    is_fr     = cfg["is_fr"]

    fig, ax = make_figure(cfg["title"])
    style_axes(ax)

    all_y_max    = y_min
    h_lines      = []
    legend_labels = []

    # 归一化基准：第一个项目的 500–2000 Hz 均值
    ref_mean = None
    if normalize:
        first_proj = next((p for p in projects
                           if p.get("freq_fr") is not None
                           and p.get("data_fr") is not None), None)
        if first_proj is not None:
            mask = ((first_proj["freq_fr"] >= 500) &
                    (first_proj["freq_fr"] <= 2000))
            ref_mean = float(np.nanmean(first_proj["data_fr"][mask]))

    for i, proj in enumerate(projects):
        col  = COMPARE_COLORS[i % len(COMPARE_COLORS)]
        freq, y = _get_proj_data(proj, metric)

        if freq is None or y is None:
            continue

        # 归一化（仅 FR；THD/RB 偏移无意义）
        if normalize and ref_mean is not None and metric.upper() == "FR":
            y = _normalize_to_ref(y, freq, ref_mean)
            label = f"{proj['name']} (norm)"
        else:
            label = f"{proj['name']} ({proj['ref_spl']:.1f} dB SPL)"

        xP, yP = clip(freq, y, x_lim)
        if len(xP) == 0:
            continue

        line, = ax.semilogx(xP, yP, color=col, linewidth=2.0)
        all_y_max = max(all_y_max, np.nanmax(yP))
        h_lines.append(line)
        legend_labels.append(label)

    # Harman Target（仅 FR）
    if is_fr and use_harman and projects:
        hf, hs = load_harman(SCRIPT_DIR)
        if hf is not None:
            ref_proj = projects[0]
            ref_freq = ref_proj.get("freq_fr")
            ref_data = ref_proj.get("data_fr")
            if ref_freq is not None and ref_data is not None:
                pf, ps = align_harman(hf, hs, ref_freq, ref_data, x_lim)
                line,  = ax.semilogx(pf, ps, color="black",
                                     linestyle="--", linewidth=1.6)
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
        ax.legend(h_lines, legend_labels,
                  loc="best", fontsize=10, frameon=True)

    fig.tight_layout()


def plot_compare(projects: list[dict], use_harman: bool, normalize: bool = False):
    """绘制多设备的 FR / THD / RB 三张对比图。"""
    for metric in ["FR", "THD", "RB"]:
        _draw_metric(projects, metric, use_harman, normalize)
