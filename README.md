# 创作者选题脚本助手

把 AI 信息源和零散资料，整理成有出处的选题卡，再推进到口播初稿与镜头清单。

**多源发现 → 深度查证 → 选题判断 → 口播初稿 → 镜头清单**

`creator-topic-script` 是供 AI 助手读取的 Skill，默认中文、短视频默认 90 秒。用户已经指定的时长、平台、选题和输出格式优先。

## 适合怎么用

| 你要做什么 | 交付内容 |
|---|---|
| 找今天或本周值得讲的 AI 话题 | 有来源、有推荐理由的选题卡 |
| 研究某个产品、论文或开源项目 | 原始证据、比较条件、可讲角度与待核实问题 |
| 整理自己的链接、笔记和 brief | 资料摘要与最多 3 张备稿选题卡 |
| 把选定方向写成视频 | 口播初稿、对应镜头、待补素材 |
| 只改口播或换一种发布形式 | 按明确要求交付，不重复整套选题流程 |

## 开始使用

下载仓库 ZIP，解压后将包含 `SKILL.md` 的文件夹命名为 `creator-topic-script`。在支持 Skill 导入的助手中按其说明导入整个文件夹；也可以先让具备本地文件读取能力的助手读取 `SKILL.md`，再提交任务。

宿主支持按名称调用时，可以使用以下示例。不同宿主的安装路径、发现机制和调用语法以其实际说明为准。

**用自己的资料备稿**

```text
用 $creator-topic-script 整理我附的 brief 和笔记，
面向刚开始做内容的人，先给 3 个有出处、有画面依据的方向。
```

**从选题继续写稿**

```text
选 T01，写成 90 秒口播和镜头清单，优先用我已经提供的材料。
```

**直接完成一个主题**

```text
用 $creator-topic-script 研究这个主题。
你选最有依据的角度，直接写完 90 秒口播和镜头清单。
```

**只要口播**

```text
保留刚才选定的方向，只给 90 秒口播，不用再列选题卡。
```

**发现近期 AI 话题**

```text
用 $creator-topic-script 看看过去 24 小时有什么适合 AI 创作者讲的内容。
给我 3 张选题卡，说明读过哪些来源、证据在哪、可以拍什么。
```

这些是使用示例，不是一次已经完成的在线扫描或运行结果。

## 工作方式

- **先核对资料。** 区分原文已读、部分已读和未读，保留来源与主张的对应关系。
- **按问题深入。** 从官方原文、机制操作、对比限制和缺口补查中选择必要步骤，不强制每个任务跑完全部来源。
- **让选题有依据。** 看观众价值、证据、自己的新增解释和可拍画面，不输出伪造的爆款概率。
- **沿用已有选择。** 用户选定方向后继续写；授权直接选题写完时不再重复确认。
- **把稿子接到画面。** 标明哪些素材已有、哪些待拍，避免把未测试的功能写成实测结果。

有合作 brief 时，按当前项目核对品牌名称、必带文案、时长、CTA 与交付要求。具体合作资料由使用者在自己的项目中提供。

## 需要什么

Skill 本身为 Markdown 指令，不是独立运行的新闻采集服务或视频生成软件。

需要能读取 Skill 文件的 AI 助手。在线发现与查证依赖宿主实际提供的搜索或网页读取工具；没有联网工具时，仍可整理用户提供的可读资料，并说明来源覆盖范围。

可选检查工具需要 **Python 3.9+**，仅使用标准库。它检查已声明的记录关系与估算口播时长，不联网、不修改输入、不判断原文是否真的支持结论。

## 可选本地检查

在仓库目录运行：

```bash
python3 scripts/check_work.py duration /path/to/voiceover.txt --target 90 --pause 10
python3 scripts/check_work.py check /path/to/record.json
```

将示例路径替换成实际文件。记录格式见 [record-format.md](references/record-format.md)。口播文件仅放正文；估时不是实际录音时长，最终需要试读。

运行现有检查器测试：

```bash
python3 -B -m unittest discover -s tests -v
```

已完成 Skill 格式校验和 20 项本地检查器测试，覆盖引用关系、未读来源、选题状态、镜头对应、异常输入与时长估算。验证不代表选题效果、完整在线工作流或所有宿主兼容性已经通过实测。STEPX/StepClaw 安装及 AmooStore 上架仍需在目标平台验证。

## 文件

| 文件 | 用途 |
|---|---|
| [SKILL.md](SKILL.md) | 主入口与任务路由 |
| [sources.md](references/sources.md) | AI 选题发现的默认信息源 |
| [research.md](references/research.md) | 研究深度、证据与选题判断 |
| [writing.md](references/writing.md) | 口播、镜头和表达原则 |
| [outputs.md](references/outputs.md) | 按请求选择交付格式 |
| [record-format.md](references/record-format.md) | 可选结构化记录约定 |
| [check_work.py](scripts/check_work.py) | 引用关系检查与口播估时 |
| [openai.yaml](agents/openai.yaml) | Codex 展示信息 |

## 方法来源与许可

结合 [ai-topic-scout](https://github.com/Jingyi-Wu-Richael/ai-topic-scout) 的多源发现与证据核验，以及作者提供的 x-collect 材料中的逐层研究方法，重新编写为连续的创作者备稿流程。附件原文不包含在本仓库。

改编范围和来源说明见 [ORIGINS.md](ORIGINS.md)，许可见 [LICENSE](LICENSE)。
