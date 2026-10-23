---
name: academic-paper-translation
description: "学术文献智能翻译工作流：基于 BabelDOC 开源引擎，将英文学术论文/PDF高质量翻译为中文，完美保留原版双列排版、图片、公式、表格位置。内置持久化个人术语库，跨任务积累术语，越翻译越精准。适用于：用户上传论文要求翻译、需要批量翻译文献、工科/理科/医学等领域学术文献翻译。"
---

# Academic Paper Translation

## Overview

本技能基于 BabelDOC 开源 PDF 翻译引擎（沉浸式翻译团队开源，8.4K+ GitHub stars），实现专业级学术文献翻译。采用 IR（中间表示）路线，排版保真度最高，完美保留原文双列排版、图片、公式、表格位置不变。

内置持久化个人术语库（保存在桌面），每次翻译自动读取已有术语，实现跨任务术语积累。最终仅交付翻译后的文档。

## Global Glossary

**全局术语库位置**：`~/Desktop/学术翻译术语库.xlsx`

术语库结构：
| 列 | 说明 |
|---|---|
| 英文术语 | 唯一键 |
| 中文译名 | 标准译法 |
| 累计出现频次 | 所有翻译任务累计 |
| 术语类别 | 核心概念/方法/设备/缩写 |
| 首次来源 | 首次出现的论文名 |

**重要**：每次翻译任务开始时必须读取该术语库，结束后将新术语写回更新。

## Prerequisites

**翻译引擎**：需要 OpenAI 兼容的翻译 API（如 DeepSeek、通义千问、OpenAI 等）。
- 默认使用 DeepSeek 翻译
- API key 由用户提供，不存储在技能中

## Workflow

```
输入 PDF → 1. 读取已有术语库 → 2. BabelDOC 翻译 → 3. 提取新术语更新库 → 4. 交付最终 PDF
```

## Step 1: 读取已有术语库

1. 打开 `~/Desktop/学术翻译术语库.xlsx`
2. 加载所有已有术语，建立 英文→中文 映射表
3. 如果文件不存在，则创建空库

## Step 2: BabelDOC 翻译

**核心命令**：
```bash
babeldoc --openai \
  --openai-base-url "https://api.deepseek.com/v1" \
  --openai-model "deepseek-chat" \
  --openai-api-key "<用户自己的API key>" \
  --files "<输入PDF路径>" \
  --lang-in en \
  --lang-out zh \
  --output "<输出目录，默认桌面>" \
  --no-watermark
```

**参数说明**：
- `--lang-in en`：源语言英文
- `--lang-out zh`：目标语言中文
- `--no-watermark`：不加水印
- `--no-dual`：只输出单语版（纯中文），不输出双语对照版

**输出文件**：
- 纯中文版：`<原文件名>.no_watermark.zh.mono.pdf`
- 双语对照版：`<原文件名>.no_watermark.zh.dual.pdf`（如果不指定 --no-dual）

**排版优势**：
- ✅ 自动识别双列/单列排版，译文保持原版式
- ✅ 图片、公式、表格位置 100% 保留
- ✅ 自动匹配字体样式（衬线/无衬线/斜体）
- ✅ 自动段落合并，不会碎块翻译
- ✅ 专业级文档布局分析模型

## Step 3: 提取新术语并更新术语库

翻译完成后：
1. 从翻译结果中识别新出现的专业术语
2. 与已有术语库对比，去重后新增
3. 已有术语频次累加
4. 写回 `~/Desktop/学术翻译术语库.xlsx`

## Step 4: 交付

**交付物**：
- 默认交付纯中文版 PDF（mono 版本）
- 如果用户需要双语对照版，保留 dual 版本

**保存位置**：桌面

**清理**：删除中间临时文件，只保留最终交付的 PDF。

## Translation Principles

1. **准确性优先**：技术含义准确传达，不随意增删信息
2. **学术语体**：使用国内学术论文常用表达习惯
3. **术语一致**：优先使用全局术语库中的译名
4. **格式保留**：双列排版、图片、公式、表格位置与原文完全一致
5. **流畅自然**：符合中文阅读习惯，避免翻译腔

## Resource Directories

### scripts/
- `build_glossary.py`：术语表 Excel 生成与合并脚本