# AudioPlotTool  –  Python 版

多设备音频测试对比工具，Python 重构版。包含两个独立工具：

| 工具 | 说明 |
|---|---|
| `AudioPlotTool`（主工具） | 多设备 / 多音量频响对比，含 THD / Rub&Buzz / Leakage |
| `AR_Glasses_FR_Plot Compare Harman.py` | AR 眼镜频响 vs 哈曼目标曲线，输出概览图 + 调音参考图 |

---

## 首次运行注意事项（macOS）

macOS 会拦截从网络下载的未签名应用，**首次使用前必须在终端运行以下两条命令**解除限制（路径替换为你实际的解压路径）：

```bash
xattr -rd com.apple.quarantine "/你的路径/AudioPlotTool_py/AudioPlotTool.app"
chmod +x "/你的路径/AudioPlotTool_py/AudioPlotTool.app/Contents/MacOS/AudioPlotTool"
```

例如放在桌面的 `Audio Tools` 文件夹里：

```bash
xattr -rd com.apple.quarantine "/Users/你的用户名/Desktop/Audio Tools/AudioPlotTool_py/AudioPlotTool.app"
chmod +x "/Users/你的用户名/Desktop/Audio Tools/AudioPlotTool_py/AudioPlotTool.app/Contents/MacOS/AudioPlotTool"
```

> 解除后**右键 → 打开**，弹窗点「打开」即可。之后每次直接双击运行。

---

## 运行方式

### 方式一：双击 App（推荐）

解除限制后，双击 `AudioPlotTool.app` 即可启动，会自动弹出终端窗口运行程序。

### 方式二：终端运行

```bash
bash /path/to/AudioPlotTool_py/install_and_run.sh
```

首次运行会自动安装 Python 3.11 和依赖，之后跳过直接启动。

---

## 目录结构

```
AudioPlotTool_py/
├── AudioPlotTool.app                        ← 双击启动（macOS）
├── AR_Glasses_FR_Plot Compare Harman.py     ← AR 眼镜调音分析工具
├── install_and_run.sh                       ← 终端启动脚本
├── main.py                                  ← 主入口
├── requirements.txt                         ← Python 依赖
├── Harmancurve.mat                          ← Harman 参考曲线（内嵌于 AR 工具，此处备用）
└── utils/
    ├── dialogs.py          弹窗交互（tkinter）
    ├── reader.py           Excel 读取
    ├── project_builder.py  数据结构构建
    ├── harman.py           Harman 曲线加载与对齐
    ├── plot_style.py       公共绘图样式
    ├── plot_single.py      单设备多音量绘图引擎
    ├── plot_compare.py     多设备对比绘图引擎
    └── exporter.py         PNG 导出
```

---

## 依赖环境

- Python 3.10+（`install_and_run.sh` 会自动安装 3.11）
- 依赖库：matplotlib / numpy / openpyxl / scipy

---

## Harman Target

将 `Harmancurve.mat` 放到工程根目录（与 `main.py` 同级）。
支持字段名：`f/SPL`、`freq/spl`、`Freq/SPL`。

---

## Excel 格式要求

| Sheet 名 | 内容 |
|---|---|
| `Freqresp -ear L/R` | 频率响应 |
| `THD 2-5 -ear L/R` | THD |
| `Rub&Buzz Harmonic 10-35 -ear L/R` | Rub & Buzz |

第1行表头，第2行起每行一次 sweep 测量数据。

---

## AudioPlotTool 两种模式

| 选择文件数 | 模式 |
|---|---|
| 1 个 | 单设备多音量：所有 sweep 全部画出，冷暖色区分音量高低 |
| 2+ 个 | 多设备对比：每台设备取最接近 75 dB SPL 的档位，可选响度归一化 |

---

## AR_Glasses_FR_Plot Compare Harman.py

AR 眼镜扬声器频响分析工具，独立运行，无需其他模块。

**用法：**
```bash
python3 "AR_Glasses_FR_Plot Compare Harman.py"
```

运行后弹窗选择 AP 导出的 Excel 文件，自动输出两张图到 `/Users/sly/Desktop/Audio Test Export/`：

| 输出文件 | 内容 |
|---|---|
| `文件名_overview.png` | H_glass(f) 与哈曼目标曲线概览（50Hz–20kHz） |
| `文件名_tuning.png` | 调音参考图 ΔH(f)（200Hz–20kHz，1 dB 刻度，正负填色） |

**选行逻辑：** 读取 `Freqresp -ear L` sheet，取 1kHz 处 SPL 最接近 75 dBSPL 的那行 sweep。

**依赖：** `matplotlib` / `numpy` / `openpyxl`（哈曼曲线已内嵌，无需 `.mat` 文件）
