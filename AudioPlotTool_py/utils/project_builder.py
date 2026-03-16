from __future__ import annotations
# -*- coding: utf-8 -*-
"""
project_builder.py  –  构建绘图所需的数据结构

单设备模式：build_single_device  → dict
多设备模式：build_multi_device   → list[dict]
"""

import os
import re
import numpy as np
from reader import read_ap_sheet, read_channel

TARGET_SPL = 75.0
BAND_LOW   = 500.0
BAND_HIGH  = 2000.0


# ── 辅助函数 ─────────────────────────────────────────────

def get_project_name(file_path: str) -> str:
    """从文件名中去掉日期/时间戳，提取项目名称。"""
    base = os.path.splitext(os.path.basename(file_path))[0]
    # 匹配常见时间戳格式
    patterns = [
        r'[_\-]\d{4}[-]\d{1,2}[-]\d{1,2}$',   # _2026-3-11
        r'[_\s]\d{8}$',                          # _20260313
        r'\s+\d{4}$',                            # 空格+年份
    ]
    name = base
    for p in patterns:
        name = re.sub(p, '', name).strip()
    return name if name else base


def calc_band_mean(freq: np.ndarray, row: np.ndarray,
                   f_low: float, f_high: float) -> float:
    """计算指定频段内的算术平均 SPL。"""
    mask = (freq >= f_low) & (freq <= f_high)
    vals = row[mask]
    vals = vals[~np.isnan(vals)]
    return float(np.mean(vals)) if len(vals) > 0 else np.nan


def select_best_row(freq: np.ndarray, data: np.ndarray,
                    f_low: float, f_high: float,
                    target: float) -> tuple[int, float]:
    """找出频段均值最接近 target 的行，返回 (行索引, 实际均值)。"""
    means = np.array([calc_band_mean(freq, data[r], f_low, f_high)
                      for r in range(data.shape[0])])
    diffs = np.abs(means - target)
    diffs[np.isnan(diffs)] = np.inf
    idx   = int(np.argmin(diffs))
    return idx, float(means[idx])


# ── 单设备模式 ───────────────────────────────────────────

def build_single_device(file_path: str, sheet_names: dict,
                        show_both: bool) -> dict | None:
    """
    读取单个 Excel 的所有 sweep，按 500–2000 Hz 均值升序排列。
    返回包含所有数据的字典。
    """
    proj_name = get_project_name(file_path)
    print(f"\n项目名称：{proj_name}")

    freq_fr_l, dat_fr_l = read_ap_sheet(file_path, sheet_names["FR_L"])
    if freq_fr_l is None:
        print("  [错误] 无法读取 FR L 数据。")
        return None

    freq_thd_l, dat_thd_l = read_ap_sheet(file_path, sheet_names["THD_L"])
    freq_rb_l,  dat_rb_l  = read_ap_sheet(file_path, sheet_names["RB_L"])

    freq_fr_r = freq_thd_r = freq_rb_r = None
    dat_fr_r  = dat_thd_r  = dat_rb_r  = None

    if show_both:
        freq_fr_r,  dat_fr_r  = read_ap_sheet(file_path, sheet_names["FR_R"])
        freq_thd_r, dat_thd_r = read_ap_sheet(file_path, sheet_names["THD_R"])
        freq_rb_r,  dat_rb_r  = read_ap_sheet(file_path, sheet_names["RB_R"])

    # 计算每行 500–2000 Hz 均值并升序排序
    n_sweeps  = dat_fr_l.shape[0]
    spl_means = np.array([
        calc_band_mean(freq_fr_l, dat_fr_l[r], BAND_LOW, BAND_HIGH)
        for r in range(n_sweeps)
    ])
    sort_idx        = np.argsort(spl_means)          # 升序：低音量→高音量
    spl_sorted      = spl_means[sort_idx]

    print(f"\n各档位声压（500–2000 Hz 均值，升序）：")
    for k, (orig, spl) in enumerate(zip(sort_idx, spl_sorted)):
        print(f"  Volume {k}（原行 {orig}）：{spl:.1f} dB SPL")

    return {
        "proj_name":   proj_name,
        "file_path":   file_path,
        "show_both":   show_both,
        "sort_idx":    sort_idx,       # numpy array，升序
        "spl_sorted":  spl_sorted,
        "freq_fr_l":   freq_fr_l,  "dat_fr_l":  dat_fr_l,
        "freq_thd_l":  freq_thd_l, "dat_thd_l": dat_thd_l,
        "freq_rb_l":   freq_rb_l,  "dat_rb_l":  dat_rb_l,
        "freq_fr_r":   freq_fr_r,  "dat_fr_r":  dat_fr_r,
        "freq_thd_r":  freq_thd_r, "dat_thd_r": dat_thd_r,
        "freq_rb_r":   freq_rb_r,  "dat_rb_r":  dat_rb_r,
    }


# ── 多设备模式 ───────────────────────────────────────────

def build_multi_device(file_list: list[str],
                       sheet_names: dict) -> list[dict]:
    """
    每个 Excel 取最接近 75 dB SPL 的行（L 声道优先）。
    返回项目字典列表。
    """
    projects = []

    for i, file_path in enumerate(file_list):
        print(f"\n正在处理文件 {i+1}/{len(file_list)}：{file_path}")

        freq_fr, dat_fr, chan = read_channel(
            file_path, sheet_names["FR_L"], sheet_names["FR_R"])

        if freq_fr is None:
            print("  [警告] 缺少 FR 数据，已跳过。")
            continue

        proj_name       = get_project_name(file_path)
        row_idx, ref_spl = select_best_row(freq_fr, dat_fr,
                                           BAND_LOW, BAND_HIGH, TARGET_SPL)

        print(f"  项目：{proj_name} | 声道：{chan} | "
              f"行：{row_idx} | 参考声压：{ref_spl:.1f} dB SPL")

        freq_thd, dat_thd, _ = read_channel(
            file_path, sheet_names["THD_L"], sheet_names["THD_R"])
        freq_rb,  dat_rb,  _ = read_channel(
            file_path, sheet_names["RB_L"],  sheet_names["RB_R"])

        def safe_row(data, idx):
            if data is None or idx >= data.shape[0]:
                return None
            return data[idx]

        projects.append({
            "name":      proj_name,
            "file_path": file_path,
            "channel":   chan,
            "row_idx":   row_idx,
            "ref_spl":   ref_spl,
            "freq_fr":   freq_fr,   "data_fr":  safe_row(dat_fr,  row_idx),
            "freq_thd":  freq_thd,  "data_thd": safe_row(dat_thd, row_idx),
            "freq_rb":   freq_rb,   "data_rb":  safe_row(dat_rb,  row_idx),
        })

    return projects
