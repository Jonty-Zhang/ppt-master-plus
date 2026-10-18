# PPT Master Plus

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Based on](https://img.shields.io/badge/based%20on-hugohe3%2Fppt--master%20v6.7.2-blue)](https://github.com/hugohe3/ppt-master)

基于 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 的增强版：让 AI 从文档生成可编辑的原生 PowerPoint，并且**交付得干净、换台电脑也不掉字体**。

> An enhanced fork of [PPT Master](https://github.com/hugohe3/ppt-master): one tidy delivery folder per deck, installed fonts embedded into the PPTX, and stricter layout defaults.

原项目的完整功能（生成流程、模板、图表、动画、配音等）全部保留，使用文档见[原项目 README](https://github.com/hugohe3/ppt-master#readme)。下面只写 Plus 多了什么。

## Plus 新增了什么

### 1. 一个文件夹交付，打开就是 PPT

原版做完一份 PPT，会在 `projects/<代号_日期>/` 里留下两百来个文件（每次导出的备份、预览图、检查报告、拆分讲稿……），成品藏在 `exports/` 里，名字是一串数字字母。

Plus 在最后一步自动打包成：

```text
第三季度经营分析/
├── 第三季度经营分析.pptx      ← 定稿，用标题命名
└── 制作文件/                        ← 以后要改 PPT 才用得上
    ├── 使用说明.md
    ├── 演讲稿.md
    ├── 幻灯片页面/                  每页的 SVG 源文件
    ├── 设计规范/                    配色、字体、每页规划、动画设置
    ├── 图标/  图片/  原始资料/
```

- 能自动重新生成的中间产物全部删掉（一份 27 页的 deck 实测从 206 个文件减到 53 个）。
- 定稿后不再修改，直接删掉「制作文件」就行，PPT 不受影响。
- 要改的时候对 AI 说「修改 <这个文件夹>」，它会从「制作文件」恢复工程，改完原地替换 PPT。你自己放进文件夹的其他文件不会被动。

### 2. 本机字体自动嵌入 PPT

PPT 用到的本机字体会嵌入到 `.pptx` 里，在没装这些字体的电脑上也能正常显示。

- **只嵌入用到的字**：思源宋体原文件 11MB，嵌入后约 230KB；一份 27 页的 deck 嵌入 5 款字体后只有 0.5MB。
- **自动转换格式**：OTF（CFF 轮廓）自动转成 PowerPoint 能加载的 TrueType 轮廓。
- **修正中文字体槽位**：原版导出时以 Windows 为目标，「思源宋体」「马善政」这类字体会被放进西文槽位，中文实际显示成微软雅黑。Plus 会把中文槽位改回设计字体，嵌进去的字体才真正被用上。
- **遵守字体授权**：OS/2 `fsType` 禁止嵌入的字体会跳过并提示；Windows 和 Mac 版 Office 都自带的字体（Arial、微软雅黑等）不重复嵌入。

PowerPoint（Windows / macOS 16.17+）会读取嵌入字体；Keynote、Google Slides 不读取。WPS 各版本支持程度不一，请自行测试。

### 3. 默认排版偏好

[`references/user-preferences.md`](./skills/ppt-master/references/user-preferences.md) 里有一组默认遵守的排版规则：

- 不加没必要的小字批注（听众早就知道的背景、页码互引、多余图例）。
- 在 1280×720 画布上，正文不小于 22px，说明文字不小于 18px。
- 页面稀疏时，用相关的线条、图形、图标来填，不靠放大字号或拉大间距。
- 背景不用纯色，加一层低透明度、跟随整体风格的矢量纹样。

用户在对话里明确提出的要求，优先于这些默认规则。

## 安装

需要 Python 3.10+。

```bash
git clone https://github.com/Jonty-Zhang/ppt-master-plus.git
cd ppt-master-plus
pip install -r requirements.txt
```

已经在用原版 skill 的话，用本仓库的 `skills/ppt-master/` 替换原来的 skill 文件夹（如 `~/.claude/skills/ppt-master`），再重新执行一次 `pip install -r requirements.txt`（Plus 新增依赖 `fonttools`）。

然后在 Claude Code 等 Agent 里打开这个文件夹，说「用 ppt-master 把 xxx 做成 PPT」即可。

## 新增的文件

| 文件 | 作用 |
|---|---|
| [`scripts/deliver.py`](./skills/ppt-master/scripts/deliver.py) | `pack` 打包交付（嵌入字体、整理文件夹、清理中间产物），`unpack` 从交付文件夹恢复工程 |
| [`scripts/pptx_embed_fonts.py`](./skills/ppt-master/scripts/pptx_embed_fonts.py) | 把本机字体子集化后嵌入任意 `.pptx`，也可以单独使用 |
| [`workflows/stages/deliver.md`](./skills/ppt-master/workflows/stages/deliver.md) | 交付阶段的流程说明，已接入默认流程（Step 7.4）和 Quick 流程 |
| [`references/user-preferences.md`](./skills/ppt-master/references/user-preferences.md) | 默认排版偏好 |

单独给已有的 PPT 嵌入字体：

```bash
python3 skills/ppt-master/scripts/pptx_embed_fonts.py 你的文件.pptx --dry-run   # 先看会嵌入哪些字体
python3 skills/ppt-master/scripts/pptx_embed_fonts.py 你的文件.pptx -o 输出.pptx
```

## 致谢与协议

本项目 fork 自 Hugo He 的 [PPT Master](https://github.com/hugohe3/ppt-master)，生成流程、模板和绝大部分代码都来自原项目，感谢原作者的开源。如果觉得好用，也请去原项目点个 Star。

沿用原项目的 [MIT 协议](./LICENSE)。
