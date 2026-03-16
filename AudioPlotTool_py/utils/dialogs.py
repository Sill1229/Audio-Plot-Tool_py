from __future__ import annotations
# -*- coding: utf-8 -*-
"""
dialogs.py  –  所有 tkinter 弹窗交互
"""

import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox

_PREF_FILE = os.path.join(os.path.expanduser("~"), ".audio_plot_tool_lastdir.json")

def _load_last_dir():
    try:
        with open(_PREF_FILE, "r") as f:
            return json.load(f).get("lastDir", "")
    except Exception:
        return ""

def _save_last_dir(path: str):
    try:
        with open(_PREF_FILE, "w") as f:
            json.dump({"lastDir": path}, f)
    except Exception:
        pass

def _yesno(title: str, message: str, default_yes: bool = False) -> bool:
    root = tk.Tk()
    root.withdraw()
    root.lift()
    result = messagebox.askyesno(title, message,
                                 default="yes" if default_yes else "no")
    root.destroy()
    return result


def ask_files() -> list:
    root = tk.Tk()
    root.withdraw()
    root.lift()

    last = _load_last_dir()
    if not last or not os.path.isdir(last):
        desk = os.path.join(os.path.expanduser("~"), "Desktop")
        candidate = os.path.join(desk, "Audio Test Data")
        last = candidate if os.path.isdir(candidate) else desk

    paths = filedialog.askopenfilenames(
        title      = "请选择一个或多个设备测试 Excel 文件（可多选）",
        initialdir = last,
        filetypes  = [("Excel 文件", "*.xlsx *.xls *.xlsm"), ("所有文件", "*.*")]
    )
    root.destroy()

    if not paths:
        return []

    file_list = list(paths)
    _save_last_dir(os.path.dirname(file_list[0]))
    print(f"已选择 {len(file_list)} 个文件。")
    return file_list


def ask_export_png() -> bool:
    val = _yesno("导出 PNG", "是否将所有对比图导出为 PNG 文件？")
    print(f"已选择：{'导出 PNG' if val else '不导出 PNG'}。")
    return val


def ask_harman() -> bool:
    val = _yesno("Harman 参考曲线", "是否在频率响应图中叠加 Harman Target 参考曲线？")
    print(f"已选择：{'叠加 Harman Target' if val else '不叠加 Harman Target'}。")
    return val


def ask_channel_mode() -> bool:
    """返回 True = L+R 双声道，False = 仅 L。"""
    root = tk.Tk()
    root.withdraw()
    root.lift()
    result = messagebox.askyesno(
        "声道选择",
        "是否同时显示 L + R 双声道？\n\n"
        "是 → L（实线）+ R（虚线）\n"
        "否 → 仅显示 L 声道",
        default="no"
    )
    root.destroy()
    label = "L + R 双声道" if result else "仅 L 声道"
    print(f"已选择：{label}。")
    return result


def ask_normalize() -> bool:
    val = _yesno("响度归一化",
                 "是否将所有曲线归一化到同一响度基准？\n\n"
                 "是 → 500–2000 Hz 均值对齐，只比较形状\n"
                 "否 → 保持真实响度差异")
    print(f"已选择：{'归一化响度' if val else '保持真实响度'}。")
    return val
