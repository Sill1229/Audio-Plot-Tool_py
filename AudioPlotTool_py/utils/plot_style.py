from __future__ import annotations
# -*- coding: utf-8 -*-
"""
plot_style.py  –  公共绘图样式和辅助函数
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.font_manager as fm
import colorsys
import platform

# ── 中文字体配置 ──────────────────────────────────────────
def _setup_chinese_font():
    """按系统自动选择可用的中文字体。"""
    sys = platform.system()
    candidates = []
    if sys == "Darwin":
        candidates = ["PingFang SC", "Heiti SC", "STHeiti", "Arial Unicode MS"]
    elif sys == "Windows":
        candidates = ["Microsoft YaHei", "SimHei", "SimSun"]
    else:
        candidates = ["WenQuanYi Micro Hei", "Noto Sans CJK SC", "DejaVu Sans"]

    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            return
    # 兜底：中文可能显示为方块，给出一次提示
    print("  [提示] 未找到中文字体，汉字可能显示为方块。"
          "可安装 PingFang SC / Microsoft YaHei 等字体后重试。")
    plt.rcParams["axes.unicode_minus"] = False

_setup_chinese_font()
plt.rcParams["axes.unicode_minus"] = False


# ── 颜色 ─────────────────────────────────────────────────

# 多设备对比色板（高区分度）
COMPARE_COLORS = [
    "#1f77b4",  # 蓝
    "#ff7f0e",  # 橙
    "#2ca02c",  # 绿
    "#d62728",  # 红
    "#9467bd",  # 紫
    "#8c564b",  # 棕
    "#e377c2",  # 粉
    "#7f7f7f",  # 灰
]


def warm_cold_colors(n: int) -> list[tuple]:
    """
    生成 n 个冷暖渐变颜色：
    低音量（k=0）→ 蓝冷，高音量（k=n-1）→ 红暖
    """
    colors = []
    for k in range(n):
        t = k / max(n - 1, 1)
        h = 0.67 * (1 - t)   # 蓝=0.67, 红=0
        r, g, b = colorsys.hsv_to_rgb(h, 0.85, 0.92)
        colors.append((r, g, b))
    return colors


# ── Metric 配置（供 plot_single / plot_compare 共用）─────────
METRIC_CFG = {
    "FR":      {"title": "Frequency Response",          "x_lim": (50, 20000),   "y_min": 20,  "is_fr": True},
    "THD":     {"title": "THD",                         "x_lim": (100, 10000),  "y_min": 0,   "is_fr": False},
    "RB":      {"title": "Rub & Buzz",                  "x_lim": (100, 10000),  "y_min": 0,   "is_fr": False},
    "LEAKAGE": {"title": "Leakage Control (Isolation)",  "x_lim": (500, 5000),   "y_min": 0,   "is_fr": False},
}


# ── 坐标轴格式 ────────────────────────────────────────────

def fmt_hz(val, _pos=None) -> str:
    if val >= 1000:
        return f"{val/1000:g}k"
    return f"{val:g}"


def apply_log_xaxis(ax, x_lim: tuple[float, float]):
    """设置对数 X 轴，加刻度和标签。"""
    ax.set_xscale("log")
    ax.set_xlim(x_lim)

    ticks = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
    ticks = [t for t in ticks if x_lim[0] <= t <= x_lim[1]]
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(fmt_hz))
    ax.xaxis.set_minor_formatter(ticker.NullFormatter())

    ax.set_xlabel("Frequency (Hz)", fontsize=13)
    ax.grid(True, which="major", alpha=0.25, linewidth=0.7)
    ax.grid(True, which="minor", alpha=0.10, linewidth=0.4)


def style_axes(ax):
    """通用坐标轴样式。"""
    ax.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)
    ax.tick_params(labelsize=10)


def auto_ymax(max_val: float, is_fr: bool = False) -> float:
    """
    FR：最大值 + 10，向上取整到 10 的倍数。
    THD / RB：直接向上取整到 10 的倍数。
    """
    if is_fr:
        return np.ceil((max_val + 10) / 10) * 10
    else:
        return np.ceil(max_val / 10) * 10


def make_figure(title: str) -> tuple:
    """创建标准 figure 和 axes。"""
    fig, ax = plt.subplots(figsize=(12, 6.5))
    fig.patch.set_facecolor("white")
    if hasattr(fig.canvas, "manager") and fig.canvas.manager is not None:
        fig.canvas.manager.set_window_title(title)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    return fig, ax


def clip(freq: np.ndarray, y: np.ndarray,
         x_lim: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]:
    """裁剪数据到绘图范围。"""
    if freq is None or y is None:
        return np.array([]), np.array([])
    mask = (freq >= x_lim[0]) & (freq <= x_lim[1])
    return freq[mask], y[mask]
