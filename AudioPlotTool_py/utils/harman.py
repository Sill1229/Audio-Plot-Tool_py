from __future__ import annotations
# -*- coding: utf-8 -*-
"""
harman.py  –  加载 Harmancurve.mat 并对齐到参考曲线
"""

import os
import numpy as np
from scipy.io   import loadmat
from scipy      import interpolate


def load_harman(script_dir: str) -> tuple[np.ndarray | None, np.ndarray | None]:
    """
    在工程目录下查找 Harmancurve.mat，返回 (freq, spl)。
    支持字段名：f/SPL, freq/spl, Freq/SPL。
    """
    candidates = [
        os.path.join(script_dir, "Harmancurve.mat"),
        os.path.join(script_dir, "utils", "Harmancurve.mat"),
        os.path.join(script_dir, "data",  "Harmancurve.mat"),
    ]
    mat_file = next((p for p in candidates if os.path.isfile(p)), None)
    if mat_file is None:
        print("  [警告] 找不到 Harmancurve.mat，Harman Target 已跳过。")
        return None, None

    try:
        H = loadmat(mat_file)
    except Exception as e:
        print(f"  [警告] 无法加载 Harmancurve.mat：{e}")
        return None, None

    # 字段名匹配
    keys = [k for k in H.keys() if not k.startswith("_")]
    if "f" in keys and "SPL" in keys:
        hf, hs = H["f"].flatten().astype(float), H["SPL"].flatten().astype(float)
    elif "freq" in keys and "spl" in keys:
        hf, hs = H["freq"].flatten().astype(float), H["spl"].flatten().astype(float)
    elif "Freq" in keys and "SPL" in keys:
        hf, hs = H["Freq"].flatten().astype(float), H["SPL"].flatten().astype(float)
    elif len(keys) >= 2:
        hf = H[keys[0]].flatten().astype(float)
        hs = H[keys[1]].flatten().astype(float)
    else:
        print("  [警告] Harmancurve.mat 字段格式无法识别。")
        return None, None

    # 去重 + 排序
    _, uid = np.unique(hf, return_index=True)
    hf, hs = hf[uid], hs[uid]
    sidx   = np.argsort(hf)
    return hf[sidx], hs[sidx]


def align_harman(h_freq: np.ndarray, h_spl: np.ndarray,
                 ref_freq: np.ndarray, ref_data: np.ndarray,
                 x_lim: tuple[float, float],
                 align_band: tuple[float, float] = (500, 1000)
                 ) -> tuple[np.ndarray, np.ndarray]:
    """
    将 Harman 曲线插值到 ref_freq 轴，并在 align_band 频段内对齐声压。
    返回 (plot_freq, aligned_spl)。
    """
    mask  = (ref_freq >= x_lim[0]) & (ref_freq <= x_lim[1])
    pfreq = ref_freq[mask]
    pref  = ref_data[mask]

    f_interp = interpolate.interp1d(h_freq, h_spl, kind="linear",
                                    bounds_error=False, fill_value=np.nan)
    h_interp = f_interp(pfreq)

    # 对齐
    am = (pfreq >= align_band[0]) & (pfreq <= align_band[1])
    if np.any(am):
        ref_mean    = np.nanmean(pref[am])
        harman_mean = np.nanmean(h_interp[am])
        offset      = ref_mean - harman_mean
    else:
        offset = 0.0

    return pfreq, h_interp + offset
