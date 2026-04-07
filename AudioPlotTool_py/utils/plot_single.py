from __future__ import annotations
# -*- coding: utf-8 -*-
"""
plot_single.py  –  单设备多音量模式绘图引擎
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d as _interp1d

sys.path.insert(0, os.path.dirname(__file__))
from plot_style import (METRIC_CFG, warm_cold_colors, apply_log_xaxis,
                        style_axes, auto_ymax, make_figure, clip)
from harman import load_harman, align_harman

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    elif m == "LEAKAGE":
        return d.get("freq_leak_l"), d.get("dat_leak_l"), None, None


def _draw_metric(data: dict, metric: str, use_harman: bool):
    cfg       = METRIC_CFG[metric.upper()]
    title_str = f"{cfg['title']}  –  {data['proj_name']}"
    x_lim     = cfg["x_lim"]
    y_min     = cfg["y_min"]
    is_fr     = cfg["is_fr"]
    is_leak   = metric.upper() == "LEAKAGE"

    freq_l, dat_l, freq_r, dat_r = _get_data(data, metric)
    if freq_l is None or dat_l is None:
        if is_leak:
            print(f"  [信息] 缺少 Leakage mic 2 数据，跳过漏音图。")
        else:
            print(f"  [警告] 缺少 {metric} L 数据，跳过。")
        return

    # Leakage 需要 FR L 数据来计算隔离度
    if is_leak:
        freq_fr_l = data.get("freq_fr_l")
        dat_fr_l  = data.get("dat_fr_l")
        if freq_fr_l is None or dat_fr_l is None:
            print("  [警告] 缺少 FR L 数据，无法计算隔离度，跳过。")
            return

    sort_idx  = data["sort_idx"]
    n_sweeps  = len(sort_idx)
    show_both = data["show_both"]
    colors    = warm_cold_colors(n_sweeps)

    fig, ax = make_figure(title_str)
    style_axes(ax)

    all_y_max    = y_min
    all_y_min    = np.inf      # 用于 Leakage 居中
    h_lines      = []
    legend_labels = []

    # Leakage 只画最大音量（sort_idx 升序，最后一个是最大）
    if is_leak:
        max_row = sort_idx[-1]
        if max_row < dat_l.shape[0] and max_row < dat_fr_l.shape[0]:
            # 频率轴对齐：将 FR 插值到漏音频率轴上再相减
            fi = _interp1d(freq_fr_l, dat_fr_l[max_row], kind="linear",
                           bounds_error=False, fill_value=np.nan)
            fr_on_leak = fi(freq_l)
            y_val = fr_on_leak - dat_l[max_row]
            xL, yL = clip(freq_l, y_val, x_lim)
            if len(xL) > 0:
                spl_val = data["spl_sorted"][-1]
                line, = ax.semilogx(xL, yL, color="#1f77b4",
                                    linestyle="--", linewidth=2.0)
                all_y_max = max(all_y_max, np.nanmax(yL))
                all_y_min = min(all_y_min, np.nanmin(yL))
                h_lines.append(line)
                legend_labels.append(f"Max Vol ({spl_val:.0f} dB SPL)")
    else:
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
    if is_leak and all_y_min < np.inf:
        # 居中显示：数据范围 ± 余量，向外取整到 5 的倍数
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
        lgd = ax.legend(h_lines, legend_labels,
                        loc="lower left", fontsize=9, frameon=True)
        if show_both and not is_leak:
            lgd.set_title("实线 = L    虚线 = R", prop={"size": 8})

    fig.tight_layout()


def plot_single_device(data: dict, use_harman: bool):
    """绘制单设备的 FR / THD / RB / Leakage 四张图。"""
    for metric in ["FR", "THD", "RB"]:
        _draw_metric(data, metric, use_harman)
    # Leakage 仅在数据存在时绘制
    _draw_metric(data, "Leakage", use_harman)
