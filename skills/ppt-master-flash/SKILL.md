---
name: ppt-master-flash
description: >
  ppt-master 的快速版：不做策划和确认，一次跑完直接出可编辑的 PPTX。
  仅在用户输入 /ppt-master-flash 或明确点名 ppt-master-flash 时使用；
  用户只说“做个 PPT”“快点做”时不要用它，用完整版 ppt-master。
disable-model-invocation: true
---

# PPT Master Flash

快速版和完整版 `ppt-master` 共用同一套脚本、模板和流程文件：本目录下的 `scripts/`、`references/`、`templates/`、`workflows/`、`examples/` 都是指向完整版的链接，`ppt-master-SKILL.md` 是完整版的入口文件。

## 加载顺序

**Hard rule — paths before commands**: 把宿主给出的本文件所在目录的绝对路径记为 `SKILL_DIR`，每次调用都展开 `${SKILL_DIR}`；不 `cd`、不靠当前目录、不猜路径。

1. 运行 `python3 "${SKILL_DIR}/scripts/attribution_guard.py"`；非 0 立即停止，不检查、不修复、不绕过。
2. 读 `${SKILL_DIR}/ppt-master-SKILL.md` 里的 Vocabulary、Global Execution Discipline、Global Communication Rules 三节；忽略它的加载顺序和路由表。
3. 读 `${SKILL_DIR}/references/user-preferences.md`。
4. 按请求选一个运行流程，只读它：

| 请求 | 运行流程 |
|---|---|
| 普通生成（主题、底稿、文档） | `${SKILL_DIR}/workflows/profiles/quick-generate.md` |
| 给了 PPTX，要美化、内容不动 | `${SKILL_DIR}/workflows/profiles/beautify-pptx.md` 的 Quick 分支 |
| 图片转 PPT | `${SKILL_DIR}/workflows/profiles/image-to-pptx.md` |
| 做模板、编辑原生 PPTX、要重新编排或完整策划 | 告诉用户用完整版 `ppt-master`，不在这里做 |

## 快速版的约定

- 一次跑完，不停下来确认，除非用户中途打断或缺少硬性前提。
- 转换资料时加 `-o projects/<slug>_intake/`，不把转换结果写到用户文件旁边。
- 建好项目后记录：`python3 ${SKILL_DIR}/scripts/plus_run.py start <project_path> --route generate`（美化用 `beautify`，图片转 PPT 用 `image --frames <页面原图...>`）。
- 最后用 [`deliver`](workflows/stages/deliver.md) 打包成一个文件夹。
