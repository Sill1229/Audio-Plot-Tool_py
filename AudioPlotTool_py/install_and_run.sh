#!/bin/bash
# =========================================================
#  install_and_run.sh
#  自动安装 Python 3.11 + 依赖，然后启动 AudioPlotTool
#  使用方式：bash install_and_run.sh
# =========================================================

set -e
cd "$(dirname "$0")"

VENV_DIR=".venv"
PYTHON_VERSION="3.11"
PYTHON_BIN="python${PYTHON_VERSION}"

echo "================================================="
echo "  AudioPlotTool 安装 & 启动脚本"
echo "================================================="

# ── 1. 检查 / 安装 Homebrew ─────────────────────────────
if ! command -v brew &> /dev/null; then
    echo ""
    echo "📦 未检测到 Homebrew，正在安装..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Apple Silicon 需要额外配置 PATH
    if [ -f "/opt/homebrew/bin/brew" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    fi
    echo "✅ Homebrew 安装完成。"
else
    echo "✅ Homebrew 已安装：$(brew --version | head -1)"
fi

# ── 2. 检查 / 安装 Python 3.11 ──────────────────────────
if ! command -v $PYTHON_BIN &> /dev/null; then
    echo ""
    echo "📦 未检测到 Python ${PYTHON_VERSION}，正在安装..."
    brew install python@${PYTHON_VERSION}

    # 确保 PATH 里能找到
    BREW_PREFIX=$(brew --prefix)
    export PATH="${BREW_PREFIX}/opt/python@${PYTHON_VERSION}/bin:$PATH"
    echo "✅ Python ${PYTHON_VERSION} 安装完成。"
else
    echo "✅ Python 已安装：$($PYTHON_BIN --version)"
fi

# 再次确认能找到
if ! command -v $PYTHON_BIN &> /dev/null; then
    BREW_PREFIX=$(brew --prefix)
    export PATH="${BREW_PREFIX}/opt/python@${PYTHON_VERSION}/bin:$PATH"
fi

if ! command -v $PYTHON_BIN &> /dev/null; then
    echo "❌ Python ${PYTHON_VERSION} 仍未找到，请重启终端后再试。"
    exit 1
fi

# ── 3. 创建 / 更新虚拟环境 ──────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "📦 创建虚拟环境（使用 Python ${PYTHON_VERSION}）..."
    $PYTHON_BIN -m venv "$VENV_DIR"
    echo "✅ 虚拟环境创建完成。"
else
    # 检查虚拟环境的 Python 版本是否满足要求
    VENV_PY_VER=$("$VENV_DIR/bin/python" --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    REQUIRED="3.10"
    if [ "$(printf '%s\n' "$REQUIRED" "$VENV_PY_VER" | sort -V | head -1)" != "$REQUIRED" ]; then
        echo ""
        echo "⚠️  现有虚拟环境 Python 版本过低（${VENV_PY_VER}），重新创建..."
        rm -rf "$VENV_DIR"
        $PYTHON_BIN -m venv "$VENV_DIR"
        echo "✅ 虚拟环境重建完成。"
    else
        echo "✅ 虚拟环境已存在（Python ${VENV_PY_VER}）。"
    fi
fi

# ── 4. 激活虚拟环境并安装依赖 ───────────────────────────
source "$VENV_DIR/bin/activate"

echo ""
echo "🔍 安装 / 更新依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ 依赖已就绪。"

# ── 5. 启动主程序 ────────────────────────────────────────
echo ""
echo "🚀 启动 AudioPlotTool..."
echo ""
python main.py

deactivate
