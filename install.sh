#!/usr/bin/env bash
# 一键安装 tang-deep-research skill 到 ~/.claude/skills/tang-deep-research/
#
# 用法（公开仓库，curl 一键）：
#   curl -fsSL https://raw.githubusercontent.com/<owner>/tang-deep-research/main/install.sh | bash
#
# 或本地手动：
#   ./install.sh                # 默认装到 ~/.claude/skills/tang-deep-research
#   SKILL_DIR=/custom/path ./install.sh

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/tangtangniuniu/tang-deep-research.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"
SKILL_NAME="${SKILL_NAME:-tang-deep-research}"
SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills/$SKILL_NAME}"

# ---------- helpers ----------
log()  { printf '\033[1;36m[install]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[err]\033[0m %s\n' "$*" 1>&2; }

need() {
  command -v "$1" >/dev/null 2>&1 || { err "缺少命令：$1"; exit 1; }
}

# ---------- preflight ----------
need git
PYTHON="$(command -v python3 || command -v python || true)"
if [[ -z "$PYTHON" ]]; then
  warn "未发现 python3 / python，跳过 Python 依赖安装；后续 imagegen / HTML 渲染会报错"
fi

# ---------- fetch / sync ----------
mkdir -p "$(dirname "$SKILL_DIR")"

if [[ -d "$SKILL_DIR/.git" ]]; then
  log "已存在仓库 $SKILL_DIR，执行 git pull"
  git -C "$SKILL_DIR" fetch --depth=1 origin "$REPO_BRANCH"
  git -C "$SKILL_DIR" reset --hard "origin/$REPO_BRANCH"
elif [[ -e "$SKILL_DIR" ]]; then
  err "$SKILL_DIR 已存在但不是 git 仓库；请先备份或删除后重试"
  exit 1
else
  log "克隆 $REPO_URL 到 $SKILL_DIR"
  git clone --depth=1 --branch "$REPO_BRANCH" "$REPO_URL" "$SKILL_DIR"
fi

# ---------- python deps ----------
install_python_deps() {
  local pkgs=(python-pptx lxml jinja2 playwright)

  # 1) 旧系统 / macOS：用户级 pip 直接装
  if "$PYTHON" -m pip install --user --quiet --upgrade --disable-pip-version-check \
       "${pkgs[@]}" 2>/dev/null; then
    log "用户级 pip 安装成功"
    INSTALL_PY="$PYTHON"
    return 0
  fi

  # 2) PEP 668 / 系统 Python 锁死时：在 skill 目录建独立 venv
  log "系统 pip 拒绝直装（多半是 PEP 668）；改用 $SKILL_DIR/.venv 独立环境"
  if ! "$PYTHON" -m venv --help >/dev/null 2>&1; then
    err "缺少 python3-venv。请先：sudo apt install python3-venv  然后重跑 install.sh"
    return 1
  fi

  local venv="$SKILL_DIR/.venv"
  if [[ ! -d "$venv" ]]; then
    "$PYTHON" -m venv "$venv"
  fi
  if "$venv/bin/python" -m pip install --quiet --upgrade --disable-pip-version-check \
       pip "${pkgs[@]}"; then
    log "venv 安装成功：$venv"
    INSTALL_PY="$venv/bin/python"
    return 0
  fi

  # 3) 兜底：明确告知用户最后一招
  err "venv 安装失败。最后一招（自担风险）：
    $PYTHON -m pip install --break-system-packages --user ${pkgs[*]}"
  return 1
}

if [[ -n "$PYTHON" ]]; then
  log "安装 Python 依赖（python-pptx / lxml / jinja2 / playwright）"
  if install_python_deps; then
    if "$INSTALL_PY" -c "import playwright" >/dev/null 2>&1; then
      log "下载 Playwright Chromium（HTML 截图用，约 170MB）"
      "$INSTALL_PY" -m playwright install chromium >/dev/null 2>&1 || \
        warn "playwright install chromium 失败，HTML 渲染需要时再手动执行：
          $INSTALL_PY -m playwright install chromium"
    fi
  else
    warn "Python 依赖未就绪，渲染阶段会失败；请按上文提示处理后重试"
  fi
fi

# ---------- optional system deps ----------
if ! command -v vtracer >/dev/null 2>&1; then
  warn "未检测到 vtracer（imagegen 路径推荐）。可选安装：cargo install vtracer 或 pip install vtracer"
fi
if ! command -v potrace >/dev/null 2>&1; then
  warn "未检测到 potrace（imagegen 路径回退）。可选安装：sudo apt-get install potrace"
fi

# ---------- done ----------
log "✅ 安装完成：$SKILL_DIR"
log "在 Claude Code 中输入 /reload，然后用如下任一句子触发 skill："
cat <<'EOF'

  - 对 <主题> 做深度分析并生成 PPT
  - 用我提供的资料目录 <path> 做一份 <主题> 的调研幻灯片
  - 对 <主题> 做调研报告然后做成幻灯片

更多用法见仓库 README。
EOF
