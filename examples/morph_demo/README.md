# 原生平滑（Morph）过渡三页演示示例

本示例展示基于 PowerPoint 原生 Morph 转场能力与对象显式配对（`morph.pairs`）的连续变形效果。

## 页面结构与平滑演进

1. **第 1 页 (`01_overview.svg`)**：
   - 核心卡片 `hero-card` 位于左侧，深青色填充，展示基础说明。
   - 状态徽章 `status-badge` 位于左上方，水平角度 0°，绿色。
   - 专属说明卡片 `intro-aside` 位于右侧。

2. **第 2 页 (`02_focus.svg`)**：
   - 转场配置：`"transition": { "effect": "平滑", "duration": 0.8 }`（测试中文名称“平滑”归一化为原生 Morph）。
   - 核心卡片 `hero-card` 连续移动至画面中央并放大，填充由深青色平滑过渡至紫色，文字同步演进。
   - 状态徽章 `status-badge` 移动至中央上方，并旋转 +8°。
   - 第 1 页独有的 `intro-aside` 自然淡出移除；底部新增指标卡片 `metric-stat`。

3. **第 3 页 (`03_summary.svg`)**：
   - 转场配置：`"transition": { "effect": "smooth", "duration": 0.8 }`（测试英文别名“smooth”归一化为原生 Morph）。
   - 核心卡片 `hero-card` 变形为顶部汇总横幅，填充色过渡为深靛蓝色。
   - 状态徽章 `status-badge` 移动至右上角，旋转角度归位为 0°，填充色变为金色。
   - 第 2 页的 `metric-stat` 自然淡出；新增 `summary-grid` 三列行动清单。

## 验证与导出

在项目根目录下，先执行最终质量检查生成合规报告，再执行 Quick Generate 导出：

```bash
# 1. 运行 lockless final quality checker 生成指纹报告
python skills/ppt-master/scripts/svg_quality_checker.py examples/morph_demo --quick-generate --canonical-authoring --stage final --json

# 2. 导出原生 PPTX（带平滑转场及原生 !! 对象命名）
python skills/ppt-master/scripts/svg_to_pptx.py examples/morph_demo --quick-generate --no-notes
```

该流程将：
1. 校验 `animations.json` 中“平滑”与“smooth”统一归一化为原生 Morph；
2. 为配对对象自动写入 PowerPoint 原生强制匹配前缀 `!!hero-card` 与 `!!status-badge`；
3. 输出 PPTX 并自动执行 `validate_pptx_morph_pairs` 包内 XML 回读校验。

## 播放与兼容性说明

- **原生支持**：现代 Microsoft 365 / PowerPoint 2019+ 原生识别 `<p159:morph option="byObject"/>` 转场及 `!!` 命名前缀，实现平滑移动、缩放、旋转与属性渐变。
- **降级回退**：不支持 Morph 的旧版 Office PowerPoint（如 2013 或早期版本）将依据 OOXML 扩展回退规范，安全回退为常规淡化（Fade）转场，不影响内容呈现与编辑。
- **测试边界**：本次已完成静态 XML 生成解析与自动化结构包完整性断言（包括解包确认 `slide2/3.xml` 的 `p159:morph` 及三页的 `!!` 形状名），未在本地运行 Microsoft Office 客户端进行交互放映实际观察。
