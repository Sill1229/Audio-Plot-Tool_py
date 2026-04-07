from __future__ import annotations
# -*- coding: utf-8 -*-
"""
plot_compare.py  –  多设备对比模式绘图引擎
"""

import os
import sys
import numpy as np
from scipy.interpolate import interp1d as _interp1d

sys.path.insert(0, os.path.dirname(__file__))
from plot_style import (METRIC_CFG, COMPARE_COLORS, apply_log_xaxis,
                        style_axes, auto_ymax, make_figure, clip)
from harman import load_harman, align_harman

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_proj_data(proj: dict, metric: str):
    m = metric.upper()
    if m == "FR":
        return proj.get("freq_fr"),  proj.get("data_fr")
    elif m == "THD":
        return proj.get("freq_thd"), proj.get("data_thd")
    elif m == "RB":
        return proj.get("freq_rb"),  proj.get("data_rb")
    elif m == "LEAKAGE":
        return proj.get("freq_leak"), proj.get("data_leak")


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
    is_leak   = metric.upper() == "LEAKAGE"

    # Leakage：缺少数据的设备单独跳过，有数据的设备正常绘制
    if is_leak:
        missing = [p for p in projects
                   if p.get("freq_leak") is None or p.get("data_leak") is None]
        if missing:
            names = ", ".join(p["name"] for p in missing)
            print(f"  [信息] 以下设备缺少 'Freqresp -mic 2' 数据，将在 Leakage 图中跳过：{names}")
        # 若所有设备均缺数据，则不生成此图
        if len(missing) == len(projects):
            return

    fig, ax = make_figure(cfg["title"])
    style_axes(ax)

    all_y_max    = y_min
    all_y_min    = np.inf      # 用于 Leakage 居中
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

        if is_leak:
            # 隔离度 = FR(最大音量) - Leakage_mic2(最大音量)
            data_fr_max = proj.get("data_fr_max")
            freq_fr     = proj.get("freq_fr")
            freq_leak, data_leak = _get_proj_data(proj, metric)
            if (data_fr_max is None or freq_fr is None or
                    freq_leak is None or data_leak is None):
                continue
            # 频率轴对齐：将 FR 插值到漏音频率轴上再相减
            fi = _interp1d(freq_fr, data_fr_max, kind="linear",
                           bounds_error=False, fill_value=np.nan)
            y     = fi(freq_leak) - data_leak
            freq  = freq_leak
            max_spl = proj.get("max_spl", 0)
            label = f"{proj['name']} ({max_spl:.0f} dB SPL)"
        else:
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

        ls = "--" if is_leak else "-"
        line, = ax.semilogx(xP, yP, color=col, linestyle=ls, linewidth=2.0)
        all_y_max = max(all_y_max, np.nanmax(yP))
        all_y_min = min(all_y_min, np.nanmin(yP))
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
    if is_leak and all_y_min < np.inf:
        margin = max((all_y_max - all_y_min) * 0.3, 5)
        y_min  = np.floor((all_y_min - margin) / 5) * 5
        y_max  = np.ceil((all_y_max + margin) / 5) * 5
    else:
        y_max = auto_ymax(all_y_max, is_fr)
    ax.set_ylim(y_min, y_max)
    if is_leak:
        ax.set_ylabel("Isolation (dB)", fontsize=13)
    elif is_fr:
        ax.set_ylabel("SPL (dB)", fontsize=13)
    else:
        ax.set_ylabel("Level (%)", fontsize=13)

    # X 轴
    apply_log_xaxis(ax, x_lim)

    # Legend
    if h_lines:
        ax.legend(h_lines, legend_labels,
                  loc="best", fontsize=10, frameon=True)

    fig.tight_layout()


def plot_compare(projects: list[dict], use_harman: bool, normalize: bool = False):
    """绘制多设备的 FR / THD / RB / Leakage 四张对比图。"""
    for metric in ["FR", "THD", "RB"]:
        _draw_metric(projects, metric, use_harman, normalize)
    # Leakage 单独处理（仅当所有设备都有数据时才画）
    _draw_metric(projects, "Leakage", use_harman, normalize)
