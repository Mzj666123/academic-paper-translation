# Academic Paper Translation

基于 BabelDOC 开源引擎的学术论文 PDF 翻译技能，专为豆包办公 Agent 设计。

## ✨ 特性

- **完美排版保留**：自动识别双列/单列排版，译文保持原版式
- **图片公式不动**：图片、公式、表格位置 100% 保留原文位置
- **专业级布局分析**：基于深度学习模型的文档布局解析
- **全局术语库**：跨文档积累专业术语，越翻译越精准
- **自动段落合并**：不会碎块翻译，按完整段落翻译

## 📋 前置要求

1. **Python 3.10+**
2. **BabelDOC**：`pip install BabelDOC`
3. **翻译 API**：OpenAI 兼容接口（推荐 DeepSeek，便宜好用）

## 🚀 安装

### 1. 安装依赖

```bash
pip install BabelDOC pandas openpyxl
```

### 2. 安装技能

把整个文件夹放到豆包的 `.user_skills` 目录下：

```
~/.doubao/agent_mode/workspace/.user_skills/
└── academic-paper-translation/
    ├── SKILL.md
    └── scripts/
        └── build_glossary.py
```

### 3. 配置术语库

第一次使用会自动在桌面创建 `学术翻译术语库.xlsx`。

## 💡 使用

在豆包中直接说：
> "帮我翻译这篇论文"

然后上传 PDF 文件即可。

## 📁 项目结构

```
academic-paper-translation/
├── SKILL.md              # 技能主文件，定义工作流
├── scripts/
│   └── build_glossary.py # 术语库管理脚本
└── README.md             # 本文件
```

## 🙏 致谢

- [BabelDOC](https://github.com/funstory-ai/BabelDOC) — 沉浸式翻译团队开源的专业 PDF 翻译引擎
- 基于 IR（中间表示）路线，排版保真度最高

## 📄 License

MIT