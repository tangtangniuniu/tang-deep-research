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
if [[ -n "$PYTHON" ]]; then
  log "安装 Python 依赖（python-pptx / lxml / jinja2 / playwright）"
  "$PYTHON" -m pip install --user --quiet --upgrade \
    python-pptx lxml jinja2 playwright || warn "pip install 失败，请手动重试"

  if "$PYTHON" -c "import playwright" >/dev/null 2>&1; then
    log "下载 Playwright Chromium（用于 HTML 截图）"
    "$PYTHON" -m playwright install chromium >/dev/null 2>&1 || \
      warn "playwright install chromium 失败，HTML 渲染需要时再手动执行"
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
