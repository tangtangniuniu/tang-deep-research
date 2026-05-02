# tang-deep-research

> Claude Code skill：从主题/资料到**可编辑 PPTX** 的深度分析流水线。
> 支持三种素材来源（参考文档目录 / 联网调研 / 混合），双渲染分支（HTML 模板 / imagegen2）。
> 默认输出**简体中文**，幻灯片默认 25 页（12–35 可调）。

---

## 一键安装

> 仓库需要为 public，下方命令才能直接 `curl | bash`。私有仓库请改用"手动安装"。

```bash
curl -fsSL https://raw.githubusercontent.com/tangtangniuniu/tang-deep-research/main/install.sh | bash
```

安装后在 Claude Code 里输入 `/reload`，技能即可被发现。

### 自定义安装路径

```bash
SKILL_DIR=$HOME/my-skills/tang-deep-research \
  curl -fsSL https://raw.githubusercontent.com/tangtangniuniu/tang-deep-research/main/install.sh | bash
```

### 手动安装（私有仓库或离线环境）

```bash
git clone https://github.com/tangtangniuniu/tang-deep-research.git \
  ~/.claude/skills/tang-deep-research
cd ~/.claude/skills/tang-deep-research
bash install.sh   # 仅装依赖
```

### 卸载

```bash
rm -rf ~/.claude/skills/tang-deep-research
```

---

## 触发示例

```
对大模型 Agent 技术做深度分析并生成 PPT
用我本地的 ./refs 目录做一份"国产 GPU 生态"的调研幻灯片
对网络运维认知智能做调研报告然后做成幻灯片
```

技能在 **Stage 0** 会先与你确认三件事：

1. **主题** — 例 "大模型 Agent 技术"
2. **资料来源** — `refs`（你的目录）/ `deep-research`（联网）/ `hybrid`（两者）
3. **渲染模式** — `mixed`（默认）/ `html` / `imagegen`

确认后写到 `run.config.json`，逐阶段产出可见。

---

## 流水线一览

```
Stage 0  入口对话         → run.config.json
Stage 1  素材整理         → raw/<NN>-<slug>.md
Stage 2  分析与切片       → analysis/outline.md, analysis/slides.json
Stage 3  主题专属 prompt  → out/<主题>深度分析ppt生成prompt.md
Stage 4  渲染（双分支）    → html/slide-*.html, images/png/slide-*.png
                          imagegen 路径再走 images/svg/
Stage 5  装配             → out/<主题>.pptx
```

每个 Stage 都有 checkpoint，需要你点头再继续，避免黑盒一口气跑完。

---

## 目录结构

```
tang-deep-research/
├── SKILL.md                      # 技能入口（被 Claude Code 加载）
├── install.sh                    # 一键安装脚本
├── README.md
├── example.md                    # 素材风格参考
├── ppt_大纲.md                   # 通用大纲的素材原型（供溯源）
├── references/
│   ├── outline_template.md       # 通用 25 页大纲（占位符版）
│   ├── gathering.md              # 三条素材路径（refs / deep-research / hybrid）
│   ├── analysis.md               # 切片 schema + 主题专属 prompt 规则
│   ├── imagegen.md               # imagegen prompt scaffold
│   ├── html_render.md            # HTML 渲染分支
│   └── assembly.md               # 矢量化 + PPTX 装配
└── scripts/
    ├── png_to_svg.py             # PNG → SVG（vtracer / potrace / wrapper 三档兜底）
    ├── html_to_pptx.py           # HTML 渲染辅助（render / shoot / compose）
    └── build_pptx.py             # 由 slides.json + 背景图装配 PPTX
```

---

## 依赖

`install.sh` 自动安装：

| 依赖 | 用途 |
|---|---|
| `python-pptx`、`lxml` | 装配 PPTX |
| `jinja2` | HTML 模板渲染 |
| `playwright` + Chromium | HTML 截图 |

可选系统级依赖（imagegen 路径效果更好时再装）：

| 依赖 | 用途 |
|---|---|
| `vtracer`（`cargo install vtracer` 或 `pip install vtracer`） | 彩色矢量化 |
| `potrace`（`sudo apt install potrace`） | 单色矢量化兜底 |

---

## 开发与贡献

```bash
git clone git@github.com:tangtangniuniu/tang-deep-research.git
cd tang-deep-research
# 改 SKILL.md / references/* / scripts/*
# 提 PR
```

模板库 `html/templates/<id>.html.j2` 可继续扩充：建议每加一个模板同步在
`references/html_render.md` 末尾的"模板库"清单里登记。

---

## License

MIT
