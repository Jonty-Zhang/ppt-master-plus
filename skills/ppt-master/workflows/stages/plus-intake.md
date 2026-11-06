---
description: Plus 开工流程——必问问题、逐页文案确认、开工记录；完整版 ppt-master 的普通生成和 PPTX 美化/改造在读运行流程前先读本文件。
---

# Plus 开工流程

> 只属于完整版 `ppt-master`；快速版 `ppt-master-flash` 不读本文件。本文件补充原版流程，不替换原版 Stage 1 / Stage 2 确认。

## 1. 什么时候用

| 请求 | 做法 |
|---|---|
| 普通生成（一句话、底稿、已逐页设计好的稿子） | §2 → Step 1 → Step 2 + §3 → §4 → 原版 Step 3 起 |
| 用户给了 PPTX 要改好 | §2（含改造档位）；`style` 走 [`beautify-pptx`](../profiles/beautify-pptx.md) 的 Default，`pptx-reedit` / `pptx-rebuild` 把 PPTX 当素材走普通生成 |
| 图片转 PPT | 只做 §6 |
| 用户说“快一点”“直接做”“跳过确认” | 仍走完整版；告诉用户快速版是 `/ppt-master-flash`，要不要切换由用户自己决定 |

## 2. 必问问题（开工前一次问完）

在对话里用用户的语言一次问完。每题给推荐答案和一句理由；用户回“按推荐的来”就采用推荐。用户没回答的题不能替用户回答。

| key | 问题 | 取值 |
|---|---|---|
| `start_point` | 手里有什么：逐页设计好的稿子（每页内容、配图、要画的插画都写好了）/ 一份底稿 / 只有一句话或一小段 | `designed` / `draft` / `topic`；PPTX 改造用下面的档位值 |
| 改造档位 | （仅给了 PPTX）改到什么程度：只换样式 / 重新编排（文字尽量保留，可拆页合页、调序、删冗余）/ 当素材重做 | `style` 记为 `level`；后两档记为 `start_point`：`pptx-reedit` / `pptx-rebuild` |
| `audience_style` | 给谁看、整体风格 | 一句话 |
| `page_count` | 大约几页 | 数字或范围；`style` 档沿用原页数，不问 |
| `ai_images` | 要不要用 AI 生图 | `yes` / `no` |
| `advanced_animation` | 要不要平滑切换（Morph）等复杂动画 | `yes` / `no` |

**改造档位**：先通读原 PPT，说清哪几页太满、重复或顺序乱，再推荐档位。任何档位都不改数字、图表数据、人名地名，除非用户明确要求。

**和原版确认的关系**：这些答案是原版 Stage 1 / Stage 2 对应字段（受众与意图、视觉风格、页数、图片来源、自定义动画）的预填推荐；Stage 1 / Stage 2 照常确认，不在对话里重复问同一件事。

**专业问题（按需 0–4 个，在 Stage 2 之前）**：题材视觉空间大或用户在意设计时追加，例如版式节奏、贯穿全篇的视觉母题、图片处理方式、数据呈现方式。每题先说选不同答案页面会怎么变，再给推荐和理由；能给色块、字体或构图小样就给。用户可以回“你定”。

## 3. 开工记录

Step 1 转换资料时一律加 `-o projects/<slug>_intake/`，不把转换结果写到用户文件旁边；Step 2 建好项目、导入资料后立刻记录：

```bash
python3 ${SKILL_DIR}/scripts/plus_run.py start <project_path> --route generate --answers '<json>'
```

`style` 档用 `--route beautify`。答案改了就重新 `start`。

## 4. 逐页文案（Step 2 之后、Step 3 之前）

| 起点 | 做法 |
|---|---|
| `designed` | 用户稿子里的每页内容、配图、插画原样作为页面计划；只在稿子标明的缺口处补搜；不写 `page_copy.md` |
| `draft` | 按底稿写 `<project_path>/page_copy.md`，只为缺口做少量搜索 |
| `topic` | 先跑 [`topic-research`](./topic-research.md) 广泛搜集，再写 `page_copy.md` |
| `pptx-reedit` | 写 `page_copy.md`，每页并排列出原文和新文案，标出拆页、合页、调序、删减 |
| `pptx-rebuild` | 同 `draft`，原 PPTX 当素材 |

`page_copy.md` 每页写标题、要点文案、配图或插画想法。给用户看、按意见改，用户明确同意后：

```bash
python3 ${SKILL_DIR}/scripts/plus_run.py confirm-copy <project_path>
```

之后 Strategist §IX 的页面内容以确认过的文案为准。文案再改要重新给用户确认并重新 `confirm-copy`，否则导出会被拒绝。

## 5. AI 生图（`ai_images: yes`）

Stage 2 图片来源包含 `ai`，获取路径用原版 `auto`；怎么画按 [`user-preferences.md`](../../references/user-preferences.md) §7。用户选了 `no` 就不推荐 `ai`。

## 6. 图片转 PPT

开工前先看有没有“参照原图改图”的能力（`IMAGE_BACKEND` 为 openai / gemini，或宿主自带改图工具）；都没有就先告诉用户，需要改图的图层会卡住导出，问要不要继续。整理好页面原图后记录：

```bash
python3 ${SKILL_DIR}/scripts/plus_run.py start <project_path> --route image --frames <项目里的页面原图...>
```

## 7. 导出检查

`svg_to_pptx.py` 导出前检查开工记录：缺记录、缺必问答案、文案没确认或确认后又改过、完整版里对普通生成或美化用 `--quick-generate`，都会拒绝导出。按提示补上缺的步骤，不要绕过。`deliver.py unpack` 恢复的修改轮自动带记录。
